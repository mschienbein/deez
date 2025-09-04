#!/usr/bin/env python3
"""
Test script for 1001 Tracklists integration.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.tracklists_simple import OneThousandOneTracklists
from src.music_agent.tools.tracklists_simple_tools import (
    get_tracklist,
    extract_track_list,
    get_tracklist_stats,
    export_as_playlist
)


def test_tracklist_extraction():
    """Test extracting a tracklist."""
    print("=" * 60)
    print("1001 Tracklists Integration Test")
    print("=" * 60)
    
    # Test URL - you'll need to provide a real one
    test_urls = [
        "https://www.1001tracklists.com/tracklist/1k9zgxvt/carl-cox-music-is-revolution-closing-party-space-ibiza-2016-09-20.html",
        "https://www.1001tracklists.com/tracklist/2nkm8pk9/amelie-lens-exhale-teletech-festival-liege-2019-07-13.html"
    ]
    
    print("\nNote: This test requires real 1001 Tracklists URLs.")
    print("The scraper will return structured data that the agent can process.\n")
    
    # Test with a sample URL (this would need a real URL)
    url = test_urls[0]
    print(f"Testing with URL: {url}\n")
    
    try:
        # Get raw tracklist data
        print("1. Fetching tracklist...")
        data = get_tracklist(url)
        
        if 'error' in data:
            print(f"❌ Error: {data['error']}")
            print("\nTrying with mock data instead...")
            data = create_mock_data()
        else:
            print("✅ Tracklist fetched successfully")
        
        # Display basic info
        print("\n2. Basic Information:")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   DJ: {data.get('dj', 'N/A')}")
        print(f"   Event: {data.get('event', 'N/A')}")
        print(f"   Date: {data.get('date', 'N/A')}")
        print(f"   Genres: {', '.join(data.get('genres', []))}")
        
        # Get statistics
        print("\n3. Statistics:")
        stats = get_tracklist_stats(data)
        print(f"   Total tracks: {stats['total_tracks']}")
        print(f"   Unknown tracks (IDs): {stats['id_tracks']}")
        print(f"   Has recording: {stats['has_recording']}")
        print(f"   Views: {stats.get('views', 'N/A')}")
        
        # Extract clean track list
        print("\n4. Track List (first 10):")
        tracks = extract_track_list(data)
        for i, track in enumerate(tracks[:10], 1):
            print(f"   {i:2}. {track}")
        
        if len(tracks) > 10:
            print(f"   ... and {len(tracks) - 10} more tracks")
        
        # Export as playlist
        print("\n5. Playlist Export (first 500 chars):")
        playlist = export_as_playlist(data)
        print(playlist[:500])
        if len(playlist) > 500:
            print("   ...")
        
        # Recording links
        print("\n6. Recording Links:")
        links = data.get('recording_links', {})
        if links:
            for platform, url in links.items():
                print(f"   {platform}: {url}")
        else:
            print("   No recording links found")
        
        print("\n✅ Test completed successfully!")
        
        # Save data for inspection
        output_file = Path("tracklist_test_output.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n📄 Full data saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def create_mock_data():
    """Create mock data for testing when real URL fails."""
    return {
        'url': 'mock://example',
        'title': 'Carl Cox @ Space Ibiza Closing',
        'dj': 'Carl Cox',
        'event': 'Music Is Revolution Closing Party',
        'date': '2016-09-20',
        'genres': ['Techno', 'Tech House'],
        'tracks': [
            {
                'position': 1,
                'cue': '00:00',
                'artist': 'Carl Cox',
                'title': 'Space Calling',
                'remix': None,
                'label': 'Intec',
                'mix_type': None,
                'is_id': False
            },
            {
                'position': 2,
                'cue': '05:30',
                'artist': 'Adam Beyer',
                'title': 'Teach Me',
                'remix': 'Len Faki Remix',
                'label': 'Drumcode',
                'mix_type': 'w/',
                'is_id': False
            },
            {
                'position': 3,
                'cue': '10:00',
                'artist': 'ID',
                'title': 'ID',
                'remix': None,
                'label': None,
                'mix_type': None,
                'is_id': True
            }
        ],
        'recording_links': {
            'soundcloud': 'https://soundcloud.com/example'
        },
        'stats': {
            'views': 50000,
            'favorites': 1200
        }
    }


def test_llm_service():
    """Test the LLM service."""
    print("\n" + "=" * 60)
    print("Testing LLM Service")
    print("=" * 60)
    
    try:
        from src.music_agent.services.llm_service import get_llm_service
        
        service = get_llm_service()
        print("✅ LLM Service initialized")
        print(f"   Default model: {service.default_model.value}")
        print(f"   Token usage: {service.get_token_usage()}")
        
    except Exception as e:
        print(f"⚠️ LLM Service not available: {e}")
        print("   Make sure OPENAI_API_KEY is set in .env")


if __name__ == "__main__":
    # Test tracklist extraction
    test_tracklist_extraction()
    
    # Test LLM service
    test_llm_service()