#!/usr/bin/env python3
"""
Test Soulseek/slskd Integration
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.soulseek import SoulseekDiscovery
from src.music_agent.tools.soulseek_tools import (
    SoulseekSearchTool,
    SoulseekDownloadTool,
    SoulseekDiscoveryTool
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_connection():
    """Test basic connection to slskd"""
    print("\n" + "=" * 60)
    print("Testing slskd Connection")
    print("=" * 60)
    
    discovery = SoulseekDiscovery()
    
    try:
        await discovery.initialize()
        print("✅ Successfully connected to slskd")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to slskd: {e}")
        print("\nMake sure:")
        print("1. slskd container is running: docker-compose up -d slskd")
        print("2. API is accessible at: http://localhost:5030")
        print("3. API key is configured (if required)")
        return False
    finally:
        await discovery.close()


async def test_search():
    """Test search functionality"""
    print("\n" + "=" * 60)
    print("Testing Search Functionality")
    print("=" * 60)
    
    search_tool = SoulseekSearchTool()
    
    try:
        # Test a simple search
        query = "electronic music"
        print(f"\nSearching for: {query}")
        
        results = await search_tool.run(
            query=query,
            min_bitrate=128,
            max_results=5
        )
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. {result['filename']}")
                print(f"     From: {result['username']}")
                print(f"     Size: {result.get('size_mb', 'N/A')} MB")
                print(f"     Bitrate: {result.get('bitrate', 'N/A')} kbps")
            return True
        else:
            print("⚠️ No results found (this might be normal if no users are sharing)")
            return True
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False
    finally:
        await search_tool.cleanup()


async def test_discovery():
    """Test discovery functionality"""
    print("\n" + "=" * 60)
    print("Testing Discovery Functionality")
    print("=" * 60)
    
    discovery_tool = SoulseekDiscoveryTool()
    
    try:
        # Test discovery by genre
        print("\nDiscovering techno tracks...")
        
        results = await discovery_tool.run(
            mode="criteria",
            genre="techno",
            bpm_range=(125, 135),
            limit=5
        )
        
        if results:
            print(f"✅ Discovered {len(results)} tracks:")
            for i, track in enumerate(results, 1):
                print(f"  {i}. {track['filename']}")
        else:
            print("⚠️ No tracks discovered (this might be normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return False
    finally:
        await discovery_tool.cleanup()


async def test_download():
    """Test download functionality (optional)"""
    print("\n" + "=" * 60)
    print("Testing Download Functionality")
    print("=" * 60)
    
    # Skip download test by default to avoid unwanted downloads
    skip_download = os.getenv("SKIP_DOWNLOAD_TEST", "true").lower() == "true"
    
    if skip_download:
        print("⏭️ Skipping download test (set SKIP_DOWNLOAD_TEST=false to enable)")
        return True
    
    search_tool = SoulseekSearchTool()
    download_tool = SoulseekDownloadTool()
    
    try:
        # First, search for a small file
        results = await search_tool.run(
            query="test",
            max_results=1
        )
        
        if not results:
            print("⚠️ No files found to download")
            return True
        
        # Download the first result
        first_result = results[0]
        print(f"\nDownloading: {first_result['filename']}")
        print(f"From user: {first_result['username']}")
        
        download_result = await download_tool.run(
            username=first_result["username"],
            filename=first_result["filename"],
            file_size=first_result.get("size")
        )
        
        if download_result and download_result.get("success"):
            print(f"✅ Successfully downloaded to: {download_result['file_path']}")
            return True
        else:
            print("❌ Download failed")
            return False
            
    except Exception as e:
        print(f"❌ Download test failed: {e}")
        return False
    finally:
        await search_tool.cleanup()
        await download_tool.cleanup()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Soulseek/slskd Integration Test Suite")
    print("=" * 60)
    
    # Check environment
    print("\nEnvironment Check:")
    print(f"SLSKD_HOST: {os.getenv('SLSKD_HOST', 'http://localhost:5030')}")
    print(f"SLSKD_API_KEY: {'Set' if os.getenv('SLSKD_API_KEY') else 'Not set'}")
    
    # Run tests
    tests = [
        ("Connection", test_connection),
        ("Search", test_search),
        ("Discovery", test_discovery),
        ("Download", test_download)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)