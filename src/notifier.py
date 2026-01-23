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
        try:
            # Build notification message
            tickers = [pick['ticker'] for pick in picks]
            ticker_str = ', '.join(tickers)
            
            message = f"Found {len(picks)} pick(s): {ticker_str}"
            if len(picks) == 1:
                pick = picks[0]
                message += f"\n{pick['action']} - Confidence: {pick['confidence']*100:.0f}%"
            
            notification.notify(
                title=f"📊 Stock Pick from {author}",
                message=message,
                timeout=10
            )
            logger.debug("Desktop notification sent")
        except Exception as e:
            logger.warning(f"Failed to send desktop notification: {e}")
    
    def _print_console_notification(self, picks, author):
        """Print formatted notification to console"""
        print("\n" + "="*60)
        print(f"📊 STOCK PICK DETECTED from {author}")
        print("="*60)
        
        for i, pick in enumerate(picks, 1):
            print(f"\nPick #{i}:")
            print(f"  Ticker: {pick['ticker']}")
            print(f"  Action: {pick['action']}")
            print(f"  Confidence: {pick['confidence']*100:.1f}%")
            if pick['weight']:
                print(f"  Weight: {pick['weight']}%")
            print(f"  Urgency: {pick['urgency']}")
            print(f"  Sentiment: {pick['sentiment']}")
            print(f"  Reasoning: {pick['reasoning']}")
        
        print("="*60 + "\n")
    
    def _copy_to_clipboard(self, picks):
        """Copy ticker(s) to clipboard"""
        try:
            tickers = [pick['ticker'] for pick in picks]
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
