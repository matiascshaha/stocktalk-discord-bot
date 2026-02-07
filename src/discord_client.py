import discord
import json
from datetime import datetime
from pydantic import ValidationError
from src.ai_parser import AIParser
from src.models.parser_models import ParsedMessage, ParsedPick
from src.notifier import Notifier
from src.utils.logger import setup_logger
from src.utils.logging_format import format_startup_status, format_pick_summary
from src.utils.paths import PICKS_LOG_PATH
from src.webull_trader import WebullTrader
from src.models.webull_models import OrderSide, OrderType, StockOrderRequest, TimeInForce
from config.settings import DISCORD_TOKEN, CHANNEL_ID

logger = setup_logger('discord_client')

class StockMonitorClient:
    """Discord client for monitoring stock picks"""
    
    def __init__(self, trader : WebullTrader = None):
        self.trader = trader
        self.parser = AIParser()
        self.notifier = Notifier()

        self._patch_pending_payments()
        
        # Setup Discord client
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            self.client = discord.Client(intents=intents)
        except AttributeError:
            # discord.py-self may not have Intents
            self.client = discord.Client()
        
        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
    
    async def on_ready(self):
        """Called when Discord client is ready"""
        logger.info("="*60)
        logger.info("Discord stock monitor active.")
        logger.info("="*60)
        for line in format_startup_status(
            self.client.user,
            CHANNEL_ID,
            self.parser.provider,
            bool(self.trader),
        ):
            logger.info(line)
        logger.info("="*60)
        logger.info("Waiting for stock picks.")
    
    async def on_message(self, message):
        """Called when a message is received"""
        if message.channel.id != CHANNEL_ID:
            logger.debug("Ignoring message from channel %s", message.channel.id)
            return

        if self.client.user and message.author.id == self.client.user.id:
            logger.debug("Ignoring own message")
            return

        content = (message.content or "").strip()
        if len(content) < 3:
            logger.debug("Ignoring short message")
            return
        
        logger.info(f"New message from {message.author.name}")
        logger.debug(f"Message content: {message.content[:100]}...")
        
        logger.info("AI analyzing message.")
        parsed = self.parser.parse(message.content, message.author.name, message.channel.id, self.trader)
        if not isinstance(parsed, dict):
            logger.warning("Parser returned unexpected type: %s", type(parsed).__name__)
            return

        try:
            parsed_message = ParsedMessage.model_validate(parsed)
        except ValidationError as exc:
            logger.warning("Parser returned invalid payload: %s", exc)
            return

        pick_objs = parsed_message.picks
        parsed_payload = parsed_message.model_dump()

        if pick_objs:
            logger.info(f"Detected {len(pick_objs)} stock pick(s).")
            logger.debug("Picks details: %s", json.dumps(parsed_payload, indent=2))
            logger.info(format_pick_summary(parsed_payload))

            # Send notifications
            self.notifier.notify(parsed_payload, message.author.name)

            # Log picks
            self._log_picks(message, parsed_payload)

            # Execute trades if trader available
            if self.trader:
                for pick in pick_objs:
                    order = self._pick_to_stock_order(pick)
                    if not order:
                        continue
                    self.trader.place_stock_order(order, weighting=pick.weight_percent)
        else:
            logger.info("No stock picks detected.")

    def _pick_to_stock_order(self, pick: ParsedPick):
        if pick.action == "HOLD":
            logger.info("Skipping HOLD pick for %s", pick.ticker)
            return None

        side = OrderSide.SELL if pick.action == "SELL" else OrderSide.BUY
        return StockOrderRequest(
            symbol=pick.ticker,
            side=side,
            quantity=1,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC,
        )
    
    def _log_picks(self, message, picks):
        """Log picks to file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "author": str(message.author),
            "message": message.content,
            "message_url": message.jump_url,
            "ai_parsed_picks": picks,
        }

        PICKS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with PICKS_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.debug("Pick logged to %s", PICKS_LOG_PATH)
    
    async def read_channel_history(self, limit=10):
        """
        Read message history from the monitored channel.
        
        Args:
            limit: Number of messages to read (default 10)
            
        Returns:
            List of message dicts with author, content, timestamp
        """
        messages = []
        
        if not self.client.is_ready():
            logger.error("Client not ready. Call this after connecting.")
            return messages

        channel = self.client.get_channel(CHANNEL_ID)
        if not channel:
            logger.error(f"Channel {CHANNEL_ID} not found")
            return messages
        
        try:
            async for msg in channel.history(limit=limit):
                messages.append({
                    'author': msg.author.name,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat(),
                    'message_id': msg.id
                })
            
            logger.info(f"Read {len(messages)} messages from channel history")
            return messages
            
        except Exception as e:
            logger.error(f"Error reading channel history: {e}")
            return messages
    
    def run(self):
        """Start the Discord client"""
        self.client.run(DISCORD_TOKEN)

    def _patch_pending_payments(self):
        """
        Work around discord.py-self handling pending_payments=None from the gateway.
        Prevents: TypeError: 'NoneType' object is not iterable
        """
        try:
            from discord import state as discord_state
        except Exception:
            return

        original = getattr(discord_state.ConnectionState, "parse_ready_supplemental", None)
        if not original or getattr(original, "_patched_pending_payments", False):
            return

        def patched(self, data):
            if not isinstance(data, dict):
                data = {}
            else:
                data = dict(data)

            pending = data.get("pending_payments")
            if not isinstance(pending, list):
                data["pending_payments"] = []

            try:
                return original(self, data)
            except TypeError as exc:
                if "NoneType" in str(exc) and "iterable" in str(exc):
                    data["pending_payments"] = []
                    try:
                        return original(self, data)
                    except Exception:
                        self.pending_payments = {}
                        return None
                raise

        patched._patched_pending_payments = True
        discord_state.ConnectionState.parse_ready_supplemental = patched
