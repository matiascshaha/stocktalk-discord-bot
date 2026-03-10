from datetime import date
from typing import Any, Optional

import discord
from pydantic import ValidationError

from config.settings import CHANNEL_ID, DISCORD_TOKEN, TRADING_CONFIG
from src.ai_parser import AIParser
from src.brokerages.ports import TradingBrokerPort
from src.brokerages.webull import WebullBroker
from src.channels.discord.runtime_flags import DiscordRuntimeFlags
from src.channels.discord.runtime_patcher import DiscordRuntimePatcher
from src.channels.discord.signal_logger import DiscordSignalLogger
from src.channels.discord.signal_order_mapper import DiscordSignalOrderMapper
from src.models.parser_models import CONTRACT_VERSION, ParsedMessage, ParsedSignal
from src.notifier import Notifier
from src.trading.contracts import OptionOrder, OrderType, StockOrder
from src.trading.orders import StockOrderExecutionPlanner, StockOrderExecutor
from src.utils.logger import setup_logger
from src.utils.logging_format import format_pick_summary, format_startup_status
from src.utils.paths import PICKS_LOG_PATH

logger = setup_logger("discord_client")

ALLOW_ALL_CHANNELS_FOR_TESTING = DiscordRuntimeFlags.env_enabled("DISCORD_ALLOW_ALL_CHANNELS")
ALLOW_SELF_MESSAGES_FOR_TESTING = DiscordRuntimeFlags.env_enabled("DISCORD_ALLOW_SELF_MESSAGES")


