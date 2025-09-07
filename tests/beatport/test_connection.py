"""
Quick connection test for Beatport API.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key not in os.environ:  # Don't override existing env vars
                    os.environ[key] = value

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.music_agent.integrations.beatport import BeatportClient


def test_connection():
    """Test basic Beatport API connection."""
    print("\n" + "="*60)
    print(" BEATPORT CONNECTION TEST")
    print("="*60)
    
    # Check for credentials
    has_token = os.getenv('BEATPORT_ACCESS_TOKEN')
    has_creds = os.getenv('BEATPORT_USERNAME') and os.getenv('BEATPORT_PASSWORD')
    
    print("\n📋 Credential Check:")
    print(f"   Access Token: {'✅ Set' if has_token else '❌ Not set'}")
    print(f"   Username: {'✅ Set' if os.getenv('BEATPORT_USERNAME') else '❌ Not set'}")
    print(f"   Password: {'✅ Set' if os.getenv('BEATPORT_PASSWORD') else '❌ Not set'}")
    
    if not has_token and not has_creds:
        print("\n❌ No credentials configured")
        print("   Set BEATPORT_ACCESS_TOKEN or BEATPORT_USERNAME/PASSWORD in .env")
        return False
    
    try:
        # Initialize client
        print("\n🔄 Initializing client...")
        client = BeatportClient()
        print("✅ Client initialized")
        
        # Test authentication
        print("\n🔐 Testing authentication...")
        token = client.authenticate()
        print(f"✅ Authenticated! Token: {token[:20]}...")
        
        # Test simple search
        print("\n🔍 Testing API access...")
        tracks = client.search_tracks("techno", per_page=1)
        
        if tracks:
            track = tracks[0]
            print(f"✅ API working! Found track: {track.name}")
            print(f"   Artist: {track.artist_names}")
            if track.bpm:
                print(f"   BPM: {track.bpm}")
        else:
            print("✅ API responding (no results)")
        
        print("\n✨ Connection test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify credentials in .env file")
        print("   3. Ensure tokens haven't expired")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)