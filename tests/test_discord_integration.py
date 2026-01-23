"""
Discord Integration Tests
Run: python tests/test_discord_integration.py
"""

import sys
import os
import asyncio
import time
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Patch discord.py-self bug
try:
    import discord
    if not hasattr(discord, 'Intents'):
        import discord.state
        _orig = discord.state.ConnectionState.parse_ready_supplemental
        def patched(self, data):
            data['pending_payments'] = data.get('pending_payments') or []
            data['merged_members'] = data.get('merged_members') or []
            return _orig(self, data)
        discord.state.ConnectionState.parse_ready_supplemental = patched
except:
    pass

from src.discord_client import StockMonitorClient
from config.settings import CHANNEL_ID, DISCORD_TOKEN


class MockMessage:
    def __init__(self, content, author_id=12345, channel_id=None):
        self.content = content
        self.author = MagicMock()
        self.author.id = author_id
        self.author.name = "TestUser"
        self.channel = MagicMock()
        self.channel.id = channel_id or CHANNEL_ID
        self.jump_url = "https://discord.com/mock/message"


class DiscordTests:
    
    def test_client_init(self):
        """Test client initializes"""
        print("Test 1: Client initialization")
        client = StockMonitorClient(trader=None)
        assert client.client is not None
        print("✅ Pass\n")
    
    async def test_message_filtering(self):
        """Test message filtering logic"""
        print("Test 2: Message filtering")
        client = StockMonitorClient(trader=None)
        
        mock_user = MagicMock()
        mock_user.id = 99999
        type(client.client).user = mock_user
        
        # These should all be filtered
        await client.on_message(MockMessage("AAPL", author_id=99999))  # Self
        await client.on_message(MockMessage("Hi"))  # Short
        await client.on_message(MockMessage("AAPL", channel_id=999))  # Wrong channel
        
        # This should process
        await client.on_message(MockMessage("AAPL is bullish"))
        
        print("✅ Pass\n")
    
    async def test_read_messages(self):
        """Test reading message history from channel"""
        print("Test 3: Read message history")
        
        if not DISCORD_TOKEN:
            print("⏭️  Skipped (no token)\n")
            return
        
        has_intents = hasattr(discord, 'Intents')
        if has_intents:
            intents = discord.Intents.default()
            intents.message_content = True
            client = discord.Client(intents=intents)
        else:
            client = discord.Client()
        
        messages = []
        done = False
        
        @client.event
        async def on_ready():
            nonlocal messages, done
            
            channel = client.get_channel(CHANNEL_ID)
            if not channel:
                print(f"❌ Channel {CHANNEL_ID} not found\n")
                done = True
                await client.close()
                return
            
            print(f"Connected as: {client.user.name}")
            print(f"Channel: {channel.name}")
            print("Reading last 5 messages...\n")
            
            try:
                async for msg in channel.history(limit=5):
                    messages.append({
                        'author': msg.author.name,
                        'content': msg.content,
                        'timestamp': msg.created_at.isoformat()
                    })
            except Exception as e:
                print(f"Error: {e}")
            
            done = True
            await client.close()
        
        task = asyncio.create_task(client.start(DISCORD_TOKEN))
        
        # Wait max 10 seconds
        start = time.time()
        while time.time() - start < 10 and not done:
            await asyncio.sleep(0.3)
        
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        if messages:
            print(f"✅ Read {len(messages)} messages:\n")
            for msg in messages:
                print(f"[{msg['timestamp']}] {msg['author']}:")
                print(f"{msg['content']}\n")
        else:
            print("⚠️  No messages found\n")
    
    async def test_listen_messages(self):
        """Test listening for new messages"""
        print("Test 4: Listen for new messages")
        
        if not DISCORD_TOKEN:
            print("⏭️  Skipped (no token)\n")
            return
        
        print("Listening for 20 seconds...")
        print("POST A MESSAGE TO YOUR CHANNEL NOW\n")
        
        has_intents = hasattr(discord, 'Intents')
        if has_intents:
            intents = discord.Intents.default()
            intents.message_content = True
            client = discord.Client(intents=intents)
        else:
            client = discord.Client()
        
        ready = False
        received = []
        
        @client.event
        async def on_ready():
            nonlocal ready
            ready = True
            print(f"👂 Listening as {client.user.name}...\n")
        
        @client.event
        async def on_message(message):
            if message.channel.id == CHANNEL_ID:
                received.append(message)
                print(f"📨 NEW MESSAGE from {message.author.name}:")
                print(f"{message.content}\n")
        
        task = asyncio.create_task(client.start(DISCORD_TOKEN))
        
        # Listen for 20 seconds
        start = time.time()
        while time.time() - start < 20:
            if ready and received:
                print(f"✅ Received {len(received)} message(s)\n")
                break
            await asyncio.sleep(0.5)
        
        if ready and not received:
            print("⏱️  No new messages (that's ok)\n")
        
        await client.close()
        
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


async def run_all_tests():
    print("\n" + "="*60)
    print("DISCORD TESTS")
    print("="*60 + "\n")
    
    tests = DiscordTests()
    
    tests.test_client_init()
    await tests.test_message_filtering()
    await tests.test_read_messages()
    await tests.test_listen_messages()
    
    print("="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60 + "\n")


if __name__ == '__main__':
    asyncio.run(run_all_tests())