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
from src.providers.openai.parser_client import request_fast_parser_completion
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

        response_text = ""
        try:
            fast_path_result = self._try_openai_fast_path(
                message_text=message_text,
                source=source,
            )
            if fast_path_result is not None:
                return fast_path_result

            prompt = self._build_prompt(
                message_text=message_text,
                author_name=author_name,
                channel_id=channel_id,
                trading_account=trading_account,
            )

            if not prompt.strip():
                logger.warning("Prompt template is empty")
                return self._empty_result(status="empty_prompt", source=source)

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
        warnings: List[str] = []

        if isinstance(payload, dict):
            if isinstance(payload.get("signals"), list):
                signal_payloads = [s for s in payload.get("signals", []) if isinstance(s, dict)]
            elif "ticker" in payload:
                signal_payloads = [payload]
            elif "picks" in payload:
                warning = "Provider returned unsupported 'picks' format; expected top-level 'signals'."
                warnings.append(warning)
                logger.warning(warning)
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
            meta=ParserMeta(status=status, provider=self.provider, error=None, warnings=warnings),
        )
        return result.model_dump()

    def _try_openai_fast_path(self, message_text: str, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if (self.provider or "").lower().strip() != "openai":
            return None

        openai_config = self.config.get("openai", {}) if isinstance(self.config, dict) else {}
        if not bool(openai_config.get("fast_path_enabled", False)):
            return None

        max_tokens = int(openai_config.get("fast_max_tokens", 250) or 250)
        confidence_threshold = float(openai_config.get("fast_confidence_threshold", 0.85) or 0.85)
        prompt = self._build_fast_prompt(message_text)

        try:
            response_text = request_fast_parser_completion(
                client=self.client,
                model=openai_config["model"],
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.0,
            )
            fast_payload = json.loads(self._clean_json(response_text))
        except Exception as exc:
            logger.warning("OpenAI fast-path failed; falling back to full parse: %s", exc)
            return None

        if not isinstance(fast_payload, dict):
            return None

        status = str(fast_payload.get("status") or "ambiguous").lower().strip()
        confidence = self._normalize_fast_confidence(fast_payload.get("confidence"))

        if status == "no_action" and confidence >= confidence_threshold:
            return self._empty_result(status="no_action", source=source)

        if status != "actionable" or confidence < confidence_threshold:
            return None

        ticker = self._normalize_ticker_candidate(fast_payload.get("primary_ticker"))
        if not ticker:
            return None

        action = self._normalize_fast_action(fast_payload.get("action"))
        if action == "NONE":
            return None

        vehicles = self._build_vehicles_from_fast_hint(
            message_text=message_text,
            vehicle_hint=fast_payload.get("vehicle_hint"),
            action=action,
        )

        signal = {
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "reasoning": str(fast_payload.get("evidence_text") or ""),
            "weight_percent": self._extract_weight_percent(message_text),
            "urgency": "MEDIUM",
            "sentiment": "NEUTRAL",
            "is_actionable": True,
            "vehicles": vehicles,
        }
        return self._coerce_result({"signals": [signal]}, source=source)

    def _build_fast_prompt(self, message_text: str) -> str:
        return (
            "Classify this Discord analyst message for trading intent. "
            "Return only JSON. "
            "If no new trade recommendation exists in this message, set status to no_action. "
            "If unclear, set status to ambiguous. "
            "primary_ticker must be symbol only (no $). "
            "vehicle_hint: stock|option|mixed|unknown. "
            "action: BUY|SELL|NONE. "
            "evidence_text should be a short direct quote from the message. "
            "sizing_text should copy any explicit size/weight phrase or 'unspecified'.\n\n"
            f"Message:\n{message_text}"
        )

    def _normalize_fast_confidence(self, value: Any) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, parsed))

    def _normalize_fast_action(self, value: Any) -> str:
        action = str(value or "NONE").upper().strip()
        if action in {"BUY", "SELL", "NONE"}:
            return action
        return "NONE"

    def _normalize_ticker_candidate(self, value: Any) -> Optional[str]:
        if value in (None, "", "null"):
            return None
        text = str(value).upper().replace("$", "").strip()
        if not text:
            return None
        if "-" in text:
            compact = text.replace("-", "")
            if compact.isalnum():
                text = compact
        return text

    def _extract_weight_percent(self, message_text: str) -> Optional[float]:
        match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*%\s*(?:weight|weighting)?", message_text, re.IGNORECASE)
        if not match:
            return None
        try:
            return float(match.group(1))
        except (TypeError, ValueError):
            return None

    def _build_vehicles_from_fast_hint(self, message_text: str, vehicle_hint: Any, action: str) -> List[Dict[str, Any]]:
        hint = str(vehicle_hint or "unknown").lower().strip()
        option_details = self._extract_option_details(message_text)

        if hint == "option":
            return [self._option_vehicle(action, option_details)]

        if hint == "mixed":
            return [
                self._stock_vehicle(action),
                self._option_vehicle(action, option_details),
            ]

        return [self._stock_vehicle(action)]

    def _stock_vehicle(self, action: str) -> Dict[str, Any]:
        return {
            "type": "STOCK",
            "enabled": True,
            "intent": "EXECUTE" if action in {"BUY", "SELL"} else "INFO",
            "side": action if action in {"BUY", "SELL"} else "NONE",
            "option_type": None,
            "strike": None,
            "expiry": None,
            "quantity_hint": None,
        }

    def _option_vehicle(self, action: str, option_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "OPTION",
            "enabled": True,
            "intent": "EXECUTE" if action in {"BUY", "SELL"} else "INFO",
            "side": action if action in {"BUY", "SELL"} else "NONE",
            "option_type": option_details.get("option_type"),
            "strike": option_details.get("strike"),
            "expiry": option_details.get("expiry"),
            "quantity_hint": None,
        }

    def _extract_option_details(self, message_text: str) -> Dict[str, Any]:
        details: Dict[str, Any] = {
            "option_type": None,
            "strike": None,
            "expiry": None,
        }

        contract_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*([CP])\b", message_text, re.IGNORECASE)
        if contract_match:
            details["strike"] = float(contract_match.group(1))
            details["option_type"] = "CALL" if contract_match.group(2).upper() == "C" else "PUT"

        if details["option_type"] is None:
            if re.search(r"\bcalls?\b", message_text, re.IGNORECASE):
                details["option_type"] = "CALL"
            elif re.search(r"\bputs?\b", message_text, re.IGNORECASE):
                details["option_type"] = "PUT"

        expiry_patterns = [
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+'?\d{2,4}\b",
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}\b",
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\bfor\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b",
        ]
        for pattern in expiry_patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match:
                details["expiry"] = match.group(0).replace("for ", "").strip()
                break

        return details

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

        if provider == "none":
            logger.info("AI provider disabled via config (ai.provider=none)")
            return

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
