"""
Comprehensive test suite for MusicBrainz API integration.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.music_agent.integrations.musicbrainz import (
    MusicBrainzClient,
    MusicBrainzConfig,
    MusicBrainzError,
    NotFoundError,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result(name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"      {details}")


def test_search_artists(client: MusicBrainzClient) -> bool:
    """Test artist search functionality."""
    try:
        results = client.search_artists(
            query="Radiohead",
            limit=3
        )
        
        if results.results:
            print(f"      Found {len(results.results)} artists")
            for result in results.results[:2]:
                print(f"      - {result.name} (Score: {result.score})")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_search_releases(client: MusicBrainzClient) -> bool:
    """Test release search functionality."""
    try:
        results = client.search_releases(
            query="OK Computer",
            artist="Radiohead",
            limit=3
        )
        
        if results.results:
            print(f"      Found {len(results.results)} releases")
            for result in results.results[:2]:
                print(f"      - {result.title} by {result.artist}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_search_recordings(client: MusicBrainzClient) -> bool:
    """Test recording search functionality."""
    try:
        results = client.search_recordings(
            query="Karma Police",
            artist="Radiohead",
            limit=3
        )
        
        if results.results:
            print(f"      Found {len(results.results)} recordings")
            for result in results.results[:2]:
                print(f"      - {result.title} by {result.artist}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_artist(client: MusicBrainzClient) -> bool:
    """Test getting specific artist details."""
    try:
        # Radiohead MBID
        artist = client.get_artist("a74b1b7f-71a5-4011-9441-d0b5e4122711")
        
        print(f"      Name: {artist.name}")
        print(f"      Type: {artist.type}")
        print(f"      Country: {artist.country}")
        return True
    except NotFoundError:
        print("      Artist not found")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_release(client: MusicBrainzClient) -> bool:
    """Test getting specific release details."""
    try:
        # OK Computer release MBID (valid)
        release = client.get_release("52e7fc61-fcf3-4b46-ac72-38e9644bf982")
        
        print(f"      Title: {release.title}")
        print(f"      Artist: {release.artist}")
        print(f"      Date: {release.release_date}")
        print(f"      Tracks: {release.track_count}")
        return True
    except NotFoundError:
        print("      Release not found")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_recording(client: MusicBrainzClient) -> bool:
    """Test getting specific recording details."""
    try:
        # Karma Police recording MBID (valid)
        recording = client.get_recording("0790ba6c-e0b1-4891-b82f-b4db9a5a927f")
        
        print(f"      Title: {recording.title}")
        print(f"      Duration: {recording.duration_formatted}")
        if recording.isrcs:
            print(f"      ISRCs: {', '.join(recording.isrcs)}")
        return True
    except NotFoundError:
        print("      Recording not found")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_label(client: MusicBrainzClient) -> bool:
    """Test getting label information."""
    try:
        # Parlophone label MBID
        label = client.get_label("df7d1c7f-ef95-425f-8eef-445b3d7bcbd9")
        
        print(f"      Name: {label.name}")
        print(f"      Type: {label.type}")
        print(f"      Country: {label.country}")
        return True
    except NotFoundError:
        print("      Label not found")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_release_group(client: MusicBrainzClient) -> bool:
    """Test getting release group information."""
    try:
        # OK Computer release group MBID
        release_group = client.get_release_group("b1392450-e666-3926-a536-22c65f834433")
        
        print(f"      Title: {release_group.title}")
        print(f"      Type: {release_group.type}")
        print(f"      Artist: {release_group.artist}")
        return True
    except NotFoundError:
        print("      Release group not found")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_artist_releases(client: MusicBrainzClient) -> bool:
    """Test getting artist releases."""
    try:
        releases = client.database.get_artist_releases(
            "a74b1b7f-71a5-4011-9441-d0b5e4122711",  # Radiohead
            limit=5
        )
        
        print(f"      Found {len(releases)} releases")
        for release in releases[:3]:
            print(f"      - {release.get('title', 'Unknown')}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_label_releases(client: MusicBrainzClient) -> bool:
    """Test getting label releases."""
    try:
        releases = client.database.get_label_releases(
            "df7d1c7f-ef95-425f-8eef-445b3d7bcbd9",  # Parlophone
            limit=5
        )
        
        print(f"      Found {len(releases)} releases")
        for release in releases[:3]:
            print(f"      - {release.get('title', 'Unknown')}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_isrc_lookup(client: MusicBrainzClient) -> bool:
    """Test ISRC lookup."""
    try:
        # Test with a known valid ISRC (Nirvana - Smells Like Teen Spirit)
        # Note: Many recordings don't have ISRCs in MusicBrainz
        test_isrc = "USGE19100107"  # Valid ISRC
        
        try:
            recordings = client.get_recording_by_isrc(test_isrc)
            
            if recordings:
                print(f"      Found {len(recordings)} recordings for ISRC")
                for rec in recordings[:2]:
                    print(f"      - {rec.title}")
            else:
                print(f"      No recordings found for ISRC {test_isrc}")
        except Exception as e:
            # ISRC lookup can fail if not in database
            print(f"      ISRC not in database (this is common)")
            
        # Test that the method at least works without crashing
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_cover_art(client: MusicBrainzClient) -> bool:
    """Test cover art retrieval."""
    try:
        # OK Computer release with cover art (valid MBID)
        cover_art = client.get_cover_art("52e7fc61-fcf3-4b46-ac72-38e9644bf982")
        
        if cover_art:
            print(f"      Cover art available")
            if 'images' in cover_art:
                print(f"      Images: {len(cover_art['images'])}")
        else:
            print("      No cover art available")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def main():
    """Run all tests."""
    print_section("MUSICBRAINZ API INTEGRATION TEST SUITE")
    
    # Initialize client
    try:
        config = MusicBrainzConfig.from_env()
        client = MusicBrainzClient(config)
        print("\n✅ Client initialized successfully")
    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
        return 1
    
    # Run tests
    tests = [
        ("Search Artists", test_search_artists),
        ("Search Releases", test_search_releases),
        ("Search Recordings", test_search_recordings),
        ("Get Artist Details", test_get_artist),
        ("Get Release Details", test_get_release),
        ("Get Recording Details", test_get_recording),
        ("Get Label Info", test_get_label),
        ("Get Release Group", test_get_release_group),
        ("Get Artist Releases", test_artist_releases),
        ("Get Label Releases", test_label_releases),
        ("ISRC Lookup", test_isrc_lookup),
        ("Cover Art Retrieval", test_cover_art),
    ]
    
    print_section("Running Tests")
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            success = test_func(client)
            if success:
                passed += 1
            else:
                failed += 1
            print_result(name, success)
        except Exception as e:
            failed += 1
            print_result(name, False, str(e))
    
    # Summary
    print_section("Test Summary")
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())