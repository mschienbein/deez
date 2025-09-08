#!/usr/bin/env python3
"""
Quick test to verify Deezer API connection.
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

# Import Deezer client
from src.music_agent.integrations.deezer import DeezerClient
from src.music_agent.integrations.deezer.config import DeezerConfig

async def test_connection_async():
    """Test basic connection to Deezer API."""
    print("Testing Deezer API Connection")
    print("=" * 50)
    
    # Check environment variables
    arl = os.getenv("DEEZER_ARL")
    
    print(f"ARL Token: {'✓' if arl else '✗'} {'(found)' if arl else '(missing - running in public mode)'}")
    print()
    
    # Initialize client
    print("Initializing client...")
    try:
        config = DeezerConfig()
        client = DeezerClient(config)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False
    
    print()
    
    # Test connection and authentication
    try:
        async with client:
            # Check authentication status
            if client.is_authenticated:
                print("✓ Authenticated with Deezer")
                user_id = client.auth_manager.user_id
                print(f"  User ID: {user_id}")
                qualities = client.auth_manager.available_qualities
                print(f"  Available qualities: {', '.join(qualities)}")
            else:
                print("ℹ Running in public API mode (no authentication)")
            
            print()
            
            # Test a simple search (works without auth)
            print("Testing API connection with search...")
            
            results = await client.search_tracks(
                query="daft punk",
                limit=1
            )
            
            if results:
                track = results[0]
                print(f"✓ API connection successful!")
                print(f"  Found: {track.title} by {track.artist_name}")
                print(f"  Duration: {track.duration_formatted}")
                print(f"  Album: {track.album_title}")
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