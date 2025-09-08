#!/usr/bin/env python3
"""
Test Soulseek/slskd connection.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

# Load .env file
env_path = project_root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

# Import Soulseek components
from src.music_agent.integrations.soulseek import (
    SoulseekClient,
    SoulseekConfig,
)


async def test_connection_async():
    """Test basic connection to slskd server."""
    print("\n" + "=" * 50)
    print(" SOULSEEK/SLSKD CONNECTION TEST")
    print("=" * 50 + "\n")
    
    # Check configuration
    config = SoulseekConfig.from_env()
    
    print("📋 Configuration Check:")
    print(f"   Host: {config.slskd.host}")
    print(f"   Port: {config.slskd.port}")
    print(f"   API Key: {'✅ Set' if config.slskd.api_key else '❌ Not set'}")
    print(f"   Username: {config.slskd.username or 'Not set'}")
    print(f"   No Auth: {config.slskd.no_auth}")
    print()
    
    # Initialize client
    print("🔄 Initializing client...")
    client = SoulseekClient(config)
    
    try:
        # Connect to slskd
        await client.connect()
        print("✅ Connected to slskd server")
        
        # Test search
        print("\n🔍 Testing search functionality...")
        results = await client.search(
            query="electronic",
            max_results=1,
            timeout=5
        )
        
        if results:
            result = results[0]
            print(f"✅ Search successful!")
            print(f"   Found: {result.file.name}")
            print(f"   From: {result.username}")
            print(f"   Size: {result.file.size_mb:.2f} MB")
            if result.file.bitrate:
                print(f"   Bitrate: {result.file.bitrate} kbps")
        else:
            print("⚠️  Search returned no results")
        
        print("\n✨ Connection test successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure slskd_api is installed: pip install slskd-api")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if slskd is running: docker ps | grep slskd")
        print("   2. Check slskd logs: docker logs slskd")
        print("   3. Verify API key in .env file")
        print("   4. Check if SLSKD_NO_AUTH=true in slskd config")
        return False
        
    finally:
        await client.close()


def test_connection():
    """Test connection synchronously for test runner."""
    return asyncio.run(test_connection_async())


async def main():
    """Run connection test."""
    success = await test_connection_async()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)