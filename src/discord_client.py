import discord
import json
from datetime import datetime

from pydantic import ValidationError
from src.ai_parser import AIParser
from src.execution.stock_order_policy import (
    build_buffered_limit_order,
    build_market_order,
    is_non_trading_hours_error,
    resolve_buffer_bps,
    resolve_time_in_force,
)
from src.models.parser_models import CONTRACT_VERSION, ParsedMessage, ParsedSignal
from src.notifier import Notifier
from src.utils.logger import setup_logger
from src.utils.logging_format import format_startup_status, format_pick_summary
from src.utils.paths import PICKS_LOG_PATH
from src.webull_trader import WebullTrader
from src.models.webull_models import OrderSide, OrderType, StockOrderRequest, TimeInForce
from config.settings import DISCORD_TOKEN, CHANNEL_ID, TRADING_CONFIG

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
            bool(TRADING_CONFIG.get("options_enabled")),
            CONTRACT_VERSION,
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

        signal_objs = parsed_message.signals
        parsed_payload = parsed_message.model_dump()

        if signal_objs:
            logger.info(f"Detected {len(signal_objs)} signal(s).")
            logger.debug("Picks details: %s", json.dumps(parsed_payload, indent=2))
            logger.info(format_pick_summary(parsed_payload))

            # Send notifications
            self.notifier.notify(parsed_payload, message.author.name)

            # Log parsed signals
            self._log_signals(message, parsed_payload)

            # Execute trades if trader available
            if self.trader:
                for signal in signal_objs:
                    order = self._signal_to_stock_order(signal)
                    if not order:
                        continue
                    self._execute_stock_signal(signal, order)
        else:
            logger.info("No actionable signals detected.")

    def _signal_to_stock_order(self, signal: ParsedSignal):
        stock_vehicle = None
        for vehicle in signal.vehicles:
            if vehicle.type == "STOCK":
                stock_vehicle = vehicle
                break

        if not stock_vehicle:
            return None

        if not stock_vehicle.enabled or stock_vehicle.intent != "EXECUTE":
            return None

        if stock_vehicle.side == "NONE":
            logger.info("Skipping non-executable stock signal for %s", signal.ticker)
            return None

        side = OrderSide.SELL if stock_vehicle.side == "SELL" else OrderSide.BUY
        time_in_force = resolve_time_in_force(TRADING_CONFIG.get("time_in_force"), TimeInForce.DAY)
        return StockOrderRequest(
            symbol=signal.ticker,
            side=side,
            quantity=1,
            order_type=OrderType.MARKET,
            time_in_force=time_in_force,
            extended_hours_trading=bool(TRADING_CONFIG.get("extended_hours_trading", False)),
        )

    def _execute_stock_signal(self, signal: ParsedSignal, base_order: StockOrderRequest) -> None:
        try:
            primary_order = self._build_primary_stock_order(base_order)
        except Exception as exc:
            logger.error(
                "Trade execution skipped for %s %s (%s): unable to build primary order: %s",
                base_order.side,
                base_order.symbol,
                signal.weight_percent,
                exc,
            )
            return

        logger.info(
            "Submitting primary order %s %s qty=%s type=%s tif=%s ext_hours=%s",
            primary_order.side,
            primary_order.symbol,
            primary_order.quantity,
            primary_order.order_type,
            primary_order.time_in_force,
            primary_order.extended_hours_trading,
        )

        try:
            self.trader.place_stock_order(primary_order, weighting=signal.weight_percent)
            return
        except Exception as exc:
            if not bool(TRADING_CONFIG.get("queue_when_closed", True)) or not is_non_trading_hours_error(exc):
                logger.error(
                    "Trade execution failed for %s %s (%s): %s",
                    primary_order.side,
                    primary_order.symbol,
                    signal.weight_percent,
                    exc,
                )
                return
            logger.warning(
                "Primary order rejected outside trading hours for %s. Retrying as queued LIMIT.",
                primary_order.symbol,
            )

        try:
            queue_order = self._build_queue_fallback_order(primary_order)
        except Exception as exc:
            logger.error(
                "Trade execution failed for %s %s (%s): unable to build queued fallback: %s",
                primary_order.side,
                primary_order.symbol,
                signal.weight_percent,
                exc,
            )
            return

        logger.info(
            "Submitting queued fallback %s %s qty=%s type=%s limit=%s tif=%s ext_hours=%s",
            queue_order.side,
            queue_order.symbol,
            queue_order.quantity,
            queue_order.order_type,
            queue_order.limit_price,
            queue_order.time_in_force,
            queue_order.extended_hours_trading,
        )
        try:
            self.trader.place_stock_order(queue_order, weighting=signal.weight_percent)
        except Exception as exc:
            logger.error(
                "Queued fallback failed for %s %s (%s): %s",
                queue_order.side,
                queue_order.symbol,
                signal.weight_percent,
                exc,
            )

    def _build_primary_stock_order(self, order: StockOrderRequest) -> StockOrderRequest:
        time_in_force = resolve_time_in_force(TRADING_CONFIG.get("time_in_force"), TimeInForce.DAY)
        extended_hours = bool(TRADING_CONFIG.get("extended_hours_trading", False))
        use_market_orders = bool(TRADING_CONFIG.get("use_market_orders", True))
        if use_market_orders:
            return build_market_order(order, time_in_force=time_in_force, extended_hours_trading=extended_hours)

        quote = self._require_quote(order.symbol)
        buffer_bps = resolve_buffer_bps(TRADING_CONFIG.get("out_of_hours_limit_buffer_bps", 50.0))
        return build_buffered_limit_order(
            order,
            quote=quote,
            buffer_bps=buffer_bps,
            time_in_force=time_in_force,
            extended_hours_trading=extended_hours,
        )

    def _build_queue_fallback_order(self, order: StockOrderRequest) -> StockOrderRequest:
        quote = self._require_quote(order.symbol)
        buffer_bps = resolve_buffer_bps(TRADING_CONFIG.get("out_of_hours_limit_buffer_bps", 50.0))
        queue_tif = resolve_time_in_force(TRADING_CONFIG.get("queue_time_in_force"), TimeInForce.GTC)
        return build_buffered_limit_order(
            order,
            quote=quote,
            buffer_bps=buffer_bps,
            time_in_force=queue_tif,
            extended_hours_trading=bool(TRADING_CONFIG.get("extended_hours_trading", False)),
        )

    def _require_quote(self, symbol: str) -> float:
        if not self.trader:
            raise ValueError("Trader is required to fetch quote for limit order pricing")

        quote = self.trader.get_current_stock_quote(symbol)
        if quote is None:
            raise ValueError(f"Unable to fetch quote for symbol {symbol}")

        quote_float = float(quote)
        if quote_float <= 0:
            raise ValueError(f"Invalid quote for symbol {symbol}: {quote}")
        return quote_float

    def _log_signals(self, message, parsed_message):
        """Log parsed signals to file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "author": str(message.author),
            "message": message.content,
            "message_url": message.jump_url,
            "ai_parsed_signals": parsed_message,
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
