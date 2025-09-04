#!/usr/bin/env python3
"""
Test script for Beatport integration.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.beatport import BeatportClient, BeatportConfig


async def test_beatport():
    """Test Beatport integration."""
    print("🎵 Testing Beatport Integration\n")
    print("=" * 50)
    
    # Check for credentials
    if not os.getenv("BEATPORT_USERNAME") or not os.getenv("BEATPORT_PASSWORD"):
        print("❌ Please set BEATPORT_USERNAME and BEATPORT_PASSWORD environment variables")
        print("\nExample:")
        print("export BEATPORT_USERNAME='your_username'")
        print("export BEATPORT_PASSWORD='your_password'")
        return
    
    # Create client with config
    config = BeatportConfig.from_env()
    client = BeatportClient(config)
    
    try:
        await client.initialize()
        print("✅ Client initialized and authenticated\n")
        
        # Test 1: Search for tracks
        print("📍 Test 1: Search for tracks")
        print("-" * 30)
        
        try:
            tracks = await client.search_tracks("techno", page=1, per_page=5)
            print(f"Found {len(tracks)} tracks")
            
            for i, track in enumerate(tracks, 1):
                print(f"\n{i}. {track.full_title}")
                print(f"   Artists: {track.artist_names}")
                if track.remixers:
                    print(f"   Remixers: {track.remixer_names}")
                print(f"   BPM: {track.bpm}, Key: {track.key}")
                print(f"   Label: {track.label.name if track.label else 'Unknown'}")
                print(f"   Genre: {track.genre.name if track.genre else 'Unknown'}")
                if track.preview_url:
                    print(f"   Preview: {track.preview_url[:50]}...")
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        # Test 2: Get genres
        print("\n📍 Test 2: Get genres")
        print("-" * 30)
        
        try:
            genres = await client.get_genres()
            print(f"Found {len(genres)} genres")
            
            # Show first 10 genres
            for genre in genres[:10]:
                print(f"  {genre.id}: {genre.name}")
        except Exception as e:
            print(f"❌ Get genres failed: {e}")
        
        # Test 3: Get Top 100
        print("\n📍 Test 3: Get Top 100 (overall)")
        print("-" * 30)
        
        try:
            top_tracks = await client.get_top_100()
            print(f"Found {len(top_tracks)} tracks in Top 100")
            
            # Show top 5
            for i, track in enumerate(top_tracks[:5], 1):
                print(f"{i}. {track.full_title} by {track.artist_names}")
        except Exception as e:
            print(f"❌ Get Top 100 failed: {e}")
        
        # Test 4: Get specific track (if we found any)
        if tracks and len(tracks) > 0:
            print("\n📍 Test 4: Get track details")
            print("-" * 30)
            
            try:
                track_id = tracks[0].id
                track = await client.get_track(track_id)
                print(f"Track: {track.full_title}")
                print(f"  ID: {track.id}")
                print(f"  Artists: {track.artist_names}")
                print(f"  Released: {track.released}")
                print(f"  Length: {track.length}")
                print(f"  Price: {track.price} {track.price_currency}")
                if track.catalog_number:
                    print(f"  Catalog: {track.catalog_number}")
                if track.isrc:
                    print(f"  ISRC: {track.isrc}")
            except Exception as e:
                print(f"❌ Get track failed: {e}")
        
        # Test 5: Search for artist
        print("\n📍 Test 5: Search for artists")
        print("-" * 30)
        
        try:
            artists = await client.search_artists("carl cox", page=1, per_page=5)
            print(f"Found {len(artists)} artists")
            
            for artist in artists:
                print(f"  {artist.id}: {artist.name}")
                
            # Get tracks from first artist
            if artists:
                artist_id = artists[0].id
                print(f"\nGetting tracks for {artists[0].name}...")
                artist_tracks = await client.get_artist_tracks(artist_id, page=1, per_page=3)
                for track in artist_tracks:
                    print(f"  - {track.full_title}")
        except Exception as e:
            print(f"❌ Artist search failed: {e}")
        
        # Test 6: Search for label
        print("\n📍 Test 6: Search for labels")
        print("-" * 30)
        
        try:
            labels = await client.search_labels("drumcode", page=1, per_page=5)
            print(f"Found {len(labels)} labels")
            
            for label in labels:
                print(f"  {label.id}: {label.name}")
        except Exception as e:
            print(f"❌ Label search failed: {e}")
        
        # Test 7: Get Techno Top 100
        print("\n📍 Test 7: Get Techno Top 100")
        print("-" * 30)
        
        try:
            # Genre ID 6 is typically Techno
            techno_tracks = await client.get_top_100(genre_id=6)
            print(f"Found {len(techno_tracks)} Techno tracks")
            
            for i, track in enumerate(techno_tracks[:3], 1):
                print(f"{i}. {track.full_title} by {track.artist_names}")
        except Exception as e:
            print(f"❌ Get Techno Top 100 failed: {e}")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


def main():
    """Main entry point."""
    asyncio.run(test_beatport())


if __name__ == "__main__":
    main()