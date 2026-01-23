import anthropic
import openai
import json
import re
from config.settings import ANTHROPIC_API_KEY, OPENAI_API_KEY
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
        
        if ANTHROPIC_API_KEY:
            try:
                self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = 'anthropic'
                logger.info("Using Anthropic Claude for AI parsing")
            except Exception as e:
                logger.warning(f"Anthropic initialization failed: {e}")
        
        if not self.client and OPENAI_API_KEY:
            try:
                self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
                self.provider = 'openai'
                logger.info("Using OpenAI GPT for AI parsing")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")
        
        if not self.client:
            logger.warning("No AI provider available - using fallback regex parser only")
    
    def parse(self, message_text, author_name):
        """Parse stock picks from message using AI"""
        
        if not self.client:
            logger.warning("No AI client available")
            return self._fallback_parse(message_text)
        
        prompt = self._build_prompt(message_text, author_name)
        
        try:
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text.strip()
            
            elif self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content.strip()
            
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
        return f"""You are analyzing a message from a professional stock trading Discord channel.

Message from {author_name}:
"{message_text}"

TASK: Extract ALL actionable stock picks from this message.

IMPORTANT RULES:
1. Only extract picks where there is CLEAR ACTION: "Added", "Buying", "New position", "Trimming", "Exiting", "Selling"
2. IGNORE portfolio updates, commentary, market analysis, reminders, or general discussion
3. IGNORE mentions of stocks without clear action (e.g., "watching XYZ" or "interesting stock")
4. For options, extract strike price and expiration date
5. VERY IMPORTANT — OPTIONS INTENT RULE:

If the author expresses ANY interest, intention, plan, or consideration to buy calls or puts for a ticker,
you MUST extract this as an OPTIONS BUY pick, even if:

- no expiration date is given
- no price is given
- the language is vague or future tense
- the contract format is incomplete

Examples of intent language that MUST trigger an options BUY:
- "may try to work into"
- "looking to add"
- "will add"
- "may add"
- "work into some calls"
- "might build a position in calls"
- "considering calls"
- "want exposure via calls"
- "options are illiquid but I may try"
- "I may try to get into $85C"
- "across multiple strikes"

In these cases:
- strike = parsed number if present, else null
- expiry = null
- option_type = CALL or PUT

STOCK PICK PATTERNS TO RECOGNIZE:
- "Added $TICKER at $X.XX" = BUY
- "New position: $TICKER" = BUY  
- "Buying $TICKER" = BUY
- "$TICKER (Shares + $XC Month 'YY)" = BUY with options
- "Trimming $TICKER" = SELL (partial)
- "Exiting $TICKER" = SELL (full)
- "X% weight @ $Y.ZZ" = weight percentage

OPTIONS FORMAT EXAMPLES:
- "$115C Mar '26" = $115 strike CALL expiring March 2026
- "$12.5C" = $12.50 strike CALL
- "$30C Jun '26" = $30 strike CALL expiring June 2026

IGNORE THESE:
- Portfolio updates (lists of holdings)
- Market commentary without specific action
- General discussion or analysis
- Reminders or announcements
- Past performance discussions

Return a JSON array. For each pick include:
{{
  "ticker": "string (no $ symbol)",
  "action": "BUY or SELL",
  "confidence": 0.0-1.0 (how certain this is an actionable pick),
  "weight": number or null (allocation percentage if mentioned),
  "price": number or null (entry price if mentioned),
  "strike": number or null (options strike price),
  "option_type": "CALL" or "PUT" or "STOCK",
  "expiry": "string or null (e.g., '2026-03-31' for Mar '26)",
  "reasoning": "brief explanation",
  "urgency": "LOW", "MEDIUM", or "HIGH",
  "sentiment": "BULLISH" or "BEARISH"
}}

Return ONLY the JSON array, no other text. If no actionable picks found, return [].

EXAMPLES:

Message: "Added $GLDD at $13.95 and some $12.5C for March at $1.75 avg just to add some juice. 4.5% weighting."
Output: [
  {{
    "ticker": "GLDD",
    "action": "BUY",
    "confidence": 1.0,
    "weight": 4.5,
    "price": 13.95,
    "strike": null,
    "option_type": "STOCK",
    "expiry": null,
    "reasoning": "Explicitly added shares at $13.95 with 4.5% weight",
    "urgency": "HIGH",
    "sentiment": "BULLISH"
  }},
  {{
    "ticker": "GLDD",
    "action": "BUY",
    "confidence": 1.0,
    "weight": null,
    "price": 1.75,
    "strike": 12.5,
    "option_type": "CALL",
    "expiry": "2026-03-31",
    "reasoning": "Added $12.5 calls for March 2026",
    "urgency": "HIGH",
    "sentiment": "BULLISH"
  }}
]

Message: "New position: Pangea Logistics $PANL - 4% weight @ $7.23 avg on shares, also very small spot in $7.5C for May"
Output: [
  {{
    "ticker": "PANL",
    "action": "BUY",
    "confidence": 1.0,
    "weight": 4.0,
    "price": 7.23,
    "strike": null,
    "option_type": "STOCK",
    "expiry": null,
    "reasoning": "New position at $7.23 with 4% weight",
    "urgency": "HIGH",
    "sentiment": "BULLISH"
  }},
  {{
    "ticker": "PANL",
    "action": "BUY",
    "confidence": 0.9,
    "weight": null,
    "price": null,
    "strike": 7.5,
    "option_type": "CALL",
    "expiry": "2026-05-31",
    "reasoning": "Small position in $7.5 calls for May",
    "urgency": "MEDIUM",
    "sentiment": "BULLISH"
  }}
]

Message: "PORTFOLIO UPDATE - 15 POSITIONS... 20-21%: $ENS* (Shares + $115C Mar '26) - $116.63"
Output: []
Reason: This is a portfolio update, not a new actionable pick

Message: "I expect $MU to meaningfully outperform the market tomorrow."
Output: []
Reason: This is commentary/prediction, not an actionable buy/sell order"""
    
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