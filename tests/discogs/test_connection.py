#!/usr/bin/env python3
"""
Quick test to verify Discogs API connection with credentials.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parents[4]
sys.path.insert(0, str(project_root))

# Load .env file
from dotenv import load_dotenv
env_path = project_root / ".env"
load_dotenv(env_path)

# Import Discogs client
from src.music_agent.integrations.discogs import DiscogsClient, DiscogsConfig

def test_connection():
    """Test basic connection to Discogs API."""
    print("Testing Discogs API Connection")
    print("=" * 50)
    
    # Check environment variables
    token = os.getenv("DISCOGS_USER_TOKEN")
    key = os.getenv("DISCOGS_CONSUMER_KEY")
    secret = os.getenv("DISCOGS_CONSUMER_SECRET")
    agent = os.getenv("DISCOGS_USER_AGENT", "MusicAgent/1.0")
    
    print(f"User Token: {'✓' if token else '✗'} {'(found)' if token else '(missing)'}")
    print(f"Consumer Key: {'✓' if key else '✗'} {'(found)' if key else '(missing)'}")
    print(f"Consumer Secret: {'✓' if secret else '✗'} {'(found)' if secret else '(missing)'}")
    print(f"User Agent: {agent}")
    print()
    
    # Initialize client
    print("Initializing client...")
    try:
        config = DiscogsConfig.from_env()
        client = DiscogsClient(config)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False
    
    print()
    
    # Test a simple search
    print("Testing API connection with search...")
    try:
        results = client.search_releases(
            query="Daft Punk",
            per_page=1
        )
        
        if results:
            print(f"✓ API connection successful!")
            print(f"  Found: {results[0].title} by {results[0].artist}")
        else:
            print("✓ API connection successful (no results)")
        return True
        
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)