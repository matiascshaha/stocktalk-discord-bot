import sys

import pyperclip
from plyer import notification

from config.settings import NOTIFICATION_CONFIG
from src.utils.logger import setup_logger

logger = setup_logger("notifier")


class Notifier:
    """Handle notifications for parsed signals."""

    def __init__(self):
        self.config = NOTIFICATION_CONFIG
        self._plyer_available = True

    def notify(self, parsed_message, author):
        if not parsed_message:
            return

        if self.config["desktop_notifications"]:
            self._send_desktop_notification(parsed_message, author)

        self._print_console_notification(parsed_message, author)

        if self.config["copy_to_clipboard"]:
            self._copy_to_clipboard(parsed_message)

        if self.config["sound_alert"]:
            self._play_sound()

    def _signal_objs(self, parsed_message):
        return parsed_message.get("signals", []) if isinstance(parsed_message, dict) else []

    def _send_desktop_notification(self, parsed_message, author):
        signal_objs = self._signal_objs(parsed_message)
        if not signal_objs:
            logger.warning("No signals to notify")
            return

        tickers = [signal.get("ticker") for signal in signal_objs if signal.get("ticker")]
        ticker_str = ", ".join(tickers)

        message = f"Found {len(signal_objs)} signal(s): {ticker_str}"
        if len(signal_objs) == 1:
            signal = signal_objs[0]
            message += f"\n{signal.get('action')} - Confidence: {float(signal.get('confidence', 0.0))*100:.0f}%"

        title = f"📊 Stock Signal from {author}"

        try:
            notification.notify(title=title, message=message, timeout=10)
            logger.debug("Desktop notification sent via plyer")
            return
        except Exception as exc:
            if self._plyer_available:
                logger.warning(f"Failed to send desktop notification via plyer: {exc}")
                self._plyer_available = False

        if sys.platform == "darwin":
            try:
                import subprocess

                subprocess.run(
                    ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                    check=False,
                )
                logger.debug("Desktop notification sent via osascript")
            except Exception as exc:
                logger.warning(f"Failed to send desktop notification via osascript: {exc}")

    def _print_console_notification(self, parsed_message, author):
        print("\n" + "=" * 60)
        print(f"📊 STOCK SIGNAL DETECTED from {author}")
        print("=" * 60)

        signal_objs = self._signal_objs(parsed_message)
        for i, signal in enumerate(signal_objs, 1):
            print(f"\nSignal #{i}:")
            print(f"  Ticker: {signal.get('ticker')}")
            print(f"  Action: {signal.get('action')}")
            print(f"  Confidence: {float(signal.get('confidence', 0.0))*100:.1f}%")
            if signal.get("weight_percent") is not None:
                print(f"  Weight: {signal.get('weight_percent')}%")
            print(f"  Urgency: {signal.get('urgency')}")
            print(f"  Sentiment: {signal.get('sentiment')}")
            print(f"  Reasoning: {signal.get('reasoning')}")

            vehicles = signal.get("vehicles") or []
            if vehicles:
                vehicle_types = [v.get("type") for v in vehicles if isinstance(v, dict)]
                print(f"  Vehicles: {', '.join([v for v in vehicle_types if v])}")

        print("=" * 60 + "\n")

    def _copy_to_clipboard(self, parsed_message):
        try:
            signal_objs = self._signal_objs(parsed_message)
            tickers = [signal.get("ticker") for signal in signal_objs if signal.get("ticker")]
            if not tickers:
                return
            pyperclip.copy(", ".join(tickers))
            logger.debug("Copied signal ticker list to clipboard")
        except Exception as exc:
            logger.warning(f"Failed to copy to clipboard: {exc}")

    def _play_sound(self):
        try:
            if sys.platform == "win32":
                import winsound

                winsound.Beep(1000, 200)
            elif sys.platform == "darwin":
                import os

                os.system("afplay /System/Library/Sounds/Glass.aiff")
            else:
                import os

                os.system('paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null || echo -e "\\a"')
        except Exception as exc:
            logger.debug(f"Could not play sound: {exc}")
