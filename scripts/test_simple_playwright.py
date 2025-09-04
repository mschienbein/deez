#!/usr/bin/env python3
"""
Simple test to verify Playwright works with 1001 Tracklists.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.tools.tracklists_simple_tools import get_tracklist, search_tracklists

def test_simple():
    """Quick test of core functions with Playwright."""
    
    print("Testing 1001 Tracklists with Playwright\n")
    
    # Test 1: Search
    print("1. Testing search...")
    results = search_tracklists("techno", limit=3)
    if results:
        print(f"✅ Search returned {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.get('title', 'No title')[:60]}...")
    else:
        print("❌ Search returned no results")
    
    # Test 2: Get a tracklist from homepage
    print("\n2. Testing tracklist fetch...")
    # Use a known working URL format
    test_url = "https://www.1001tracklists.com/tracklist/2wg95mf9/charlotte-de-witte-tomorrowland-weekend-2-belgium-2024-07-27.html"
    
    data = get_tracklist(test_url)
    
    if data and not data.get('error'):
        print(f"✅ Fetched tracklist: {data.get('title', 'No title')[:60]}...")
        print(f"   DJ: {data.get('dj', 'Unknown')}")
        print(f"   Tracks found: {len(data.get('tracks', []))}")
        if data.get('tracks'):
            print(f"   First track: {data['tracks'][0]}")
    else:
        print(f"❌ Failed to fetch tracklist: {data.get('error', 'Unknown error')}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_simple()