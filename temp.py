"""
Simple script to read last 20 messages from Discord channel
Run: python temp.py
"""

import asyncio
import discord
from config.settings import DISCORD_TOKEN, CHANNEL_ID

# Patch discord.py-self bug
try:
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


async def read_messages():
    # Create client directly
    has_intents = hasattr(discord, 'Intents')
    if has_intents:
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)
    else:
        client = discord.Client()
    
    @client.event
    async def on_ready():
        print(f"\n✅ Connected as: {client.user.name}")
        
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            print(f"❌ Channel {CHANNEL_ID} not found")
            await client.close()
            return
        
        print(f"📖 Reading last 20 messages from: {channel.name}\n")
        print("="*70)
        
        messages = []
        async for msg in channel.history(limit=20):
            messages.append({
                'author': msg.author.name,
                'content': msg.content,
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        for i, msg in enumerate(messages, 1):
            print(f"\n[{i}] {msg['timestamp']} - {msg['author']}")
            print(f"{msg['content']}")
            print("-"*70)
        
        print(f"\n✅ Read {len(messages)} messages\n")
        await client.close()
    
    await client.start(DISCORD_TOKEN)


if __name__ == '__main__':
    asyncio.run(read_messages())