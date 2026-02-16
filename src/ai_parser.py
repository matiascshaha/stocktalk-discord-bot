import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from pytz import timezone

from config.settings import (
    AI_CONFIG,
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_API_KEY,
    TRADING_CONFIG,
    get_account_constraints,
    get_analyst_for_channel,
)
from src.models.parser_models import (
    CONTRACT_VERSION,
    ParsedMessage,
    ParsedSignal,
    ParsedVehicle,
    ParserMeta,
)
from src.providers.client_factory import build_provider_client
from src.providers.parser_dispatch import UnsupportedProviderError, request_provider_completion
from src.utils.logger import setup_logger
from src.utils.paths import resolve_prompt_path

logger = setup_logger("ai_parser")


IMMUTABLE_CONTRACT_INSTRUCTION = f"""
# IMMUTABLE RESPONSE CONTRACT (DO NOT DEVIATE)
Return ONLY valid JSON (no markdown) with this exact shape:
{{
  "contract_version": "{CONTRACT_VERSION}",
  "source": {{
    "author": "string|null",
    "channel_id": "string|null",
    "message_id": "string|null",
    "message_text": "string|null"
  }},
  "signals": [
    {{
      "ticker": "string",
      "action": "BUY|SELL|HOLD|NONE",
      "confidence": 0.0,
      "reasoning": "string",
      "weight_percent": null,
      "urgency": "LOW|MEDIUM|HIGH",
      "sentiment": "BULLISH|BEARISH|NEUTRAL",
      "is_actionable": false,
      "vehicles": [
        {{
          "type": "STOCK|OPTION",
          "enabled": true,
          "intent": "EXECUTE|WATCH|INFO",
          "side": "BUY|SELL|NONE",
          "option_type": "CALL|PUT|null",
          "strike": null,
          "expiry": null,
          "quantity_hint": null
        }}
      ]
    }}
  ],
  "meta": {{
    "status": "ok|no_action|invalid_json|provider_error",
    "provider": "openai|anthropic|google|null",
    "error": null,
    "warnings": []
  }}
}}
Rules:
- ALWAYS include top-level keys: contract_version, source, signals, meta.
- If no actionable output, return an empty signals array.
- Portfolio recaps/watchlists/holdings summaries are NOT actionable; return an empty signals array unless the message includes a new execution command in this message.
- Never add or rename top-level keys.
""".strip()


