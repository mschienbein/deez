#!/usr/bin/env python3
"""
Test script for Bandcamp integration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.bandcamp import BandcampClient


async def test_bandcamp():
    """Test Bandcamp integration."""
    print("🎵 Testing Bandcamp Integration\n")
    print("=" * 50)
    
    client = BandcampClient()
    
    try:
        await client.initialize()
        print("✅ Client initialized\n")
        
        # Test 1: Search for music
        print("📍 Test 1: Search for albums")
        print("-" * 30)
        
        results = await client.search_albums("ambient", page=1)
        print(f"Found {len(results)} albums")
        
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['name']}")
            if result.get('artist'):
                print(f"   By: {result['artist']}")
            if result.get('genre'):
                print(f"   Genre: {result['genre']}")
            print(f"   URL: {result['url']}")
        
        # Test 2: Get album details
        print("\n📍 Test 2: Get album details")
        print("-" * 30)
        
        # Use a known free album for testing
        test_url = "https://music.monstercat.com/album/monstercat-instinct-vol-1"
        
        # Try alternative URL if first doesn't work
        try:
            album = await client.get_album(test_url)
        except:
            # Try a different album
            test_url = "https://machinedrum.bandcamp.com/album/a-view-of-u"
            try:
                album = await client.get_album(test_url)
            except:
                # Use first search result if available
                if results:
                    test_url = results[0]['url']
                    album = await client.get_album(test_url)
                else:
                    print("⚠️ Could not get album details")
                    album = None
        
        if album:
            print(f"Album: {album.title}")
            print(f"Artist: {album.artist}")
            print(f"Tracks: {album.num_tracks}")
            print(f"Tags: {', '.join(album.tags[:5])}")
            
            # Show first 3 tracks
            if album.tracks:
                print("\nTracklist:")
                for track in album.tracks[:3]:
                    print(f"  {track.track_num or '-'}. {track.title} ({track.duration_formatted})")
        
        # Test 3: Search for artists
        print("\n📍 Test 3: Search for artists")
        print("-" * 30)
        
        artist_results = await client.search_artists("electronic", page=1)
        print(f"Found {len(artist_results)} artists")
        
        for i, artist in enumerate(artist_results[:3], 1):
            print(f"{i}. {artist['name']}")
            if artist.get('location'):
                print(f"   Location: {artist['location']}")
        
        # Test 4: Get track (single)
        print("\n📍 Test 4: Get single track")
        print("-" * 30)
        
        # Search for tracks
        track_results = await client.search_tracks("lo-fi", page=1)
        if track_results:
            track_url = track_results[0]['url']
            print(f"Getting track from: {track_url}")
            
            try:
                track = await client.get_track(track_url)
                print(f"Track: {track.title}")
                print(f"Artist: {track.artist}")
                print(f"Duration: {track.duration_formatted}")
                print(f"Streamable: {track.is_streamable}")
            except Exception as e:
                print(f"⚠️ Could not get track: {e}")
        
        # Test 5: Check download capability
        print("\n📍 Test 5: Check download capability")
        print("-" * 30)
        
        if album and album.tracks:
            downloadable = album.get_downloadable_tracks()
            print(f"Downloadable tracks: {len(downloadable)}/{album.num_tracks}")
            
            if downloadable:
                track = downloadable[0]
                print(f"Example: {track.title}")
                print(f"  Stream URL available: {bool(track.stream_url)}")
                print(f"  Free: {track.free}")
        
        # Test 6: URL parsing
        print("\n📍 Test 6: URL parsing")
        print("-" * 30)
        
        from src.music_agent.integrations.bandcamp.utils import parse_bandcamp_url
        
        test_urls = [
            "https://artist.bandcamp.com",
            "https://artist.bandcamp.com/album/test-album",
            "https://artist.bandcamp.com/track/test-track",
        ]
        
        for url in test_urls:
            try:
                url_type, artist, item = parse_bandcamp_url(url)
                print(f"URL: {url}")
                print(f"  Type: {url_type}, Artist: {artist}, Item: {item}")
            except Exception as e:
                print(f"  Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


async def test_download():
    """Test downloading functionality."""
    print("\n🎵 Testing Bandcamp Download")
    print("=" * 50)
    
    client = BandcampClient()
    
    try:
        await client.initialize()
        
        # Search for free/name-your-price albums
        print("Searching for free music...")
        results = await client.search_albums("free", page=1)
        
        downloaded = False
        for result in results[:5]:
            try:
                print(f"\nTrying: {result['name']}")
                album = await client.get_album(result['url'])
                
                # Check if any tracks are downloadable
                downloadable = album.get_downloadable_tracks()
                if downloadable:
                    print(f"  Found {len(downloadable)} downloadable tracks")
                    
                    # Download first track as test
                    track = downloadable[0]
                    if track.stream_url:
                        download_dir = Path("downloads/bandcamp_test")
                        download_dir.mkdir(parents=True, exist_ok=True)
                        
                        path = await client.download_track(
                            track,
                            output_dir=str(download_dir)
                        )
                        
                        print(f"✅ Downloaded: {path}")
                        downloaded = True
                        break
            
            except Exception as e:
                print(f"  Failed: {e}")
                continue
        
        if not downloaded:
            print("\n⚠️ Could not find downloadable content")
            print("Note: Most Bandcamp content requires purchase")
    
    finally:
        await client.close()


def main():
    """Main entry point."""
    # Run tests
    asyncio.run(test_bandcamp())
    
    # Test download if requested
    if "--download" in sys.argv:
        asyncio.run(test_download())


if __name__ == "__main__":
    main()