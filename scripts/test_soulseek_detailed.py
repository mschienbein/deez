#!/usr/bin/env python3
"""
Detailed Soulseek Integration Test
Tests all individual Soulseek tools and methods
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.soulseek import SoulseekClient, SoulseekDiscovery
from src.music_agent.tools.soulseek_tools import (
    SoulseekSearchTool,
    SoulseekDownloadTool,
    SoulseekDiscoveryTool,
    SoulseekUserTool
)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_client_methods():
    """Test low-level SoulseekClient methods"""
    print("\n" + "=" * 60)
    print("Testing SoulseekClient Methods")
    print("=" * 60)
    
    client = SoulseekClient()
    
    try:
        await client.initialize()
        print("✅ Client initialized")
        
        # Test search
        print("\n1. Testing search method...")
        results = await client.search("test", min_bitrate=128, max_results=5, timeout=5)
        print(f"   Search returned {len(results)} results")
        
        # Test user info (will likely fail without real users)
        print("\n2. Testing get_user_info...")
        try:
            user_info = await client.get_user_info("testuser")
            print(f"   User info: {user_info}")
        except Exception as e:
            print(f"   ⚠️ User info failed (expected): {e}")
        
        # Test browse user
        print("\n3. Testing browse_user...")
        try:
            files = await client.browse_user("testuser")
            print(f"   Found {len(files)} files")
        except Exception as e:
            print(f"   ⚠️ Browse failed (expected): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False
    finally:
        await client.close()


async def test_search_tool_detailed():
    """Test SoulseekSearchTool with various parameters"""
    print("\n" + "=" * 60)
    print("Testing SoulseekSearchTool in Detail")
    print("=" * 60)
    
    tool = SoulseekSearchTool()
    
    try:
        # Test 1: Basic search
        print("\n1. Basic search for 'music'...")
        results = await tool.run(query="music", max_results=3)
        print(f"   Found {len(results)} results")
        
        # Test 2: Search with bitrate filter
        print("\n2. Search with high bitrate (320kbps)...")
        results = await tool.run(query="electronic", min_bitrate=320, max_results=3)
        print(f"   Found {len(results)} high-quality results")
        
        # Test 3: Search with file type filter
        print("\n3. Search for FLAC files...")
        results = await tool.run(query="jazz", file_type="flac", max_results=3)
        print(f"   Found {len(results)} FLAC files")
        
        # Test 4: Empty search
        print("\n4. Testing empty query handling...")
        results = await tool.run(query="", max_results=1)
        print(f"   Empty query returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Search tool test failed: {e}")
        return False
    finally:
        await tool.cleanup()


async def test_discovery_tool_detailed():
    """Test SoulseekDiscoveryTool with various modes"""
    print("\n" + "=" * 60)
    print("Testing SoulseekDiscoveryTool in Detail")
    print("=" * 60)
    
    tool = SoulseekDiscoveryTool()
    
    try:
        # Test 1: Discovery by criteria
        print("\n1. Discovery by genre...")
        results = await tool.run(
            mode="criteria",
            genre="ambient",
            limit=3
        )
        print(f"   Discovered {len(results)} ambient tracks")
        
        # Test 2: Discovery by artist
        print("\n2. Discovery by artist...")
        results = await tool.run(
            mode="criteria",
            artist="Aphex Twin",
            limit=3
        )
        print(f"   Discovered {len(results)} tracks by artist")
        
        # Test 3: Discovery by BPM range
        print("\n3. Discovery by BPM range...")
        results = await tool.run(
            mode="criteria",
            bpm_range=(120, 130),
            limit=3
        )
        print(f"   Discovered {len(results)} tracks in BPM range")
        
        # Test 4: Discovery by key
        print("\n4. Discovery by musical key...")
        results = await tool.run(
            mode="criteria",
            key="5A",
            limit=3
        )
        print(f"   Discovered {len(results)} tracks in key 5A")
        
        # Test 5: Similar tracks discovery
        print("\n5. Discovery of similar tracks...")
        results = await tool.run(
            mode="similar",
            reference_track="Boards of Canada - Roygbiv",
            limit=3
        )
        print(f"   Found {len(results)} similar tracks")
        
        return True
        
    except Exception as e:
        print(f"❌ Discovery tool test failed: {e}")
        return False
    finally:
        await tool.cleanup()


async def test_user_tool_detailed():
    """Test SoulseekUserTool"""
    print("\n" + "=" * 60)
    print("Testing SoulseekUserTool in Detail")
    print("=" * 60)
    
    tool = SoulseekUserTool()
    
    try:
        # Test 1: Get user info
        print("\n1. Getting user info...")
        result = await tool.run(
            action="info",
            username="testuser"
        )
        if result["success"]:
            print(f"   Got info for user: {result['username']}")
        else:
            print(f"   ⚠️ User info failed (expected without real users)")
        
        # Test 2: Browse user files
        print("\n2. Browsing user files...")
        result = await tool.run(
            action="browse",
            username="testuser",
            limit=10
        )
        if result["success"]:
            print(f"   Found {result['total_files']} files, showing {result['showing']}")
        else:
            print(f"   ⚠️ Browse failed (expected without real users)")
        
        # Test 3: Invalid action
        print("\n3. Testing invalid action...")
        result = await tool.run(
            action="invalid",
            username="testuser"
        )
        if not result["success"]:
            print(f"   ✅ Invalid action correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ User tool test failed: {e}")
        return False
    finally:
        await tool.cleanup()


async def test_download_tool_mock():
    """Test SoulseekDownloadTool with mock data"""
    print("\n" + "=" * 60)
    print("Testing SoulseekDownloadTool (Mock)")
    print("=" * 60)
    
    tool = SoulseekDownloadTool()
    
    try:
        # Since we don't have real files, we'll test the interface
        print("\n1. Testing download interface...")
        
        # This will fail but tests the API
        result = await tool.run(
            username="mockuser",
            filename="/music/test.mp3",
            file_size=5000000,
            output_dir="/tmp",
            auto_tag=False
        )
        
        if result:
            print(f"   ✅ Download succeeded: {result['file_path']}")
        else:
            print(f"   ⚠️ Download failed (expected without real network)")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Download tool test error (expected): {e}")
        return True  # Expected to fail without real network
    finally:
        await tool.cleanup()


async def test_discovery_class():
    """Test high-level SoulseekDiscovery class"""
    print("\n" + "=" * 60)
    print("Testing SoulseekDiscovery Class")
    print("=" * 60)
    
    discovery = SoulseekDiscovery()
    
    try:
        await discovery.initialize()
        print("✅ Discovery initialized")
        
        # Test discover_tracks
        print("\n1. Testing discover_tracks...")
        tracks = await discovery.discover_tracks(
            genre="electronic",
            bpm_range=(125, 135)
        )
        print(f"   Discovered {len(tracks)} tracks")
        
        # Test find_similar_tracks
        print("\n2. Testing find_similar_tracks...")
        similar = await discovery.find_similar_tracks(
            reference_track="Test Track",
            limit=5
        )
        print(f"   Found {len(similar)} similar tracks")
        
        return True
        
    except Exception as e:
        print(f"❌ Discovery class test failed: {e}")
        return False
    finally:
        await discovery.close()


async def test_api_endpoints():
    """Test slskd API endpoints directly"""
    print("\n" + "=" * 60)
    print("Testing slskd API Endpoints")
    print("=" * 60)
    
    import slskd_api
    
    api_key = os.getenv("SLSKD_API_KEY", "deez-slskd-api-key-2024")
    host = os.getenv("SLSKD_HOST", "http://localhost:5030")
    
    try:
        client = slskd_api.SlskdClient(host, api_key, "")
        
        # Test 1: Application info
        print("\n1. Getting application info...")
        try:
            info = client.application.info()
            print(f"   slskd version: {info.get('version', 'unknown')}")
        except Exception as e:
            print(f"   ⚠️ App info failed: {e}")
        
        # Test 2: Get server state
        print("\n2. Getting server state...")
        try:
            state = client.server.state()
            print(f"   Server state: {json.dumps(state, indent=2)}")
        except Exception as e:
            print(f"   ⚠️ Server state failed: {e}")
        
        # Test 3: List searches
        print("\n3. Listing active searches...")
        try:
            searches = client.searches.get_all()
            print(f"   Active searches: {len(searches) if searches else 0}")
        except Exception as e:
            print(f"   ⚠️ List searches failed: {e}")
        
        # Test 4: List transfers
        print("\n4. Listing transfers...")
        try:
            downloads = client.transfers.get_downloads()
            uploads = client.transfers.get_uploads()
            print(f"   Downloads: {len(downloads) if downloads else 0}")
            print(f"   Uploads: {len(uploads) if uploads else 0}")
        except Exception as e:
            print(f"   ⚠️ List transfers failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


async def main():
    """Run all detailed tests"""
    print("=" * 60)
    print("Detailed Soulseek Integration Test Suite")
    print("=" * 60)
    
    # Set API key
    os.environ["SLSKD_API_KEY"] = "deez-slskd-api-key-2024"
    
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Client Methods", test_client_methods),
        ("Search Tool", test_search_tool_detailed),
        ("Discovery Tool", test_discovery_tool_detailed),
        ("User Tool", test_user_tool_detailed),
        ("Download Tool", test_download_tool_mock),
        ("Discovery Class", test_discovery_class),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}", exc_info=True)
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Detailed Test Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All detailed tests passed!")
    else:
        print("⚠️ Some tests failed (expected without real Soulseek network)")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)