class StockMonitorClient:
    """Discord client for monitoring stock picks."""

    def __init__(
        self,
        trader: Optional[Any] = None,
        broker: Optional[TradingBrokerPort] = None,
        trading_account: Optional[Any] = None,
    ):
        self.trader = trader
        self.trading_account = trading_account or trader
        self.parser = AIParser()
        self.notifier = Notifier()
        self.order_executor: Optional[StockOrderExecutor] = None
        self._broker = self._resolve_broker(broker, trader)
        self._signal_mapper = DiscordSignalOrderMapper(trading_config=TRADING_CONFIG, logger=logger)
        self._signal_logger = DiscordSignalLogger(logger=logger)
        self._runtime_patcher = DiscordRuntimePatcher(logger=logger)

        if self._broker is not None:
            planner = StockOrderExecutionPlanner(TRADING_CONFIG)
            self.order_executor = StockOrderExecutor(self._broker, planner)

        self._patch_pending_payments()
        self.client = self._create_discord_client()
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

    @staticmethod
    def _resolve_broker(broker: Optional[TradingBrokerPort], trader: Optional[Any]) -> Optional[TradingBrokerPort]:
        if broker is not None:
            return broker
        if trader is None:
            return None
        return WebullBroker(trader)

    @staticmethod
    def _create_discord_client() -> discord.Client:
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            return discord.Client(intents=intents)
        except AttributeError:
            return discord.Client()

    async def on_ready(self):
        logger.info("=" * 60)
        logger.info("Discord stock monitor active.")
        logger.info("=" * 60)
        for line in format_startup_status(
            self.client.user,
            CHANNEL_ID,
            self.parser.provider,
            bool(self.order_executor),
            bool(TRADING_CONFIG.get("options_enabled")),
            CONTRACT_VERSION,
        ):
            logger.info(line)
        logger.info("=" * 60)
        logger.info("Waiting for stock picks.")

    async def on_message(self, message):
        if self._should_ignore_message(message):
            return

        logger.info("New message from %s", message.author.name)
        logger.debug("Message content: %s...", message.content[:100])
        parsed_message = self._parse_message(message)
        if parsed_message is None:
            return

        signals = parsed_message.signals
        parsed_payload = parsed_message.model_dump()
        if not signals:
            logger.info("No actionable signals detected.")
            return

        logger.info("Detected %s signal(s).", len(signals))
        logger.info(format_pick_summary(parsed_payload))
        self.notifier.notify(parsed_payload, message.author.name)
        self._log_signals(message, parsed_payload)
        await self._execute_signals(signals)

    def _should_ignore_message(self, message: Any) -> bool:
        if not ALLOW_ALL_CHANNELS_FOR_TESTING and message.channel.id != CHANNEL_ID:
            logger.debug("Ignoring message from channel %s", message.channel.id)
            return True

        if (
            not ALLOW_SELF_MESSAGES_FOR_TESTING
            and self.client.user
            and message.author.id == self.client.user.id
        ):
            logger.debug("Ignoring own message")
            return True

        content = (message.content or "").strip()
        if len(content) < 3:
            logger.debug("Ignoring short message")
            return True
        return False

    def _parse_message(self, message: Any) -> Optional[ParsedMessage]:
        logger.info("AI analyzing message.")
        parsed = self.parser.parse(message.content, message.author.name, message.channel.id, self.trading_account)
        if not isinstance(parsed, dict):
            logger.warning("Parser returned unexpected type: %s", type(parsed).__name__)
            return None

        try:
            return ParsedMessage.model_validate(parsed)
        except ValidationError as exc:
            logger.warning("Parser returned invalid payload: %s", exc)
            return None

    async def _execute_signals(self, signals: list[ParsedSignal]) -> None:
        if not self.order_executor and not self._options_execution_enabled():
            return

        for signal in signals:
            if not self._passes_min_confidence(signal):
                logger.info(
                    "Skipping trade for %s due to confidence %.3f below min_confidence %.3f",
                    signal.ticker,
                    float(signal.confidence),
                    self._min_confidence_threshold(),
                )
                continue
            self._execute_stock_signal(signal)
            self._execute_option_signal(signal)

    def _execute_stock_signal(self, signal: ParsedSignal) -> None:
        if self.order_executor is None:
            return
        order = self._signal_to_stock_order(signal)
        if order is None:
            return

        try:
            self.order_executor.execute(order, weighting=signal.weight_percent)
        except Exception as exc:
            logger.error(
                "Trade execution failed for %s %s (%s): %s",
                order.side,
                order.symbol,
                signal.weight_percent,
                exc,
            )

    def _execute_option_signal(self, signal: ParsedSignal) -> None:
        if not self._options_execution_enabled():
            return

        for option_order in self._signal_to_option_orders(signal):
            try:
                option_result = self._broker.place_option_order(option_order, weighting=signal.weight_percent)
                logger.info(
                    "Option trade submitted for %s %s %s %.2f exp=%s (order_id=%s)",
                    option_order.side,
                    option_order.symbol,
                    option_order.option_type,
                    option_order.strike_price,
                    option_order.option_expire_date,
                    option_result.order_id,
                )
            except Exception as exc:
                logger.error(
                    "Option trade execution failed for %s %s %s %.2f exp=%s: %s",
                    option_order.side,
                    option_order.symbol,
                    option_order.option_type,
                    option_order.strike_price,
                    option_order.option_expire_date,
                    exc,
                )

    def _signal_to_stock_order(self, signal: ParsedSignal) -> Optional[StockOrder]:
        return self._signal_mapper.to_stock_order(signal)

    def _signal_to_option_orders(self, signal: ParsedSignal) -> list[OptionOrder]:
        return self._signal_mapper.to_option_orders(signal)

    def _options_execution_enabled(self) -> bool:
        if not TRADING_CONFIG.get("options_enabled"):
            return False
        if self._broker is None:
            return False
        return hasattr(self._broker, "place_option_order")

    def _resolve_option_quantity(self, quantity_hint: Optional[float]) -> int:
        return self._signal_mapper.resolve_option_quantity(quantity_hint)

    def _resolve_option_order_type(self) -> OrderType:
        return self._signal_mapper.resolve_option_order_type()

    def _resolve_option_limit_price(self, order_type: OrderType) -> Optional[float]:
        return self._signal_mapper.resolve_option_limit_price(order_type)

    def _resolve_time_in_force(self) -> str:
        return self._signal_mapper.resolve_time_in_force()

    def _normalize_option_expiry(self, raw_expiry: Optional[str]) -> Optional[str]:
        return self._signal_mapper.normalize_option_expiry(raw_expiry)

    def _third_friday(self, year: int, month: int) -> date:
        return self._signal_mapper.third_friday(year, month)

    def _min_confidence_threshold(self) -> float:
        return self._signal_mapper.min_confidence_threshold()

    def _passes_min_confidence(self, signal: ParsedSignal) -> bool:
        return self._signal_mapper.passes_min_confidence(signal)

    def _log_signals(self, message: Any, parsed_message: dict) -> None:
        self._signal_logger.append(message=message, parsed_message=parsed_message, output_path=PICKS_LOG_PATH)

    async def read_channel_history(self, limit: int = 10):
        messages = []
        if not self.client.is_ready():
            logger.error("Client not ready. Call this after connecting.")
            return messages

        channel = self.client.get_channel(CHANNEL_ID)
        if not channel:
            logger.error("Channel %s not found", CHANNEL_ID)
            return messages

        try:
            async for msg in channel.history(limit=limit):
                messages.append(
                    {
                        "author": msg.author.name,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat(),
                        "message_id": msg.id,
                    }
                )
            logger.info("Read %s messages from channel history", len(messages))
            return messages
        except Exception as exc:
            logger.error("Error reading channel history: %s", exc)
            return messages

    def run(self):
        self.client.run(DISCORD_TOKEN)

    def _patch_pending_payments(self):
        self._runtime_patcher.patch_pending_payments()
