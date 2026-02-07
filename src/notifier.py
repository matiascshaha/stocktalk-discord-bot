import pyperclip
from plyer import notification
from datetime import datetime
import sys
from config.settings import NOTIFICATION_CONFIG
from src.utils.logger import setup_logger

logger = setup_logger('notifier')

class Notifier:
    """Handle notifications for stock picks"""
    
    def __init__(self):
        self.config = NOTIFICATION_CONFIG
        self._plyer_available = True
    
    def notify(self, picks, author):
        """Send notifications for picks"""
        if not picks:
            return
        
        # Desktop notification
        if self.config['desktop_notifications']:
            self._send_desktop_notification(picks, author)
        
        # Console output
        self._print_console_notification(picks, author)
        
        # Copy to clipboard
        if self.config['copy_to_clipboard']:
            self._copy_to_clipboard(picks)
        
        # Sound alert
        if self.config['sound_alert']:
            self._play_sound()
    
    def _send_desktop_notification(self, picks, author):
        """Send desktop notification"""
        # Build notification message
        pick_objs = picks.get("picks", [])
        if not pick_objs:
            logger.warning("No picks to notify")
            return
        
        tickers = [pick['ticker'] for pick in pick_objs]
        ticker_str = ', '.join(tickers)

        message = f"Found {len(pick_objs)} pick(s): {ticker_str}"
        if len(pick_objs) == 1:
            pick = pick_objs[0]
            message += f"\n{pick['action']} - Confidence: {pick['confidence']*100:.0f}%"

        title = f"📊 Stock Pick from {author}"

        try:
            notification.notify(
                title=title,
                message=message,
                timeout=10
            )
            logger.debug("Desktop notification sent via plyer")
            return
        except Exception as e:
            if self._plyer_available:
                logger.warning(f"Failed to send desktop notification via plyer: {e}")
                self._plyer_available = False

        # macOS fallback using osascript (avoids pyobjus dependency)
        if sys.platform == 'darwin':
            try:
                import subprocess
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{message}" with title "{title}"'
                    ],
                    check=False,
                )
                logger.debug("Desktop notification sent via osascript")
            except Exception as e:
                logger.warning(f"Failed to send desktop notification via osascript: {e}")
    
    def _print_console_notification(self, picks, author):
        """Print formatted notification to console"""
        print("\n" + "="*60)
        print(f"📊 STOCK PICK DETECTED from {author}")
        print("="*60)

        pick_objs = picks.get("picks", [])
        for i, pick in enumerate(pick_objs, 1):
            print(f"\nPick #{i}:")
            print(f"  Ticker: {pick['ticker']}")
            print(f"  Action: {pick['action']}")
            print(f"  Confidence: {pick['confidence']*100:.1f}%")
            if pick['weight_percent']:
                print(f"  Weight: {pick['weight_percent']}%")
            print(f"  Urgency: {pick['urgency']}")
            print(f"  Sentiment: {pick['sentiment']}")
            print(f"  Reasoning: {pick['reasoning']}")
        
        print("="*60 + "\n")
    
    def _copy_to_clipboard(self, picks):
        """Copy ticker(s) to clipboard"""
        try:
            pick_objs = picks.get("picks", [])
            tickers = [pick['ticker'] for pick in pick_objs if pick.get("ticker")]
            if not tickers:
                return
            ticker_str = ', '.join(tickers)
            pyperclip.copy(ticker_str)
            logger.debug(f"Copied {ticker_str} to clipboard")
        except Exception as e:
            logger.warning(f"Failed to copy to clipboard: {e}")
    
    def _play_sound(self):
        """Play system sound alert"""
        try:
            # Windows
            if sys.platform == 'win32':
                import winsound
                winsound.Beep(1000, 200)  # 1000Hz for 200ms
            # macOS
            elif sys.platform == 'darwin':
                import os
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            # Linux
            else:
                import os
                os.system('paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null || echo -e "\a"')
        except Exception as e:
            logger.debug(f"Could not play sound: {e}")
