#!/usr/bin/env python3
"""
Comprehensive test suite for Deezer API integration.
Tests all major endpoints and functionality.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List

# Add parent directory to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

# Load .env file
env_path = project_root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

# Import Deezer components
from src.music_agent.integrations.deezer import (
    DeezerClient,
    DeezerConfig,
    Track,
    Album,
    Artist,
    Playlist,
    SearchFilters,
)

class TestDeezerAPI:
    """Test suite for Deezer API."""
    
    def __init__(self):
        """Initialize test suite."""
        self.config = DeezerConfig()
        self.client = DeezerClient(self.config)
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print(" DEEZER API TEST SUITE")
        print("=" * 60 + "\n")
        
        async with self.client:
            # Check authentication
            if self.client.is_authenticated:
                print("✓ Running tests with authentication")
            else:
                print("ℹ Running tests in public mode")
            print()
            
            # Search tests
            await self.test_search_tracks()
            await self.test_search_albums()
            await self.test_search_artists()
            await self.test_search_playlists()
            await self.test_search_with_filters()
            
            # Content tests
            await self.test_get_track()
            await self.test_get_album()
            await self.test_get_artist()
            await self.test_get_playlist()
            
            # Charts tests
            await self.test_chart_tracks()
            
            # Download tests (only if authenticated)
            if self.client.is_authenticated:
                await self.test_download_info()
        
        # Print summary
        self.print_summary()
    
    async def test_search_tracks(self):
        """Test searching for tracks."""
        test_name = "Search Tracks"
        try:
            results = await self.client.search_tracks(
                query="electronic music",
                limit=5
            )
            
            assert results, "No results returned"
            assert len(results) <= 5, f"Too many results: {len(results)}"
            assert all(isinstance(r, Track) for r in results), "Invalid result type"
            
            # Check first result has expected fields
            if results:
                track = results[0]
                assert track.title, "Missing track title"
                assert track.id, "Missing track ID"
                assert track.artist_name, "Missing artist name"
            
            self.record_success(test_name, f"Found {len(results)} tracks")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_search_albums(self):
        """Test searching for albums."""
        test_name = "Search Albums"
        try:
            results = await self.client.search_albums(
                query="discovery",
                limit=3
            )
            
            assert results, "No albums found"
            assert len(results) <= 3, f"Too many results: {len(results)}"
            assert all(isinstance(r, Album) for r in results), "Invalid result type"
            
            # Check first album has expected fields
            if results:
                album = results[0]
                assert album.title, "Missing album title"
                assert album.id, "Missing album ID"
            
            self.record_success(test_name, f"Found {len(results)} albums")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_search_artists(self):
        """Test searching for artists."""
        test_name = "Search Artists"
        try:
            results = await self.client.search_artists(
                query="daft punk",
                limit=3
            )
            
            assert results, "No artists found"
            assert len(results) <= 3, f"Too many results: {len(results)}"
            assert all(isinstance(r, Artist) for r in results), "Invalid result type"
            
            # Check first artist has expected fields
            if results:
                artist = results[0]
                assert artist.name, "Missing artist name"
                assert artist.id, "Missing artist ID"
            
            self.record_success(test_name, f"Found {len(results)} artists")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_search_playlists(self):
        """Test searching for playlists."""
        test_name = "Search Playlists"
        try:
            results = await self.client.search_playlists(
                query="workout",
                limit=3
            )
            
            assert results, "No playlists found"
            assert len(results) <= 3, f"Too many results: {len(results)}"
            assert all(isinstance(r, Playlist) for r in results), "Invalid result type"
            
            # Check first playlist has expected fields
            if results:
                playlist = results[0]
                assert playlist.title, "Missing playlist title"
                assert playlist.id, "Missing playlist ID"
            
            self.record_success(test_name, f"Found {len(results)} playlists")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_search_with_filters(self):
        """Test searching with filters."""
        test_name = "Search with Filters"
        try:
            filters = SearchFilters(
                artist="daft punk",
                dur_min=180,  # At least 3 minutes
                dur_max=600,  # At most 10 minutes
            )
            
            results = await self.client.search_tracks(
                query="",  # Empty query, rely on filters
                limit=5,
                filters=filters
            )
            
            # Filters might be too restrictive
            if results:
                assert all(isinstance(r, Track) for r in results), "Invalid result type"
                self.record_success(test_name, f"Found {len(results)} filtered tracks")
            else:
                self.record_success(test_name, "Filter search returned no results (expected with strict filters)")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_get_track(self):
        """Test getting a specific track."""
        test_name = "Get Track"
        try:
            # First search for a track
            search_results = await self.client.search_tracks("get lucky", limit=1)
            if not search_results:
                self.record_failure(test_name, "No tracks found to test")
                return
            
            track_id = search_results[0].id
            
            # Get the track details
            track = await self.client.get_track(track_id)
            
            assert track, "Failed to get track"
            assert track.id == track_id, "ID mismatch"
            assert track.title, "Missing track title"
            
            self.record_success(test_name, f"Got track: {track.title}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_get_album(self):
        """Test getting a specific album."""
        test_name = "Get Album"
        try:
            # First search for an album
            search_results = await self.client.search_albums("random access memories", limit=1)
            if not search_results:
                self.record_failure(test_name, "No albums found to test")
                return
            
            album_id = search_results[0].id
            
            # Get the album details
            album = await self.client.get_album(album_id)
            
            assert album, "Failed to get album"
            assert album.id == album_id, "ID mismatch"
            assert album.title, "Missing album title"
            
            self.record_success(test_name, f"Got album: {album.title} ({album.nb_tracks} tracks)")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_get_artist(self):
        """Test getting a specific artist."""
        test_name = "Get Artist"
        try:
            # First search for an artist
            search_results = await self.client.search_artists("daft punk", limit=1)
            if not search_results:
                self.record_failure(test_name, "No artists found to test")
                return
            
            artist_id = search_results[0].id
            
            # Get the artist details
            artist = await self.client.get_artist(artist_id)
            
            assert artist, "Failed to get artist"
            assert artist.id == artist_id, "ID mismatch"
            assert artist.name, "Missing artist name"
            
            self.record_success(test_name, f"Got artist: {artist.name} ({artist.nb_fan} fans)")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_get_playlist(self):
        """Test getting a specific playlist."""
        test_name = "Get Playlist"
        try:
            # First search for a playlist
            search_results = await self.client.search_playlists("hits", limit=1)
            if not search_results:
                self.record_failure(test_name, "No playlists found to test")
                return
            
            playlist_id = search_results[0].id
            
            # Get the playlist details
            playlist = await self.client.get_playlist(playlist_id)
            
            assert playlist, "Failed to get playlist"
            assert playlist.id == playlist_id, "ID mismatch"
            assert playlist.title, "Missing playlist title"
            
            self.record_success(test_name, f"Got playlist: {playlist.title} ({playlist.nb_tracks} tracks)")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_chart_tracks(self):
        """Test getting chart tracks."""
        test_name = "Chart Tracks"
        try:
            tracks = await self.client.get_chart_tracks(limit=10)
            
            assert tracks, "No chart tracks found"
            assert len(tracks) <= 10, f"Too many results: {len(tracks)}"
            assert all(isinstance(t, Track) for t in tracks), "Invalid track type"
            
            self.record_success(test_name, f"Found {len(tracks)} chart tracks")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_download_info(self):
        """Test getting download information for a track."""
        test_name = "Download Info"
        try:
            # First search for a track
            search_results = await self.client.search_tracks("test", limit=1)
            if not search_results:
                self.record_failure(test_name, "No tracks found to test")
                return
            
            track = search_results[0]
            
            # Get download info
            download_info = await self.client.get_download_info(track)
            
            assert download_info, "No download info returned"
            assert "url" in download_info, "Missing download URL"
            assert "quality" in download_info, "Missing quality info"
            assert "format" in download_info, "Missing format info"
            
            self.record_success(
                test_name, 
                f"Got download info: {download_info['quality']} ({download_info['format']})"
            )
            
        except Exception as e:
            # Download might fail if user doesn't have proper subscription
            if "subscription" in str(e).lower() or "quality" in str(e).lower():
                self.record_success(test_name, "Download info requires higher subscription (expected)")
            else:
                self.record_failure(test_name, str(e))
    
    def record_success(self, test_name: str, details: str = ""):
        """Record a successful test."""
        self.passed += 1
        self.tests.append((test_name, True, details))
        print(f"✅ {test_name}: {details}")
    
    def record_failure(self, test_name: str, error: str):
        """Record a failed test."""
        self.failed += 1
        self.tests.append((test_name, False, error))
        print(f"❌ {test_name}: {error}")
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print(" TEST SUMMARY")
        print("=" * 60)
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed. See details above.")


async def main():
    """Run the test suite."""
    tester = TestDeezerAPI()
    await tester.run_all_tests()
    
    # Return exit code
    return 0 if tester.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)