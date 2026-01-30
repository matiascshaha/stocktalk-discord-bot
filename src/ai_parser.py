import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

import anthropic
import openai

from config.settings import (
    AI_CONFIG,
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_API_KEY,
    get_account_constraints,
    get_analyst_for_channel,
)
from src.utils.logger import setup_logger

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
        account_balance: Optional[Dict[str, Any]] = None,
        account_positions: Optional[Dict[str, Any]] = None,
    ) -> list:
        """
        Parse stock picks from message using AI with optional account context.
        
        Args:
            message_text: The Discord message content
            author_name: The author's Discord username
            channel_id: Optional Discord channel ID for analyst-specific rules
            account_balance: Optional account balance dict from Webull API
            account_positions: Optional account positions dict from Webull API
        
        Returns:
            List of picks (with new unified format if account context provided)
        """
        
        if not self.client:
            logger.warning("No AI client available")
            return self._fallback_parse(message_text)
        
        # Determine which prompt template to use
        use_account_context = (account_balance is not None or account_positions is not None)
        
        prompt = self._build_prompt(
            message_text=message_text,
            author_name=author_name,
            channel_id=channel_id,
            account_balance=account_balance,
            account_positions=account_positions,
            use_account_context=use_account_context,
        )
        
        if not prompt.strip():
            logger.warning("Prompt template is empty; falling back to regex parser")
            return self._fallback_parse(message_text)
        
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
            
            logger.debug(f"AI response: {response_text}")
            
            # Clean and parse JSON
            response_text = self._clean_json(response_text)
            
            # Try parsing as dict first (new unified format)
            try:
                result = json.loads(response_text)
                if isinstance(result, dict) and "picks" in result:
                    # New unified format with summary
                    logger.info(f"Parsed {len(result.get('picks', []))} picks with account context")
                    return result
                else:
                    # Fallback: treat as list
                    return result if isinstance(result, list) else [result]
            except json.JSONDecodeError:
                # Try parsing as list (legacy format)
                return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Raw response: {response_text}")
            return self._fallback_parse(message_text)
        
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return self._fallback_parse(message_text)
    
    def _build_prompt(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        account_balance: Optional[Dict[str, Any]] = None,
        account_positions: Optional[Dict[str, Any]] = None,
        use_account_context: bool = False,
    ) -> str:
        """Build AI prompt for parsing, optionally with account context."""
        
        if use_account_context:
            # Use unified prompt with account context
            return self._render_prompt_with_account(
                message_text=message_text,
                author_name=author_name,
                channel_id=channel_id,
                account_balance=account_balance,
                account_positions=account_positions,
            )
        else:
            # Use simple prompt
            return self._render_prompt(message_text, author_name)

    def _render_prompt(self, message_text, author_name):
        template = self.prompt_template or ""
        prompt = template.replace("{{AUTHOR_NAME}}", str(author_name))
        prompt = prompt.replace("{{MESSAGE_TEXT}}", str(message_text))
        return prompt

    def _render_prompt_with_account(
        self,
        message_text: str,
        author_name: str,
        channel_id: Optional[int] = None,
        account_balance: Optional[Dict[str, Any]] = None,
        account_positions: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render the unified AI prompt with account context.
        Uses ai_parser_with_account.prompt template.
        """
        # Try to load the account-aware prompt template
        account_prompt_path = Path("config/ai_parser_with_account.prompt")
        try:
            template = account_prompt_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(f"Failed to load account-aware prompt template: {exc}")
            # Fallback to simple prompt
            return self._render_prompt(message_text, author_name)

        # Get analyst rules if channel_id provided
        analyst_rules = None
        if channel_id:
            analyst_rules = get_analyst_for_channel(channel_id)

        analyst_name = analyst_rules.get("name", "Unknown") if analyst_rules else "Unknown"
        commons_multiplier = analyst_rules.get("commons_multiplier", 1.0) if analyst_rules else 1.0
        options_multiplier = analyst_rules.get("options_multiplier", 1.0) if analyst_rules else 1.0
        analyst_options_prefs = analyst_rules.get("options_preferences", "") if analyst_rules else ""
        margin_buffer_required = analyst_rules.get("margin_buffer_required", 1000) if analyst_rules else 1000

        # Extract account stats (these should come from the Webull API response)
        account_balance_str = self._format_account_balance(account_balance)
        positions_str = self._format_account_positions(account_positions)
        margin_stats = self._extract_margin_stats(account_balance)

        # Get natural language constraints
        account_constraints = get_account_constraints()

        # Build the prompt by substituting all placeholders
        prompt = template
        prompt = prompt.replace("{{AUTHOR_NAME}}", str(author_name))
        prompt = prompt.replace("{{MESSAGE_TEXT}}", str(message_text))
        prompt = prompt.replace("{{ACCOUNT_BALANCE}}", account_balance_str)
        prompt = prompt.replace("{{AVAILABLE_MARGIN}}", margin_stats.get("available", "unknown"))
        prompt = prompt.replace("{{MARGIN_BUFFER}}", margin_stats.get("buffer", "unknown"))
        prompt = prompt.replace("{{POSITION_COUNT}}", margin_stats.get("position_count", "unknown"))
        prompt = prompt.replace("{{CURRENT_POSITIONS}}", positions_str)
        prompt = prompt.replace("{{ANALYST_NAME}}", analyst_name)
        prompt = prompt.replace("{{COMMONS_MULTIPLIER}}", str(commons_multiplier))
        prompt = prompt.replace("{{OPTIONS_MULTIPLIER}}", str(options_multiplier))
        prompt = prompt.replace("{{MARGIN_BUFFER_REQUIRED}}", str(margin_buffer_required))
        prompt = prompt.replace("{{ANALYST_OPTIONS_PREFERENCES}}", analyst_options_prefs)
        prompt = prompt.replace("{{ACCOUNT_CONSTRAINTS}}", account_constraints)

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
        path = path or "config/ai_parser.prompt"
        prompt_path = Path(path)

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
    
    def _fallback_parse(self, message_text):
        """Fallback regex parser if AI fails"""
        logger.warning("Using fallback regex parser")
        
        picks = []
        
        # Look for explicit buy patterns
        buy_patterns = [
            r'(?:Added|Buying|New position:?)\s+\$?([A-Z]{1,5})',
            r'\$([A-Z]{1,5})\s+at\s+\$?([\d.]+)',
        ]
        
        for pattern in buy_patterns:
            matches = re.finditer(pattern, message_text, re.IGNORECASE)
            for match in matches:
                ticker = match.group(1).upper()
                price = float(match.group(2)) if len(match.groups()) > 1 else None
                
                picks.append({
                    'ticker': ticker,
                    'action': 'BUY',
                    'confidence': 0.6,
                    'weight': None,
                    'price': price,
                    'strike': None,
                    'option_type': 'STOCK',
                    'expiry': None,
                    'reasoning': 'Fallback regex match',
                    'urgency': 'MEDIUM',
                    'sentiment': 'BULLISH'
                })
        
        return picks
