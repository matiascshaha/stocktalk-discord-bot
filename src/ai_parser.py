import json
import re
from pathlib import Path

import anthropic
import openai

from config.settings import (
    AI_CONFIG,
    AI_PROVIDER,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_API_KEY,
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
    
    def parse(self, message_text, author_name):
        """Parse stock picks from message using AI"""
        
        if not self.client:
            logger.warning("No AI client available")
            return self._fallback_parse(message_text)
        
        prompt = self._build_prompt(message_text, author_name)
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
            picks = json.loads(response_text)
            
            return picks
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Raw response: {response_text}")
            return self._fallback_parse(message_text)
        
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return self._fallback_parse(message_text)
    
    def _build_prompt(self, message_text, author_name):
        """Build AI prompt for parsing"""
        return self._render_prompt(message_text, author_name)

    def _render_prompt(self, message_text, author_name):
        template = self.prompt_template or ""
        prompt = template.replace("{{AUTHOR_NAME}}", str(author_name))
        prompt = prompt.replace("{{MESSAGE_TEXT}}", str(message_text))
        return prompt

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
