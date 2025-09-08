#!/usr/bin/env python3
"""
Test YouTube connection and basic functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.music_agent.integrations.youtube import YouTubeClient


def test_connection():
    """Test basic YouTube connection."""
    print("Testing YouTube connection...")
    
    try:
        # Initialize client
        client = YouTubeClient.from_env()
        
        # Check authentication (optional - yt-dlp works without auth)
        print("Checking authentication...")
        try:
            is_auth = client.authenticate()
            print(f"✓ Authentication status: {is_auth}")
        except Exception as e:
            print(f"  Note: Authentication optional - {e}")
        
        # Test basic search
        print("\nTesting search...")
        results = client.search_music("Daft Punk", limit=3)
        
        if results:
            print(f"✓ Found {len(results)} results")
            for video in results[:3]:
                print(f"  - {video.title} by {video.channel_title}")
        else:
            print("✗ No results found")
            return False
        
        # Test video info
        if results:
            print("\nTesting video info...")
            video = client.get_video(results[0].id)
            print(f"✓ Got video: {video.title}")
            print(f"  Duration: {video.duration}s")
            print(f"  Views: {video.view_count:,}")
        
        print("\n✅ YouTube connection test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ YouTube connection test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)