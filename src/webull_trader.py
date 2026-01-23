from webull import webull
import json
import os
from datetime import datetime
from config.settings import TRADING_CONFIG
from src.utils.logger import setup_logger

logger = setup_logger('webull_trader')

class WebullTrader:
    """Webull trading integration"""
    
    def __init__(self, config):
        self.config = config
        self.wb = webull()
        self.logged_in = False
    
    def login(self):
        """Login to Webull"""
        try:
            self.wb.login(
                self.config['username'],
                self.config['password']
            )
            self.wb.get_trade_token(self.config['trading_pin'])
            
            account = self.wb.get_account()
            logger.info("✅ Logged into Webull successfully")
            logger.info(f"💰 Account Value: ${float(account['netLiquidation']):,.2f}")
            logger.info(f"💵 Cash Available: ${float(account['accountMembers'][1]['value']):,.2f}")
            
            self.logged_in = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Webull login failed: {e}")
            self.logged_in = False
            return False
    
    def execute_trade(self, pick):
        """Execute trade based on pick"""
        
        # Validate preconditions
        if not self._should_trade(pick):
            return
        
        # Only handle BUY for now
        if pick['action'] != 'BUY':
            logger.info(f"ℹ️  {pick['action']} action for {pick['ticker']} - manual action required")
            return
        
        # Only trade stocks (not options)
        if pick['option_type'] != 'STOCK':
            logger.warning(f"⚠️  Options trading not supported for {pick['ticker']}")
            return
        
        try:
            self._place_order(pick)
        except Exception as e:
            logger.error(f"❌ Trade execution failed for {pick['ticker']}: {e}")
    
    def _should_trade(self, pick):
        """Determine if we should execute this trade"""
        
        if not self.logged_in:
            logger.warning("⚠️  Not logged into Webull")
            return False
        
        if pick['confidence'] < TRADING_CONFIG['min_confidence']:
            logger.info(
                f"⚠️  Confidence too low ({pick['confidence']:.2f}) for {pick['ticker']}. "
                f"Threshold: {TRADING_CONFIG['min_confidence']}"
            )
            return False
        
        return True
    
    def _place_order(self, pick):
        """Place order on Webull"""
        ticker = pick['ticker']
        
        # Get current price
        quote = self.wb.get_quote(ticker)
        if not quote:
            logger.error(f"❌ Could not get quote for {ticker}")
            return
        
        current_price = float(quote['close'])
        
        # Calculate quantity
        account = self.wb.get_account()
        cash_available = float(account['accountMembers'][1]['value'])
        
        if pick['weight']:
            dollar_amount = (pick['weight'] / 100) * cash_available
        else:
            dollar_amount = TRADING_CONFIG['default_amount']
        
        quantity = int(dollar_amount / current_price)
        
        if quantity < 1:
            logger.warning(f"⚠️  Not enough cash to buy {ticker} (need ${current_price:.2f})")
            return
        
        # Place order
        logger.info(f"\n🔄 Executing: {pick['action']} {quantity} shares of {ticker}")
        logger.info(f"   Price: ${current_price:.2f}")
        logger.info(f"   Total: ${quantity * current_price:.2f}")
        logger.info(f"   Confidence: {pick['confidence']*100:.0f}%")
        
        if TRADING_CONFIG['use_market_orders']:
            order = self.wb.place_order(
                stock=ticker,
                action='BUY',
                orderType='MKT',
                quant=quantity,
            )
        else:
            order = self.wb.place_order(
                stock=ticker,
                action='BUY',
                orderType='LMT',
                price=current_price,
                quant=quantity,
            )
        
        logger.info(f"✅ ORDER PLACED: BUY {quantity} shares of {ticker}")
        logger.info(f"   Order ID: {order.get('orderId', 'N/A')}\n")
        
        # Log trade
        self._log_trade(pick, quantity, current_price, order)
    
    def _log_trade(self, pick, quantity, price, order):
        """Log trade to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'ticker': pick['ticker'],
            'action': pick['action'],
            'quantity': quantity,
            'price': price,
            'total_cost': quantity * price,
            'confidence': pick['confidence'],
            'reasoning': pick['reasoning'],
            'order': order,
            'pick_details': pick,
        }
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        with open('data/trades_log.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.info("📝 Trade logged to trades_log.jsonl")
