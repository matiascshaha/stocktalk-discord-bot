import discord
import json
import os
from datetime import datetime
from src.ai_parser import AIParser
from src.notifier import Notifier
from src.utils.logger import setup_logger
from config.settings import DISCORD_TOKEN, CHANNEL_ID

logger = setup_logger('discord_client')

class StockMonitorClient:
    """Discord client for monitoring stock picks"""
    
    def __init__(self, trader=None):
        self.trader = trader
        self.parser = AIParser()
        self.notifier = Notifier()
        
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
        logger.info("🤖 DISCORD STOCK MONITOR ACTIVE")
        logger.info("="*60)
        logger.info(f"📱 Logged in as: {self.client.user}")
        logger.info(f"📊 Monitoring channel: {CHANNEL_ID}")
        logger.info(f"🧠 AI Parser: {self.parser.provider.title() if self.parser.provider else 'None (Regex only)'}")
        logger.info(f"🤖 Auto-trading: {'ENABLED' if self.trader else 'DISABLED'}")
        logger.info("="*60)
        logger.info("\n⏳ Waiting for stock picks...\n")
    
    async def on_message(self, message):
        """Called when a message is received"""
        # Filter messages
        # if message.channel.id != CHANNEL_ID:
        #     logger.debug(f"Ignoring message from channel {message.channel.id}")
        #     return
        
        # if message.author.id == self.client.user.id:
        #     logger.debug("Ignoring own message")
        #     return
        
        # if len(message.content) < 3:
        #     logger.debug("Ignoring short message")
        #     return
        
        logger.info(f"\n📨 New message from {message.author.name}")
        logger.debug(f"Message content: {message.content[:100]}...")
        
        # Parse message with AI
        logger.info("🧠 AI analyzing message...")
        picks = self.parser.parse(message.content, message.author.name)
        
        if picks:
            logger.info(f"✅ AI found {len(picks)} pick(s)")
            
            # Send notifications
            self.notifier.notify(picks, message.author.name)
            
            # Log picks
            self._log_picks(message, picks)
            
            # Execute trades if trader available
            if self.trader:
                for pick in picks:
                    self.trader.execute_trade(pick)
        else:
            logger.info("ℹ️  No stock picks detected")
    
    def _log_picks(self, message, picks):
        """Log picks to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'author': str(message.author),
            'message': message.content,
            'message_url': message.jump_url,
            'ai_parsed_picks': picks,
        }
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        with open('data/picks_log.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.debug("📝 Pick logged to picks_log.jsonl")
    
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
        so
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