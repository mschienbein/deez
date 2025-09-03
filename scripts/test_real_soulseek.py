#!/usr/bin/env python3
"""
Test Real Soulseek Network Functionality
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
import json
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import slskd_api
from src.music_agent.integrations.soulseek import SoulseekClient, SoulseekDiscovery

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_search():
    """Test searching on the real Soulseek network"""
    print("\n" + "=" * 60)
    print("Testing Real Soulseek Network Search")
    print("=" * 60)
    
    api_key = os.getenv("SLSKD_API_KEY", "deez-slskd-api-key-2024")
    host = os.getenv("SLSKD_HOST", "http://localhost:5030")
    
    client = slskd_api.SlskdClient(host, api_key, "")
    
    # Test popular searches that should return results
    test_queries = [
        "Beatles",
        "Pink Floyd",
        "Electronic",
        "Jazz",
        "Classical music"
    ]
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        
        try:
            # Start search
            search_result = client.searches.search_text(
                searchText=query,
                fileLimit=100,
                filterResponses=True,
                searchTimeout=15000  # 15 seconds
            )
            
            search_id = search_result.get('id')
            print(f"  Search ID: {search_id}")
            
            # Wait for results
            print("  Waiting for results...")
            for i in range(10):  # Check for 10 seconds
                time.sleep(1)
                
                # Get search state
                try:
                    state = client.searches.state(search_id)
                    response_count = state.get('responseCount', 0)
                    file_count = state.get('fileCount', 0)
                    
                    if response_count > 0:
                        print(f"  Got {response_count} responses with {file_count} files")
                        
                        # Get actual responses
                        responses = client.searches.search_responses(search_id)
                        
                        # Show first few results
                        shown = 0
                        for response in responses[:3]:
                            username = response.get('username', 'unknown')
                            files = response.get('files', [])
                            if files:
                                print(f"\n  User: {username}")
                                for file in files[:2]:
                                    filename = file.get('filename', '')
                                    size_mb = file.get('size', 0) / (1024*1024)
                                    bitrate = file.get('bitRate', 'unknown')
                                    print(f"    - {Path(filename).name}")
                                    print(f"      Size: {size_mb:.1f} MB, Bitrate: {bitrate}")
                                    shown += 1
                                    if shown >= 5:
                                        break
                            if shown >= 5:
                                break
                        break
                    
                except Exception as e:
                    print(f"  Error checking state: {e}")
            
            # Clean up search
            try:
                client.searches.stop(search_id)
            except:
                pass
                
        except Exception as e:
            print(f"  Search failed: {e}")


async def test_server_status():
    """Test server connection status"""
    print("\n" + "=" * 60)
    print("Testing Server Status")
    print("=" * 60)
    
    api_key = os.getenv("SLSKD_API_KEY", "deez-slskd-api-key-2024")
    host = os.getenv("SLSKD_HOST", "http://localhost:5030")
    
    client = slskd_api.SlskdClient(host, api_key, "")
    
    try:
        # Get server state
        state = client.server.state()
        print(f"\nServer State:")
        print(f"  Username: {state.get('username', 'not connected')}")
        print(f"  Connected: {state.get('isConnected', False)}")
        
        if state.get('isConnected'):
            print(f"  Address: {state.get('address', 'unknown')}")
            
    except Exception as e:
        print(f"Failed to get server state: {e}")


async def test_browse_popular_user():
    """Test browsing a user who likely has files"""
    print("\n" + "=" * 60)
    print("Testing User Browse")
    print("=" * 60)
    
    client = SoulseekClient()
    
    try:
        await client.initialize()
        
        # First search for users with files
        print("\nSearching for users with music...")
        results = await client.search("music collection", max_results=10, timeout=10)
        
        if results:
            # Get unique users
            users = list(set([r['username'] for r in results]))[:3]
            
            for username in users:
                print(f"\nBrowsing user: {username}")
                files = await client.browse_user(username)
                
                if files:
                    print(f"  Found {len(files)} files")
                    for file in files[:5]:
                        print(f"    - {file['filename']}")
                else:
                    print(f"  No files or browse failed")
                    
    except Exception as e:
        print(f"Browse test failed: {e}")
    finally:
        await client.close()


async def test_with_discovery():
    """Test using the high-level discovery interface"""
    print("\n" + "=" * 60)
    print("Testing Discovery Interface")
    print("=" * 60)
    
    discovery = SoulseekDiscovery()
    
    try:
        await discovery.initialize()
        
        # Search for electronic music
        print("\nDiscovering electronic music...")
        tracks = await discovery.discover_tracks(
            genre="electronic",
            bpm_range=(120, 130)
        )
        
        if tracks:
            print(f"Found {len(tracks)} tracks:")
            for track in tracks[:5]:
                print(f"  - {track['filename']}")
                print(f"    From: {track['username']}")
        else:
            print("No tracks found")
            
    except Exception as e:
        print(f"Discovery test failed: {e}")
    finally:
        await discovery.close()


async def main():
    """Run all real network tests"""
    print("=" * 60)
    print("Real Soulseek Network Test")
    print("=" * 60)
    
    # Set API key
    os.environ["SLSKD_API_KEY"] = "deez-slskd-api-key-2024"
    
    await test_server_status()
    await test_real_search()
    await test_browse_popular_user()
    await test_with_discovery()
    
    print("\n" + "=" * 60)
    print("Real Network Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())