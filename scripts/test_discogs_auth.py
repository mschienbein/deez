#!/usr/bin/env python3
"""
Test Discogs authentication and basic API access.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.utils.config import get_config
import discogs_client

def test_auth():
    """Test Discogs authentication."""
    config = get_config()
    
    print("=" * 60)
    print("Discogs Configuration Test")
    print("=" * 60)
    
    print(f"Consumer Key: {config.discogs.consumer_key}")
    print(f"Consumer Secret: {config.discogs.consumer_secret[:10]}..." if config.discogs.consumer_secret else "Consumer Secret: None")
    print(f"User Agent: {config.discogs.user_agent}")
    print(f"User Token: {config.discogs.user_token[:10]}..." if config.discogs.user_token else "User Token: None")
    
    print("\n" + "=" * 60)
    print("Testing API Access")
    print("=" * 60)
    
    # Try with user token
    print("\n1. Testing with User Token...")
    if config.discogs.user_token:
        try:
            client = discogs_client.Client(
                config.discogs.user_agent,
                user_token=config.discogs.user_token
            )
            
            # Try a simple search
            results = client.search("Daft Punk", type="artist")
            print(f"✅ Search successful! Found {len(results)} results")
            
            if results:
                print(f"   First result: {results[0].name}")
                
        except Exception as e:
            print(f"❌ Error with user token: {e}")
    else:
        print("❌ No user token configured")
    
    # Try with consumer key/secret
    print("\n2. Testing with Consumer Key/Secret...")
    try:
        client = discogs_client.Client(
            config.discogs.user_agent,
            consumer_key=config.discogs.consumer_key,
            consumer_secret=config.discogs.consumer_secret
        )
        
        # Try a simple search
        results = client.search("Daft Punk", type="artist")
        print(f"✅ Search successful! Found {len(results)} results")
        
        if results:
            print(f"   First result: {results[0].name}")
            
    except Exception as e:
        print(f"❌ Error with consumer key/secret: {e}")
    
    # Try without auth
    print("\n3. Testing without authentication...")
    try:
        client = discogs_client.Client(config.discogs.user_agent)
        
        # Try a simple search
        results = client.search("Daft Punk", type="artist")
        print(f"✅ Search successful! Found {len(results)} results")
        
        if results:
            print(f"   First result: {results[0].name}")
            
    except Exception as e:
        print(f"❌ Error without auth: {e}")
    
    print("\n" + "=" * 60)
    print("Note: Discogs API requires authentication for most operations.")
    print("You can:")
    print("1. Use the provided consumer key/secret (limited access)")
    print("2. Get a personal access token from: https://www.discogs.com/settings/developers")
    print("   Then add it to .env as: DISCOGS_USER_TOKEN=your_token_here")
    print("=" * 60)


if __name__ == "__main__":
    test_auth()