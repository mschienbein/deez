#!/usr/bin/env python3
"""
Quick test to verify Mixcloud API connection.
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

# Import Mixcloud client
from src.music_agent.integrations.mixcloud import MixcloudClient
from src.music_agent.integrations.mixcloud.config import MixcloudConfig

async def test_connection_async():
    """Test basic connection to Mixcloud API."""
    print("Testing Mixcloud API Connection")
    print("=" * 50)
    
    # Check environment variables
    client_id = os.getenv("MIXCLOUD_CLIENT_ID")
    client_secret = os.getenv("MIXCLOUD_CLIENT_SECRET")
    redirect_uri = os.getenv("MIXCLOUD_REDIRECT_URI", "http://localhost:8080/callback")
    
    print(f"Client ID: {'✓' if client_id else '✗'} {'(found)' if client_id else '(missing)'}")
    print(f"Client Secret: {'✓' if client_secret else '✗'} {'(found)' if client_secret else '(missing)'}")
    print(f"Redirect URI: {redirect_uri}")
    print()
    
    # Initialize client
    print("Initializing client...")
    try:
        config = MixcloudConfig()
        client = MixcloudClient(config)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False
    
    print()
    
    # Test a simple search (doesn't require auth)
    print("Testing API connection with search...")
    try:
        async with client:
            results = await client.search_cloudcasts(
                query="electronic",
                limit=1
            )
            
            if results:
                cloudcast = results[0]
                print(f"✓ API connection successful!")
                print(f"  Found: {cloudcast.name} by {cloudcast.user.name if cloudcast.user else 'Unknown'}")
            else:
                print("✓ API connection successful (no results)")
            return True
        
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection():
    """Synchronous wrapper for the async test."""
    return asyncio.run(test_connection_async())

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)