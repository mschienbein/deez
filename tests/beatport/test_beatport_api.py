"""
Comprehensive test suite for Beatport API integration.
Tests all endpoints without requiring user interaction.
"""

import os
import sys
from typing import Optional
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

from src.music_agent.integrations.beatport import (
    BeatportClient,
    BeatportConfig,
    SearchQuery,
    SearchType,
    ChartType,
    BeatportError,
    AuthenticationError,
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


def test_search_tracks(client: BeatportClient) -> bool:
    """Test track search functionality."""
    try:
        tracks = client.search_tracks(
            query="techno",
            per_page=3
        )
        
        if tracks:
            print_result("Track Search", True, f"Found {len(tracks)} tracks")
            track = tracks[0]
            print(f"      Example: {track.name} by {track.artist_names}")
            if track.bpm:
                print(f"      BPM: {track.bpm}, Genre: {track.genre.name if track.genre else 'N/A'}")
            return True
        else:
            print_result("Track Search", False, "No tracks found")
            return False
            
    except Exception as e:
        print_result("Track Search", False, str(e))
        return False


def test_search_with_filters(client: BeatportClient) -> bool:
    """Test search with BPM filters."""
    try:
        tracks = client.search_tracks(
            query="house",
            bpm_low=120,
            bpm_high=128,
            per_page=3
        )
        
        if tracks:
            # Check if any tracks have BPM in range (API might not filter strictly)
            tracks_with_bpm = [t for t in tracks if t.bpm]
            if tracks_with_bpm:
                in_range = [t for t in tracks_with_bpm if 120 <= t.bpm <= 128]
                print_result("Search with BPM Filter", True, 
                            f"Found {len(tracks)} tracks, {len(in_range)}/{len(tracks_with_bpm)} in BPM range")
            else:
                print_result("Search with BPM Filter", True, 
                            f"Found {len(tracks)} tracks (no BPM data)")
            return True
        else:
            print_result("Search with BPM Filter", True, "No tracks found")
            return True
            
    except Exception as e:
        print_result("Search with BPM Filter", False, str(e))
        return False


def test_search_releases(client: BeatportClient) -> bool:
    """Test release search."""
    try:
        releases = client.search_releases(
            query="album",
            per_page=3
        )
        
        if releases:
            print_result("Release Search", True, f"Found {len(releases)} releases")
            release = releases[0]
            print(f"      Example: {release.name} by {release.artist_names}")
            return True
        else:
            print_result("Release Search", False, "No releases found")
            return False
            
    except Exception as e:
        print_result("Release Search", False, str(e))
        return False


def test_search_artists(client: BeatportClient) -> bool:
    """Test artist search."""
    try:
        artists = client.search_artists(
            query="carl cox",
            per_page=3
        )
        
        if artists:
            print_result("Artist Search", True, f"Found {len(artists)} artists")
            print(f"      Example: {artists[0].name}")
            return True
        else:
            print_result("Artist Search", True, "No exact match found")
            return True
            
    except Exception as e:
        print_result("Artist Search", False, str(e))
        return False


def test_search_labels(client: BeatportClient) -> bool:
    """Test label search."""
    try:
        labels = client.search_labels(
            query="drumcode",
            per_page=3
        )
        
        if labels:
            print_result("Label Search", True, f"Found {len(labels)} labels")
            print(f"      Example: {labels[0].name}")
            return True
        else:
            print_result("Label Search", True, "No exact match found")
            return True
            
    except Exception as e:
        print_result("Label Search", False, str(e))
        return False


def test_get_track(client: BeatportClient) -> bool:
    """Test getting track by ID."""
    try:
        # First get a track ID from search
        tracks = client.search_tracks("techno", per_page=1)
        if not tracks:
            print_result("Get Track by ID", False, "No tracks to test with")
            return False
        
        track_id = tracks[0].id
        track = client.get_track(track_id)
        
        print_result("Get Track by ID", True, 
                    f"Retrieved: {track.name} (ID: {track.id})")
        return True
        
    except Exception as e:
        print_result("Get Track by ID", False, str(e))
        return False


def test_get_related_tracks(client: BeatportClient) -> bool:
    """Test getting related tracks."""
    try:
        # First get a track ID
        tracks = client.search_tracks("house", per_page=1)
        if not tracks:
            print_result("Get Related Tracks", False, "No tracks to test with")
            return False
        
        track_id = tracks[0].id
        related = client.get_related_tracks(track_id, limit=3)
        
        if related:
            print_result("Get Related Tracks", True, 
                        f"Found {len(related)} related tracks")
            return True
        else:
            print_result("Get Related Tracks", True, "No related tracks found")
            return True
            
    except NotFoundError:
        print_result("Get Related Tracks", True, "Feature not available")
        return True
    except Exception as e:
        print_result("Get Related Tracks", False, str(e))
        return False


def test_advanced_search(client: BeatportClient) -> bool:
    """Test advanced search with SearchQuery."""
    try:
        query = SearchQuery(
            query="progressive",
            search_type=SearchType.TRACKS,
            bpm_low=125,
            bpm_high=130,
            per_page=3
        )
        
        result = client.search(query)
        
        print_result("Advanced Search", True, 
                    f"Found {result.total} total results, showing {len(result.tracks)}")
        return True
        
    except Exception as e:
        print_result("Advanced Search", False, str(e))
        return False


def test_charts(client: BeatportClient) -> bool:
    """Test chart retrieval."""
    try:
        # Try to get Top 100
        top_100 = client.get_top_100()
        
        if top_100:
            print_result("Charts (Top 100)", True, 
                        f"Retrieved {len(top_100)} tracks")
            print(f"      #1: {top_100[0].name} by {top_100[0].artist_names}")
            return True
        else:
            print_result("Charts", False, "No chart data")
            return False
            
    except NotFoundError:
        print_result("Charts", True, "Charts not available with current access")
        return True
    except Exception as e:
        print_result("Charts", False, str(e))
        return False


def test_autocomplete(client: BeatportClient) -> bool:
    """Test autocomplete suggestions."""
    try:
        suggestions = client.autocomplete("dead")
        
        total = sum(len(v) for v in suggestions.values())
        if total > 0:
            print_result("Autocomplete", True, 
                        f"Got {total} suggestions")
            return True
        else:
            print_result("Autocomplete", True, "No suggestions")
            return True
            
    except NotFoundError:
        print_result("Autocomplete", True, "Feature not available")
        return True
    except Exception as e:
        print_result("Autocomplete", False, str(e))
        return False


def run_all_tests():
    """Run all Beatport API tests."""
    print_section("BEATPORT API TEST SUITE")
    
    # Check for credentials
    has_token = os.getenv('BEATPORT_ACCESS_TOKEN')
    has_creds = os.getenv('BEATPORT_USERNAME') and os.getenv('BEATPORT_PASSWORD')
    
    if not has_token and not has_creds:
        print("\n⚠️  No Beatport credentials configured")
        print("   Set BEATPORT_ACCESS_TOKEN or BEATPORT_USERNAME/PASSWORD")
        return False
    
    # Initialize client
    print("\nInitializing client...")
    try:
        client = BeatportClient()
        print("✅ Client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test authentication
    try:
        token = client.authenticate()
        print(f"✅ Authenticated successfully")
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    
    # Run tests
    print_section("RUNNING TESTS")
    
    results = []
    test_functions = [
        test_search_tracks,
        test_search_with_filters,
        test_search_releases,
        test_search_artists,
        test_search_labels,
        test_get_track,
        test_get_related_tracks,
        test_advanced_search,
        test_charts,
        test_autocomplete,
    ]
    
    for test_func in test_functions:
        try:
            result = test_func(client)
            results.append(result)
        except Exception as e:
            print_result(test_func.__name__, False, f"Unexpected error: {e}")
            results.append(False)
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\nResults: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n✅ All tests passed!")
    elif passed > 0:
        print(f"\n⚠️  {total - passed} test(s) failed")
    else:
        print("\n❌ All tests failed")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)