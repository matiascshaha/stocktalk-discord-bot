import json
import re
from typing import Any, Dict, Optional
from datetime import datetime
from pytz import timezone

import anthropic
import openai
from pydantic import ValidationError

from config.settings import (
    AI_CONFIG,
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_API_KEY,
    get_account_constraints,
    get_analyst_for_channel,
)
from src.models.parser_models import ParsedMessage, ParsedPick, ParserMeta
from src.utils.logger import setup_logger
from src.utils.paths import resolve_prompt_path

logger = setup_logger('ai_parser')

class AIParser:
    """
    AI-powered stock pick parser using Claude or GPT
    
    Primary: Claude Sonnet 4.5
    Fallback: GPT-4
    """
    
    def __init__(self):
        self.client = None
        self.provider = None
        self.config = AI_CONFIG
        self.prompt_template = self._load_prompt_template()

        self._init_client()
        
        if not self.client:
            logger.warning("No AI provider available - using fallback regex parser only")
    
    def parse(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        trading_account: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Parse stock picks from message using AI with optional account context.
        
        Args:
            message_text: The Discord message content
            author_name: The author's Discord username
            channel_id: Optional Discord channel ID for analyst-specific rules
            trading_account: Optional trading account object for context

        Returns:
            Dict with a stable shape:
            {
              "picks": [...],
              "meta": {"status": "...", "provider": "...", "error": "..."}
            }
        """
        
        if not self.client:
            logger.warning("No AI client available")
            logger.warning("Skipping because no AI provider is configured")
            return self._empty_result(status="no_client")
        
        prompt = self._build_prompt(
            message_text=message_text,
            author_name=author_name,
            channel_id=channel_id,
            trading_account=trading_account
        )
        
        if not prompt.strip():
            logger.warning("Prompt template is empty; Doing nothing.")
            return self._empty_result(status="empty_prompt")
        
        try:
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.config['anthropic']['model'],
                    max_tokens=self.config['anthropic']['max_tokens'],
                    temperature=self.config['anthropic']['temperature'],
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text.strip()
            
            elif self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.config['openai']['model'],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config['openai']['max_tokens'],
                    temperature=self.config['openai']['temperature'],
                )
                response_text = response.choices[0].message.content.strip()

            elif self.provider == 'google':
                response = self.client.generate_content(prompt)
                response_text = response.text.strip()
            else:
                logger.error("AI provider is not set on initialized client")
                return self._empty_result(status="unknown_provider")
            
            logger.debug(f"AI response: {response_text}")
            
            response_text = self._clean_json(response_text)
            
            try:
                result = json.loads(response_text)
                return self._coerce_result(result)
            except json.JSONDecodeError:
                logger.warning("AI response was not in expected format. Probably an issue with context.")
                logger.error(f"Failed to parse AI response as JSON: {response_text}")
                return self._empty_result(status="invalid_json", error=response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Raw response: {response_text}")
            return self._empty_result(status="json_error", error=str(e))
        
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return self._empty_result(status="provider_error", error=str(e))

    def _empty_result(self, status: str, error: Optional[str] = None) -> Dict[str, Any]:
        return ParsedMessage(
            picks=[],
            meta=ParserMeta(status=status, provider=self.provider, error=error),
        ).model_dump()

    def _coerce_result(self, payload: Any) -> Dict[str, Any]:
        picks: list = []
        extras: Dict[str, Any] = {}

        if isinstance(payload, dict):
            if isinstance(payload.get("picks"), list):
                picks = payload.get("picks", [])
                extras = {k: v for k, v in payload.items() if k not in {"picks", "meta"}}
            elif "ticker" in payload:
                picks = [payload]
            else:
                picks = []
        elif isinstance(payload, list):
            picks = payload

        normalized_picks = []
        for pick in picks:
            normalized = self._normalize_pick(pick)
            if normalized:
                normalized_picks.append(normalized.model_dump())

        result = ParsedMessage(
            picks=normalized_picks,
            meta=ParserMeta(status="ok", provider=self.provider, error=None),
            **extras,
        )
        return result.model_dump()

    def _normalize_pick(self, pick: Any) -> Optional[ParsedPick]:
        if not isinstance(pick, dict):
            return None
        try:
            return ParsedPick.model_validate(pick)
        except ValidationError:
            return None
    
    def _build_prompt(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        trading_account: Optional[Any] = None,
    ) -> str:
        """Build AI prompt for parsing, optionally with account context."""
        
        if trading_account is not None:
            # Use unified prompt with account context
            return self._render_prompt_with_account(
                message_text=message_text,
                author_name=author_name,
                channel_id=channel_id,
                trading_account=trading_account
            )
        else:
            # Use simple prompt
            return self._render_prompt(message_text, author_name, channel_id=channel_id)

    def _clear_remaining_placeholders(self, prompt: str) -> str:
        """Remove any unreplaced placeholders from the prompt."""
        return re.sub(r"\{\{[A-Z_]+\}\}", "", prompt)

    def _render_prompt(self, message_text, author_name, channel_id=None) -> str:
        prompt = self.prompt_template or ""
        eastern = timezone('US/Eastern')
        current_time = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S %Z")
        analyst_rules = get_analyst_for_channel(channel_id) if channel_id else None
        analyst_name = analyst_rules.get("name", "Unknown") if analyst_rules else "Unknown"
        analyst_prefs = analyst_rules.get("analyst_preferences", "") if analyst_rules else ""
        account_constraints = get_account_constraints()
        TRADING_DEACTIVATED_NOTICE = (
            "Note: Auto-trading is currently deactivated. "
            "Provide stock picks without considering trading actions."
        )
        prompt = prompt.replace("{{CURRENT_TIME}}", current_time)
        prompt = prompt.replace("{{AUTHOR_NAME}}", str(author_name))
        prompt = prompt.replace("{{MESSAGE_TEXT}}", str(message_text))
        prompt = prompt.replace("{{ACCOUNT_BALANCE}}", f"N/A")
        prompt = prompt.replace("{{DAY_BUYING_POWER}}", f"N/A")
        prompt = prompt.replace("{{OVERNIGHT_BUYING_POWER}}", f"N/A")
        prompt = prompt.replace("{{OPTION_BUYING_POWER}}", f"N/A")
        prompt = prompt.replace("{{MARGIN_BUFFER}}", f"N/A")
        prompt = prompt.replace("{{ANALYST_NAME}}", analyst_name)
        prompt = prompt.replace("{{ANALYST_PREFERENCES}}", analyst_prefs)
        prompt = prompt.replace("{{OPTIONS_CHAIN}}", "N/A")
        prompt = prompt.replace("{{ACCOUNT_CONSTRAINTS}}", account_constraints)
        prompt = prompt.replace("{{EXTRA_IMPORTANT_DETAILS}}", TRADING_DEACTIVATED_NOTICE)
        prompt = self._clear_remaining_placeholders(prompt)
        return prompt

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
            return self._render_prompt(message_text, author_name)

        # ---- REQUIRED Webull fields ----
        total_market_value = float(self._require(account_balance, "total_market_value"))

        currency = self._require_currency_asset(account_balance)
        net_liquidation_value = float(self._require(currency, "net_liquidation_value"))
        margin_equity_percentage = (net_liquidation_value / total_market_value * 100.0) if total_market_value > 0 else 100.0
        margin_power = float(self._require(currency, "margin_power"))
        cash_power = float(self._require(currency, "cash_power"))

        account_constraints = get_account_constraints()

        prompt = template
        eastern = timezone('US/Eastern')
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

        return prompt

    def _format_account_balance(self, balance_data: Optional[Dict[str, Any]]) -> str:
        """Format account balance dict into readable string for AI prompt."""
        if not balance_data:
            return "No account data available"

        # Handle various Webull response formats
        try:
            # Extract common fields
            total_value = balance_data.get("total_asset_value") or balance_data.get("total")
            cash = balance_data.get("cash") or balance_data.get("available_cash")
            buying_power = balance_data.get("buying_power") or balance_data.get("available_margin")

            parts = []
            if total_value:
                parts.append(f"Total Value: ${total_value}")
            if cash:
                parts.append(f"Cash: ${cash}")
            if buying_power:
                parts.append(f"Buying Power: ${buying_power}")

            return " | ".join(parts) if parts else "No account balance data"
        except Exception as exc:
            logger.warning(f"Failed to format account balance: {exc}")
            return "No account data available"

    def _format_account_positions(self, positions_data: Optional[Dict[str, Any]]) -> str:
        """Format account positions dict into readable string for AI prompt."""
        if not positions_data:
            return "No open positions"

        try:
            # Handle various response formats
            positions_list = []
            if isinstance(positions_data, dict):
                positions_list = positions_data.get("positions") or positions_data.get("data") or []
            elif isinstance(positions_data, list):
                positions_list = positions_data

            if not positions_list:
                return "No open positions"

            # Format each position
            formatted = []
            for pos in positions_list[:5]:  # Limit to 5 for brevity
                ticker = pos.get("symbol") or pos.get("ticker")
                qty = pos.get("quantity") or pos.get("qty")
                avg_cost = pos.get("avg_cost") or pos.get("average_price")
                current_price = pos.get("current_price") or pos.get("price")

                if ticker:
                    formatted.append(f"{ticker}: {qty} shares @ ${avg_cost}")

            return " | ".join(formatted) if formatted else "No open positions"

        except Exception as exc:
            logger.warning(f"Failed to format account positions: {exc}")
            return "No position data available"

    def _extract_margin_stats(self, balance_data: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Extract margin-related stats from account balance."""
        if not balance_data:
            return {
                "available": "unknown",
                "buffer": "unknown",
                "position_count": "unknown",
            }

        try:
            available_margin = balance_data.get("available_margin") or balance_data.get("buying_power") or "unknown"
            
            # Calculate margin buffer (simplified: assume maintenance requirement is 30% of positions)
            # In real scenario, you'd calculate this from actual position values
            total_value = balance_data.get("total_asset_value") or balance_data.get("total") or 0
            margin_maintenance = float(total_value) * 0.30 if total_value else 0
            cash = balance_data.get("cash") or balance_data.get("available_cash") or 0
            margin_buffer = float(cash) - margin_maintenance if cash else 0

            return {
                "available": str(available_margin),
                "buffer": f"${margin_buffer:.2f}" if margin_buffer > 0 else "unknown",
                "position_count": "unknown",  # Would need positions data
            }
        except Exception as exc:
            logger.warning(f"Failed to extract margin stats: {exc}")
            return {
                "available": "unknown",
                "buffer": "unknown",
                "position_count": "unknown",
            }

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
            if provider == "anthropic" and ANTHROPIC_API_KEY:
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = "anthropic"
                logger.info("Using Anthropic Claude for AI parsing")
            elif provider == "openai" and OPENAI_API_KEY:
                self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
                self.provider = "openai"
                logger.info("Using OpenAI GPT for AI parsing")
            elif provider == "google" and GOOGLE_API_KEY:
                import google.generativeai as genai

                genai.configure(api_key=GOOGLE_API_KEY)
                model_name = self.config["google"]["model"]
                self.client = genai.GenerativeModel(model_name)
                self.provider = "google"
                logger.info("Using Google Gemini for AI parsing")
        except Exception as e:
            logger.warning(f"{provider.title()} initialization failed: {e}")
    
    def _clean_json(self, text):
        """Clean JSON response from AI"""
        # Remove markdown code blocks
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\n', '', text)
            text = re.sub(r'\n```$', '', text)
        return text.strip()