class AIParser:
    """AI-powered parser that normalizes output to a strict, predictable contract."""

    def __init__(self):
        self.client = None
        self.provider = None
        self.config = AI_CONFIG
        self.options_enabled = bool(TRADING_CONFIG.get("options_enabled", False))
        self.prompt_template = self._load_prompt_template()

        self._init_client()

        if not self.client:
            logger.warning("No AI provider available")

    def parse(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        trading_account: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse a message into the canonical parser contract."""

        source = {
            "author": str(author_name) if author_name is not None else None,
            "channel_id": str(channel_id) if channel_id is not None else None,
            "message_id": None,
            "message_text": str(message_text) if message_text is not None else None,
        }

        if not self.client:
            logger.warning("No AI client available")
            return self._empty_result(status="no_client", source=source)

        prompt = self._build_prompt(
            message_text=message_text,
            author_name=author_name,
            channel_id=channel_id,
            trading_account=trading_account,
        )

        if not prompt.strip():
            logger.warning("Prompt template is empty")
            return self._empty_result(status="empty_prompt", source=source)

        response_text = ""
        try:
            response_text = request_provider_completion(
                provider=self.provider,
                client=self.client,
                config=self.config,
                prompt=prompt,
            )
            cleaned = self._clean_json(response_text)
            payload = json.loads(cleaned)
            return self._coerce_result(payload, source=source)
        except UnsupportedProviderError:
            logger.error("AI provider is not set on initialized client")
            return self._empty_result(status="unknown_provider", source=source)
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return self._empty_result(status="invalid_json", error=response_text, source=source)
        except Exception as exc:
            logger.error("AI parsing error: %s", exc)
            return self._empty_result(status="provider_error", error=str(exc), source=source)

    def _empty_result(self, status: str, source: Dict[str, Any], error: Optional[str] = None) -> Dict[str, Any]:
        return ParsedMessage(
            contract_version=CONTRACT_VERSION,
            source=source,
            signals=[],
            meta=ParserMeta(status=status, provider=self.provider, error=error),
        ).model_dump()

    def _coerce_result(self, payload: Any, source: Dict[str, Any]) -> Dict[str, Any]:
        signal_payloads: List[Dict[str, Any]] = []

        if isinstance(payload, dict):
            if isinstance(payload.get("signals"), list):
                signal_payloads = [s for s in payload.get("signals", []) if isinstance(s, dict)]
            elif "ticker" in payload:
                signal_payloads = [payload]
        elif isinstance(payload, list):
            signal_payloads = [s for s in payload if isinstance(s, dict)]

        normalized_signals: List[Dict[str, Any]] = []
        for signal in signal_payloads:
            normalized = self._normalize_signal(signal)
            if normalized:
                normalized_signals.append(normalized.model_dump())

        status = "ok" if normalized_signals else "no_action"
        result = ParsedMessage(
            contract_version=CONTRACT_VERSION,
            source=source,
            signals=normalized_signals,
            meta=ParserMeta(status=status, provider=self.provider, error=None),
        )
        return result.model_dump()

    def _normalize_signal(self, signal: Dict[str, Any]) -> Optional[ParsedSignal]:
        if not isinstance(signal, dict):
            return None

        action = str(signal.get("action") or "NONE").upper().strip()
        raw_vehicles = signal.get("vehicles")
        vehicles = self._normalize_vehicles(raw_vehicles, action)

        payload = dict(signal)
        payload["vehicles"] = [v.model_dump() for v in vehicles]

        if "is_actionable" not in payload:
            payload["is_actionable"] = action in {"BUY", "SELL", "HOLD"}

        try:
            return ParsedSignal.model_validate(payload)
        except ValidationError:
            return None

    def _normalize_vehicles(self, raw_vehicles: Any, action: str) -> List[ParsedVehicle]:
        if not isinstance(raw_vehicles, list) or not raw_vehicles:
            return [self._default_stock_vehicle(action)]

        normalized: List[ParsedVehicle] = []
        for vehicle in raw_vehicles:
            if not isinstance(vehicle, dict):
                continue

            vehicle_payload = dict(vehicle)
            vtype = str(vehicle_payload.get("type") or "STOCK").upper().strip()

            if "side" not in vehicle_payload:
                if vtype == "STOCK" and action in {"BUY", "SELL"}:
                    vehicle_payload["side"] = action
                else:
                    vehicle_payload["side"] = "NONE"

            if "intent" not in vehicle_payload:
                if vtype == "STOCK" and action in {"BUY", "SELL"}:
                    vehicle_payload["intent"] = "EXECUTE"
                else:
                    vehicle_payload["intent"] = "INFO"

            if "enabled" not in vehicle_payload:
                vehicle_payload["enabled"] = True

            if vtype == "OPTION" and not self.options_enabled:
                vehicle_payload["enabled"] = False

            try:
                normalized.append(ParsedVehicle.model_validate(vehicle_payload))
            except ValidationError:
                continue

        if not normalized:
            return [self._default_stock_vehicle(action)]

        return normalized

    def _default_stock_vehicle(self, action: str) -> ParsedVehicle:
        if action in {"BUY", "SELL"}:
            return ParsedVehicle(
                type="STOCK",
                enabled=True,
                intent="EXECUTE",
                side=action,
            )
        return ParsedVehicle(type="STOCK", enabled=True, intent="INFO", side="NONE")

    def _build_prompt(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        trading_account: Optional[Any] = None,
    ) -> str:
        if trading_account is not None:
            return self._render_prompt_with_account(
                message_text=message_text,
                author_name=author_name,
                channel_id=channel_id,
                trading_account=trading_account,
            )
        return self._render_prompt(message_text, author_name, channel_id=channel_id)

    def _clear_remaining_placeholders(self, prompt: str) -> str:
        return re.sub(r"\{\{[A-Z_]+\}\}", "", prompt)

    def _append_contract_instruction(self, prompt: str) -> str:
        return f"{prompt.rstrip()}\n\n{IMMUTABLE_CONTRACT_INSTRUCTION}\n"

    def _render_prompt(self, message_text: str, author_name: str, channel_id: Optional[int] = None) -> str:
        prompt = self.prompt_template or ""
        eastern = timezone("US/Eastern")
        current_time = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S %Z")
        analyst_rules = get_analyst_for_channel(channel_id) if channel_id else None
        analyst_name = analyst_rules.get("name", "Unknown") if analyst_rules else "Unknown"
        analyst_prefs = analyst_rules.get("analyst_preferences", "") if analyst_rules else ""
        account_constraints = get_account_constraints()
        trading_notice = "Return signals only. Runtime policy controls execution."

        prompt = prompt.replace("{{CURRENT_TIME}}", current_time)
        prompt = prompt.replace("{{AUTHOR_NAME}}", str(author_name))
        prompt = prompt.replace("{{MESSAGE_TEXT}}", str(message_text))
        prompt = prompt.replace("{{ACCOUNT_BALANCE}}", "N/A")
        prompt = prompt.replace("{{DAY_BUYING_POWER}}", "N/A")
        prompt = prompt.replace("{{OVERNIGHT_BUYING_POWER}}", "N/A")
        prompt = prompt.replace("{{OPTION_BUYING_POWER}}", "N/A")
        prompt = prompt.replace("{{MARGIN_BUFFER}}", "N/A")
        prompt = prompt.replace("{{MARGIN_POWER}}", "N/A")
        prompt = prompt.replace("{{CASH_POWER}}", "N/A")
        prompt = prompt.replace("{{MARGIN_EQUITY_PERCENTAGE}}", "N/A")
        prompt = prompt.replace("{{ANALYST_NAME}}", analyst_name)
        prompt = prompt.replace("{{ANALYST_PREFERENCES}}", analyst_prefs)
        prompt = prompt.replace("{{OPTIONS_CHAIN}}", "N/A")
        prompt = prompt.replace("{{ACCOUNT_CONSTRAINTS}}", account_constraints)
        prompt = prompt.replace("{{EXTRA_IMPORTANT_DETAILS}}", trading_notice)
        prompt = self._clear_remaining_placeholders(prompt)
        return self._append_contract_instruction(prompt)

    def _require(self, d: dict, key: str):
        if key not in d:
            raise KeyError(f"Missing required key from Webull payload: {key}")
        return d[key]

    def _require_currency_asset(self, account_balance: dict) -> dict:
        assets = self._require(account_balance, "account_currency_assets")
        if not isinstance(assets, list) or not assets:
            raise ValueError("account_currency_assets missing or empty")
        return assets[0]

    def _render_prompt_with_account(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        trading_account: Optional[Any] = None,
    ) -> str:
        template = self.prompt_template or ""

        analyst_rules = get_analyst_for_channel(channel_id) if channel_id else None
        analyst_name = analyst_rules.get("name", "Unknown") if analyst_rules else "Unknown"
        analyst_prefs = analyst_rules.get("analyst_preferences", "") if analyst_rules else ""

        account_balance = trading_account.get_account_balance() if trading_account else None
        if not account_balance:
            logger.warning("No account balance data available for prompt; using simple prompt instead")
            return self._render_prompt(message_text, author_name, channel_id=channel_id)

        total_market_value = float(self._require(account_balance, "total_market_value"))
        currency = self._require_currency_asset(account_balance)
        net_liquidation_value = float(self._require(currency, "net_liquidation_value"))
        margin_equity_percentage = (net_liquidation_value / total_market_value * 100.0) if total_market_value > 0 else 100.0
        margin_power = float(self._require(currency, "margin_power"))
        cash_power = float(self._require(currency, "cash_power"))

        account_constraints = get_account_constraints()

        prompt = template
        eastern = timezone("US/Eastern")
        current_time = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S %Z")
        prompt = prompt.replace("{{CURRENT_TIME}}", current_time)
        prompt = prompt.replace("{{AUTHOR_NAME}}", str(author_name))
        prompt = prompt.replace("{{MESSAGE_TEXT}}", str(message_text))
        prompt = prompt.replace("{{ACCOUNT_BALANCE}}", f"{net_liquidation_value:,.2f}")
        prompt = prompt.replace("{{MARGIN_POWER}}", f"{margin_power:,.2f}")
        prompt = prompt.replace("{{CASH_POWER}}", f"{cash_power:,.2f}")
        prompt = prompt.replace("{{MARGIN_EQUITY_PERCENTAGE}}", f"{margin_equity_percentage:,.2f}")
        prompt = prompt.replace("{{ANALYST_NAME}}", analyst_name)
        prompt = prompt.replace("{{ANALYST_PREFERENCES}}", analyst_prefs)
        prompt = prompt.replace("{{OPTIONS_CHAIN}}", "")
        prompt = prompt.replace("{{ACCOUNT_CONSTRAINTS}}", account_constraints)
        prompt = self._clear_remaining_placeholders(prompt)
        return self._append_contract_instruction(prompt)

    def _load_prompt_template(self) -> str:
        path = self.config.get("prompt_file") if isinstance(self.config, dict) else None
        prompt_path = resolve_prompt_path(path)
        logger.info("Loading prompt template from: %s", prompt_path)

        try:
            return prompt_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to load prompt template from %s: %s", prompt_path, exc)
            return ""

    def _init_client(self):
        provider = (AI_PROVIDER or "").lower().strip()
        fallback = bool(self.config.get("fallback_to_available_provider"))

        if provider in ("", "auto"):
            provider = None

        if provider:
            self._try_init_provider(provider)
            if not self.client and fallback:
                self._init_first_available()
        else:
            self._init_first_available()

    def _init_first_available(self):
        for name in ("anthropic", "openai", "google"):
            if self._provider_key_available(name):
                self._try_init_provider(name)
                if self.client:
                    return

    def _provider_key_available(self, provider: str) -> bool:
        if provider == "anthropic":
            return bool(ANTHROPIC_API_KEY)
        if provider == "openai":
            return bool(OPENAI_API_KEY)
        if provider == "google":
            return bool(GOOGLE_API_KEY)
        return False

    def _try_init_provider(self, provider: str):
        try:
            client = build_provider_client(
                provider=provider,
                config=self.config,
                anthropic_api_key=ANTHROPIC_API_KEY,
                openai_api_key=OPENAI_API_KEY,
                google_api_key=GOOGLE_API_KEY,
            )
            if client is None:
                return

            self.client = client
            self.provider = provider

            if provider == "anthropic":
                logger.info("Using Anthropic for AI parsing")
            elif provider == "openai":
                logger.info("Using OpenAI for AI parsing")
            elif provider == "google":
                logger.info("Using Google Gemini for AI parsing")
        except Exception as exc:
            logger.warning("%s initialization failed: %s", provider.title(), exc)

    def _clean_json(self, text: str) -> str:
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\\n", "", text)
            text = re.sub(r"\\n```$", "", text)
        return text.strip()
