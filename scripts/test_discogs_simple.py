#!/usr/bin/env python3
"""
Simple test for Discogs API integration.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.discogs import DiscogsIntegration, SearchFilters, SearchType

def test_basic():
    """Test basic Discogs functionality."""
    print("=" * 60)
    print("Testing Discogs Integration")
    print("=" * 60)
    
    # Initialize integration
    discogs = DiscogsIntegration()
    
    # Test 1: Basic search
    print("\n1. Testing basic search...")
    try:
        results = discogs.search(query="Daft Punk Discovery", page=1, per_page=5)
        if results.get('results'):
            print(f"✅ Found {len(results['results'])} results")
            for r in results['results'][:3]:
                print(f"   - {r.get('title')} ({r.get('type')})")
        else:
            print(f"❌ No results: {results.get('error')}")
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # Test 2: Get identity
    print("\n2. Testing identity...")
    try:
        identity = discogs.get_identity()
        if not identity.get('error'):
            print(f"✅ Authenticated as: {identity.get('username')}")
        else:
            print(f"❌ Identity error: {identity.get('error')}")
    except Exception as e:
        print(f"❌ Identity failed: {e}")
    
    # Test 3: Artist search
    print("\n3. Testing artist search...")
    try:
        filters = SearchFilters(query="Aphex Twin", type=SearchType.ARTIST)
        results = discogs.search(filters=filters, page=1, per_page=3)
        if results.get('results'):
            print(f"✅ Found {len(results['results'])} artists")
            # Get details for first artist
            if results['results']:
                artist_id = results['results'][0]['id']
                artist = discogs.get_artist(artist_id)
                if not artist.get('error'):
                    print(f"   Artist: {artist.get('name')}")
                    print(f"   Real name: {artist.get('real_name', 'N/A')}")
        else:
            print(f"❌ No artists found")
    except Exception as e:
        print(f"❌ Artist search failed: {e}")
    
    # Test 4: Release details
    print("\n4. Testing release details...")
    try:
        # Search for a specific release
        results = discogs.search(query="Dark Side of the Moon Pink Floyd", page=1, per_page=1)
        if results.get('results'):
            release_id = results['results'][0]['id']
            print(f"   Getting details for release ID: {release_id}")
            release = discogs.get_release(release_id)
            if not release.get('error'):
                print(f"✅ Release: {release.get('title')}")
                print(f"   Artists: {', '.join([a['name'] for a in release.get('artists', [])])}")
                print(f"   Year: {release.get('year')}")
                print(f"   Tracks: {len(release.get('tracklist', []))}")
            else:
                print(f"❌ Error: {release.get('error')}")
        else:
            print("❌ No releases found")
    except Exception as e:
        print(f"❌ Release details failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")


if __name__ == "__main__":
    test_basic()