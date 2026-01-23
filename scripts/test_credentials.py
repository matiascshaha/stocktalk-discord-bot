#!/usr/bin/env python3
"""
Credential Testing Script

Tests all configured credentials to ensure they're valid before running the monitor.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

def test_discord_token():
    """Test Discord token validity"""
    print("\n" + "="*60)
    print("Testing Discord Token...")
    print("="*60)
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN not found in .env file")
        return False
    
    try:
        import discord
        # discord.py-self doesn't use Intents the same way
        # Try with Intents first, fallback to no Intents
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            client = discord.Client(intents=intents)
        except AttributeError:
            # discord.py-self may not have Intents
            client = discord.Client()
        
        login_success = False
        error_occurred = False
        
        @client.event
        async def on_ready():
            nonlocal login_success
            login_success = True
            print(f"✅ Discord token is valid!")
            print(f"   Logged in as: {client.user}")
            print(f"   User ID: {client.user.id}")
            await client.close()
        
        @client.event
        async def on_error(event, *args, **kwargs):
            nonlocal error_occurred
            error_occurred = True
            print(f"❌ Discord error: {event}")
            await client.close()
        
        try:
            # Use run() which handles the event loop
            client.run(token, log_handler=None)
            return login_success
        except discord.LoginFailure:
            print("❌ Invalid Discord token - login failed")
            return False
        except TypeError as e:
            if "iterable" in str(e):
                print("❌ Discord library compatibility issue")
                print("   Try: pip install --upgrade discord.py-self")
            return False
        except Exception as e:
            if login_success:
                return True  # Connected successfully before error
            print(f"❌ Discord connection error: {e}")
            return False
            
    except ImportError:
        print("⚠️  discord.py not installed. Install with: pip install discord.py-self")
        return False

def test_discord_channel():
    """Test Discord channel ID accessibility"""
    print("\n" + "="*60)
    print("Testing Discord Channel ID...")
    print("="*60)
    
    channel_id = os.getenv('CHANNEL_ID')
    if not channel_id:
        print("❌ CHANNEL_ID not found in .env file")
        return False
    
    try:
        channel_id_int = int(channel_id)
        print(f"✅ Channel ID format is valid: {channel_id_int}")
        print("   Note: Cannot verify channel exists without valid Discord token")
        return True
    except ValueError:
        print(f"❌ Invalid Channel ID format: {channel_id}")
        print("   Channel ID must be a number")
        return False

def test_openai_key():
    """Test OpenAI API key"""
    print("\n" + "="*60)
    print("Testing OpenAI API Key...")
    print("="*60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ℹ️  OPENAI_API_KEY not found (skipping)")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API key is valid!")
        print(f"   Model: gpt-4o-mini")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("⚠️  openai package not installed. Install with: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI API key test failed: {e}")
        return False

def test_anthropic_key():
    """Test Anthropic API key"""
    print("\n" + "="*60)
    print("Testing Anthropic API Key...")
    print("="*60)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ℹ️  ANTHROPIC_API_KEY not found (skipping)")
        return None
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test call
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=5,
            messages=[{"role": "user", "content": "Say 'test'"}]
        )
        
        print("✅ Anthropic API key is valid!")
        print(f"   Model: claude-sonnet-4-5")
        print(f"   Response: {response.content[0].text}")
        return True
        
    except ImportError:
        print("⚠️  anthropic package not installed. Install with: pip install anthropic")
        return False
    except Exception as e:
        print(f"❌ Anthropic API key test failed: {e}")
        return False

def test_google_key():
    """Test Google Gemini API key"""
    print("\n" + "="*60)
    print("Testing Google Gemini API Key...")
    print("="*60)
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("ℹ️  GOOGLE_API_KEY not found (skipping)")
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-3-pro-preview')
        response = model.generate_content("Say 'test'")
        
        print("✅ Google API key is valid!")
        print(f"   Model: gemini-3-pro-preview")
        print(f"   Response: {response.text}")
        return True
        
    except ImportError:
        print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Google API key test failed: {e}")
        return False

def test_webull_credentials():
    """Test Webull credentials using their SDK"""
    print("\n" + "="*60)
    print("Testing Webull Credentials...")
    print("="*60)
    
    username = os.getenv('WEBULL_USERNAME')
    password = os.getenv('WEBULL_PASSWORD')
    trading_pin = os.getenv('WEBULL_TRADING_PIN')
    
    if not username or not password:
        print("ℹ️  Webull credentials not found (skipping)")
        print("   These are optional unless AUTO_TRADE=true")
        return None
    
    try:
        from webull import webull
        wb = webull()
        
        print("Attempting to log in...")
        wb.login(username, password)
        
        if trading_pin:
            print("Getting trade token...")
            wb.get_trade_token(trading_pin)
        
        account = wb.get_account()
        
        print("✅ Webull credentials are valid!")
        print(f"   Account Value: ${float(account['netLiquidation']):,.2f}")
        print(f"   Cash Available: ${float(account['accountMembers'][1]['value']):,.2f}")
        return True
        
    except ImportError:
        print("⚠️  webull package not installed. Install with: pip install webull")
        return False
    except Exception as e:
        print(f"❌ Webull login failed: {e}")
        print("   Check your username, password, and trading PIN")
        return False

def main():
    """Run all credential tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        Discord Stock Monitor - Credential Tester          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # Test Discord
    results['discord_token'] = test_discord_token()
    results['discord_channel'] = test_discord_channel()
    
    # Test AI providers (check which one is configured)
    ai_provider = os.getenv('AI_PROVIDER', '').lower()
    
    # If AI_PROVIDER is set, only test that one
    if ai_provider == 'openai':
        results['openai'] = test_openai_key()
    elif ai_provider == 'anthropic':
        results['anthropic'] = test_anthropic_key()
    elif ai_provider == 'google':
        results['google'] = test_google_key()
    else:
        # If not specified, test all that have keys configured
        # This helps users figure out which provider they want to use
        results['openai'] = test_openai_key()
        results['anthropic'] = test_anthropic_key()
        results['google'] = test_google_key()
    
    # Test Webull (optional)
    results['webull'] = test_webull_credentials()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    required_passed = True
    ai_provider_configured = False
    
    for name, result in results.items():
        if result is None:
            status = "⏭️  Skipped"
        elif result:
            status = "✅ Passed"
            if name in ['openai', 'anthropic', 'google']:
                ai_provider_configured = True
        else:
            status = "❌ Failed"
            # Discord is always required
            if name in ['discord_token', 'discord_channel']:
                required_passed = False
            # AI provider is required if one is configured
            elif name in ['openai', 'anthropic', 'google']:
                if ai_provider and ai_provider == name:
                    required_passed = False
        
        print(f"  {name.replace('_', ' ').title()}: {status}")
    
    # Check if at least one AI provider is configured
    if not ai_provider_configured and not ai_provider:
        print("\n⚠️  No AI provider configured!")
        print("   Set AI_PROVIDER in .env (openai, anthropic, or google)")
        print("   See docs/AI_PROVIDER_COMPARISON.md for recommendations")
        required_passed = False
    
    print("\n" + "="*60)
    if required_passed:
        print("✅ All required credentials are valid!")
        print("   You can now run: python src/main.py")
    else:
        print("❌ Some required credentials failed validation")
        print("   Please check your .env file and try again")
        print("   See docs/CREDENTIALS_SETUP.md for help")
    print("="*60 + "\n")
    
    return 0 if required_passed else 1

if __name__ == '__main__':
    sys.exit(main())
