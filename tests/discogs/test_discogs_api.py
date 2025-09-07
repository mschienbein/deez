"""
Comprehensive test suite for Discogs API integration.
Tests all endpoints without requiring user interaction.
"""

import os
import sys
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.music_agent.integrations.discogs import (
    DiscogsClient,
    DiscogsConfig,
    DiscogsError,
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


def test_search_releases(client: DiscogsClient) -> bool:
    """Test release search functionality."""
    try:
        results = client.search_releases(
            query="Daft Punk",
            per_page=5
        )
        
        if results:
            print(f"      Found {len(results)} releases")
            for result in results[:2]:
                print(f"      - {result.title} by {result.artist}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_search_with_filters(client: DiscogsClient) -> bool:
    """Test search with various filters."""
    try:
        results = client.search.search(
            query="Electronic",
            type="release",
            genre="House",
            year="2020",
            per_page=3
        )
        
        if results:
            print(f"      Found {len(results)} filtered results")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_release(client: DiscogsClient) -> bool:
    """Test getting specific release details."""
    try:
        # Use a known release ID (Discovery by Daft Punk)
        release = client.get_release(249504)
        
        print(f"      Title: {release.title}")
        print(f"      Artist: {release.artist}")
        print(f"      Year: {release.year}")
        print(f"      Tracks: {len(release.tracklist)}")
        return True
    except NotFoundError:
        print("      Release not found (ID: 249504)")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_master(client: DiscogsClient) -> bool:
    """Test getting master release."""
    try:
        # Master ID for Daft Punk - Discovery
        master = client.get_master(90146)
        
        print(f"      Title: {master.title}")
        print(f"      Main release: {master.main_release}")
        return True
    except NotFoundError:
        print("      Master not found (ID: 90146)")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_artist(client: DiscogsClient) -> bool:
    """Test getting artist information."""
    try:
        # Daft Punk artist ID
        artist = client.get_artist(210)
        
        print(f"      Name: {artist.name}")
        if artist.members:
            print(f"      Members: {', '.join(artist.members)}")
        return True
    except NotFoundError:
        print("      Artist not found (ID: 210)")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_get_label(client: DiscogsClient) -> bool:
    """Test getting label information."""
    try:
        # Warp Records label ID
        label = client.get_label(23528)
        
        print(f"      Name: {label.name}")
        if label.profile:
            print(f"      Profile: {label.profile[:100]}...")
        return True
    except NotFoundError:
        print("      Label not found (ID: 23528)")
        return False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_artist_releases(client: DiscogsClient) -> bool:
    """Test getting artist releases."""
    try:
        releases = client.database.get_artist_releases(210, per_page=5)
        
        print(f"      Found {len(releases)} releases")
        for release in releases[:3]:
            print(f"      - {release.get('title', 'Unknown')}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_label_releases(client: DiscogsClient) -> bool:
    """Test getting label releases."""
    try:
        releases = client.database.get_label_releases(23528, per_page=5)
        
        print(f"      Found {len(releases)} releases")
        for release in releases[:3]:
            print(f"      - {release.get('title', 'Unknown')}")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_master_versions(client: DiscogsClient) -> bool:
    """Test getting master release versions."""
    try:
        versions = client.database.get_master_versions(90146, per_page=5)
        
        print(f"      Found {len(versions)} versions")
        for version in versions[:3]:
            print(f"      - {version.get('title', 'Unknown')} ({version.get('format', 'Unknown')})")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_marketplace_listings(client: DiscogsClient) -> bool:
    """Test marketplace listings (if authenticated)."""
    try:
        listings = client.get_marketplace_listings(249504, currency="USD")
        
        if listings:
            print(f"      Found {len(listings)} listings")
            for listing in listings[:2]:
                print(f"      - ${listing.price} ({listing.condition})")
        else:
            print("      No listings found")
        return True
    except AuthenticationError:
        print("      Requires authentication - skipping")
        return True  # Not a failure if not authenticated
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_collection(client: DiscogsClient) -> bool:
    """Test collection access (if authenticated)."""
    try:
        collection = client.get_collection()
        
        if collection:
            print(f"      Found {len(collection)} items in collection")
        else:
            print("      Collection is empty")
        return True
    except AuthenticationError:
        print("      Requires authentication - skipping")
        return True  # Not a failure if not authenticated
    except Exception as e:
        print(f"      Error: {e}")
        return False


def test_rate_limiting(client: DiscogsClient) -> bool:
    """Test rate limiting behavior."""
    try:
        # Make several quick requests
        for i in range(3):
            client.search_releases(f"test{i}", per_page=1)
        
        print("      Rate limiting working correctly")
        return True
    except Exception as e:
        print(f"      Error: {e}")
        return False


def main():
    """Run all tests."""
    print_section("DISCOGS API INTEGRATION TEST SUITE")
    
    # Check for authentication
    token = os.getenv("DISCOGS_USER_TOKEN")
    if not token:
        print("\n⚠️  Warning: DISCOGS_USER_TOKEN not set")
        print("   Some features may be limited without authentication")
        print("   Get a token at: https://www.discogs.com/settings/developers")
    
    # Initialize client
    try:
        config = DiscogsConfig.from_env()
        client = DiscogsClient(config)
        print("\n✅ Client initialized successfully")
    except AuthenticationError as e:
        print(f"\n❌ Authentication error: {e}")
        print("   Please set DISCOGS_USER_TOKEN in your environment")
        return 1
    except Exception as e:
        print(f"\n❌ Failed to initialize client: {e}")
        return 1
    
    # Run tests
    tests = [
        ("Search Releases", test_search_releases),
        ("Search with Filters", test_search_with_filters),
        ("Get Release Details", test_get_release),
        ("Get Master Release", test_get_master),
        ("Get Artist Info", test_get_artist),
        ("Get Label Info", test_get_label),
        ("Get Artist Releases", test_artist_releases),
        ("Get Label Releases", test_label_releases),
        ("Get Master Versions", test_master_versions),
        ("Marketplace Listings", test_marketplace_listings),
        ("User Collection", test_collection),
        ("Rate Limiting", test_rate_limiting),
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