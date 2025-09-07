#!/usr/bin/env python3
"""
Quick test to verify MusicBrainz API connection.
"""

import os
import sys
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

# Import MusicBrainz client
from src.music_agent.integrations.musicbrainz import MusicBrainzClient, MusicBrainzConfig

def test_connection():
    """Test basic connection to MusicBrainz API."""
    print("Testing MusicBrainz API Connection")
    print("=" * 50)
    
    # Check environment variables
    user_agent = os.getenv("MUSICBRAINZ_USER_AGENT", "DeezMusicAgent/1.0")
    contact_email = os.getenv("MUSICBRAINZ_CONTACT_EMAIL")
    username = os.getenv("MUSICBRAINZ_USERNAME")
    password = os.getenv("MUSICBRAINZ_PASSWORD")
    
    print(f"User Agent: {user_agent}")
    print(f"Contact Email: {'✓' if contact_email else '✗'} {'(set)' if contact_email else '(not set - recommended)'}")
    print(f"Username: {'✓' if username else '✗'} {'(set)' if username else '(not set - optional)'}")
    print(f"Password: {'✓' if password else '✗'} {'(set)' if password else '(not set - optional)'}")
    print()
    
    # Initialize client
    print("Initializing client...")
    try:
        config = MusicBrainzConfig.from_env()
        client = MusicBrainzClient(config)
        print("✓ Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False
    
    print()
    
    # Test a simple search
    print("Testing API connection with artist search...")
    try:
        results = client.search_artists(
            query="Daft Punk",
            limit=1
        )
        
        if results.results:
            print(f"✓ API connection successful!")
            print(f"  Found: {results.results[0].name} (Score: {results.results[0].score})")
            print(f"  MBID: {results.results[0].id}")
        else:
            print("✓ API connection successful (no results)")
        return True
        
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)