#!/usr/bin/env python3
"""
Test script for Mixcloud integration.

Tests basic functionality with the provided API keys.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.mixcloud import MixcloudClient


async def test_mixcloud():
    """Test Mixcloud integration."""
    print("🎵 Testing Mixcloud Integration\n")
    print("=" * 50)
    
    # Create client
    client = MixcloudClient()
    
    try:
        # Initialize client
        await client.initialize()
        print("✅ Client initialized")
        
        # Test 1: Search for cloudcasts
        print("\n📍 Test 1: Search for techno mixes")
        print("-" * 30)
        results = await client.search_cloudcasts("techno", limit=3)
        
        for i, cloudcast in enumerate(results, 1):
            print(f"\n{i}. {cloudcast.name}")
            print(f"   By: {cloudcast.username}")
            print(f"   Duration: {cloudcast.duration_formatted}")
            print(f"   Plays: {cloudcast.play_count or 0:,}")
            print(f"   URL: {cloudcast.mixcloud_url}")
        
        # Test 2: Get a specific cloudcast
        print("\n📍 Test 2: Get specific cloudcast")
        print("-" * 30)
        
        cloudcast = None
        # Use a known cloudcast (NTS Radio usually has many shows)
        try:
            cloudcast = await client.get_cloudcast("NTSRadio", "cleo-sol-nts-10th-anniversary-19th-april-2021")
            print(f"✅ Found: {cloudcast.name}")
            print(f"   Created: {cloudcast.created_time}")
            print(f"   Tags: {', '.join([tag.name for tag in cloudcast.tags[:5]])}")
        except Exception as e:
            print(f"⚠️ Could not get specific cloudcast: {e}")
            print("   Trying alternative...")
            
            # Try with first search result
            if results:
                cloudcast = results[0]
                print(f"✅ Using: {cloudcast.name}")
        
        # Test 3: Get user info
        print("\n📍 Test 3: Get user information")
        print("-" * 30)
        
        if cloudcast and cloudcast.user:
            user = await client.get_user(cloudcast.username)
            print(f"User: {user.display_name} (@{user.username})")
            print(f"Followers: {user.follower_count or 0:,}")
            print(f"Cloudcasts: {user.cloudcast_count or 0:,}")
            if user.location:
                print(f"Location: {user.location}")
        
        # Test 4: Get popular cloudcasts
        print("\n📍 Test 4: Get popular cloudcasts")
        print("-" * 30)
        
        popular = await client.get_popular(limit=3)
        for i, cc in enumerate(popular, 1):
            print(f"{i}. {cc.name} by {cc.username}")
        
        # Test 5: Get categories
        print("\n📍 Test 5: Get categories")
        print("-" * 30)
        
        categories = await client.get_categories()
        for cat in categories[:5]:
            print(f"• {cat.name}")
        
        # Test 6: Test download (if available)
        if client.config.enable_downloads and results:
            print("\n📍 Test 6: Test download capability")
            print("-" * 30)
            
            test_cloudcast = results[0]
            print(f"Testing download for: {test_cloudcast.name}")
            
            try:
                # Just test stream extraction, not actual download
                from src.music_agent.integrations.mixcloud.download import StreamExtractor
                extractor = StreamExtractor(client._session, client.config.download)
                stream_info = await extractor.extract(test_cloudcast)
                
                if stream_info:
                    print("✅ Stream extraction successful")
                    if stream_info.get("hls_url"):
                        print("   Type: HLS stream")
                    elif stream_info.get("stream_url"):
                        print("   Type: Direct stream")
                    elif stream_info.get("preview_url"):
                        print("   Type: Preview only")
                    print(f"   Quality: {stream_info.get('quality', 'unknown')}")
                else:
                    print("⚠️ No downloadable stream found")
            except Exception as e:
                print(f"❌ Stream extraction failed: {e}")
        
        # Test 7: Authentication (optional)
        print("\n📍 Test 7: Authentication check")
        print("-" * 30)
        
        if client.is_authenticated():
            print("✅ Already authenticated")
            try:
                me = await client.get_me()
                print(f"   Logged in as: {me.username}")
            except:
                print("   But could not get user info")
        else:
            print("ℹ️ Not authenticated (OAuth2 available for user actions)")
            print("   Client ID configured:", bool(client.config.auth.client_id))
            print("   Client Secret configured:", bool(client.config.auth.client_secret))
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await client.close()


async def test_download_specific():
    """Test downloading a specific cloudcast."""
    print("\n🎵 Testing Specific Download")
    print("=" * 50)
    
    client = MixcloudClient()
    
    try:
        await client.initialize()
        
        # Search for a downloadable mix
        print("Searching for downloadable content...")
        results = await client.search_cloudcasts("deep house mix", limit=5)
        
        downloaded_count = 0
        for cloudcast in results:
            if cloudcast.is_exclusive:
                print(f"⚠️ Skipping exclusive: {cloudcast.name}")
                continue
            
            print(f"\nTrying to download: {cloudcast.name}")
            print(f"  URL: {cloudcast.mixcloud_url}")
            
            try:
                # Create downloads directory
                download_dir = Path("downloads/mixcloud_test")
                download_dir.mkdir(parents=True, exist_ok=True)
                
                # Download
                path = await client.download_cloudcast(
                    cloudcast,
                    output_dir=str(download_dir)
                )
                
                print(f"✅ Downloaded to: {path}")
                
                # Check file size
                file_size = os.path.getsize(path)
                print(f"   File size: {file_size / 1024 / 1024:.1f} MB")
                
                downloaded_count += 1
                break  # Download just one for testing
                
            except Exception as e:
                print(f"❌ Download failed: {e}")
        
        if downloaded_count == 0:
            print("\n⚠️ Could not download any cloudcasts")
            print("This is normal - Mixcloud protects most streams")
        
    finally:
        await client.close()


def main():
    """Main entry point."""
    # Check for environment variables
    if not os.getenv("MIXCLOUD_CLIENT_ID"):
        print("⚠️ Warning: MIXCLOUD_CLIENT_ID not set in environment")
        print("  OAuth2 authentication will not work")
    
    # Run tests
    asyncio.run(test_mixcloud())
    
    # Optionally test download
    if "--download" in sys.argv:
        asyncio.run(test_download_specific())


if __name__ == "__main__":
    main()