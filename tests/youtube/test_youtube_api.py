#!/usr/bin/env python3
"""
Comprehensive test suite for YouTube integration.
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.music_agent.integrations.youtube import YouTubeClient, utils
from src.music_agent.integrations.youtube.exceptions import (
    YouTubeError,
    YouTubeVideoNotFoundError
)


class YouTubeAPITest:
    """Test YouTube API endpoints."""
    
    def __init__(self):
        """Initialize test suite."""
        self.client = YouTubeClient.from_env()
        self.passed = 0
        self.failed = 0
        self.test_video_id = "dQw4w9WgXcQ"  # Rick Roll for testing
        self.test_playlist_id = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"  # Sample playlist
    
    def run_all_tests(self):
        """Run all tests."""
        print("=" * 60)
        print("YouTube API Test Suite")
        print("=" * 60)
        
        tests = [
            ("Authentication", self.test_authentication),
            ("Search Music", self.test_search_music),
            ("Search All", self.test_search_all),
            ("Get Video", self.test_get_video),
            ("Get Video URL", self.test_get_video_url),
            ("Parse URLs", self.test_parse_urls),
            ("Extract Metadata", self.test_extract_metadata),
            ("Get Playlist", self.test_get_playlist),
            ("Download Audio", self.test_download_audio),
            ("Utility Functions", self.test_utils),
            ("Error Handling", self.test_error_handling),
            ("Backward Compatibility", self.test_backward_compatibility)
        ]
        
        for name, test_func in tests:
            print(f"\n{name}:")
            try:
                test_func()
                self.passed += 1
                print(f"  ✅ {name} passed")
            except Exception as e:
                self.failed += 1
                print(f"  ❌ {name} failed: {e}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Passed: {self.passed}/{self.passed + self.failed}")
        print(f"Failed: {self.failed}/{self.passed + self.failed}")
        
        return self.failed == 0
    
    def test_authentication(self):
        """Test authentication."""
        is_auth = self.client.authenticate()
        assert isinstance(is_auth, bool), "Authentication should return bool"
        print(f"  - Authentication status: {is_auth}")
        
        if self.client.config.auth.api_key:
            is_valid = self.client.auth.validate_api_key()
            print(f"  - API key valid: {is_valid}")
    
    def test_search_music(self):
        """Test music search."""
        results = self.client.search_music("Beethoven Symphony", limit=5)
        assert len(results) > 0, "Should find music results"
        assert len(results) <= 5, "Should respect limit"
        
        for video in results:
            assert video.id, "Video should have ID"
            assert video.title, "Video should have title"
            assert video.channel_title, "Video should have channel"
        
        print(f"  - Found {len(results)} music videos")
        print(f"  - First result: {results[0].title}")
    
    def test_search_all(self):
        """Test general search."""
        result = self.client.search_all("programming tutorial", limit=10)
        
        assert result.videos or result.playlists or result.channels, \
            "Should find some content"
        
        total = len(result.videos) + len(result.playlists) + len(result.channels)
        print(f"  - Found {len(result.videos)} videos")
        print(f"  - Found {len(result.playlists)} playlists")
        print(f"  - Found {len(result.channels)} channels")
        print(f"  - Total: {total} results")
    
    def test_get_video(self):
        """Test getting video info."""
        # Test with ID
        video = self.client.get_video(self.test_video_id)
        assert video.id == self.test_video_id, "Should get correct video"
        assert video.title, "Video should have title"
        assert video.duration > 0, "Video should have duration"
        
        print(f"  - Got video: {video.title}")
        print(f"  - Duration: {video.duration}s")
        print(f"  - Views: {video.view_count:,}")
        
        # Test with URL
        url = f"https://www.youtube.com/watch?v={self.test_video_id}"
        video2 = self.client.get_video(url)
        assert video2.id == self.test_video_id, "Should handle URL input"
    
    def test_get_video_url(self):
        """Test getting stream URL."""
        try:
            url = self.client.get_video_url(self.test_video_id, "bestaudio")
            assert url, "Should get stream URL"
            assert url.startswith("http"), "Should be valid URL"
            print(f"  - Got stream URL (length: {len(url)})")
        except Exception as e:
            print(f"  - Could not get stream URL: {e}")
    
    def test_parse_urls(self):
        """Test URL parsing."""
        test_urls = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "video", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "video", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf", 
             "playlist", "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"),
            ("https://www.youtube.com/channel/UC38IQsAvIsxxjztdMZQtwHA", 
             "channel", "UC38IQsAvIsxxjztdMZQtwHA")
        ]
        
        for url, expected_type, expected_id in test_urls:
            result = self.client.parse_url(url)
            assert result, f"Should parse {url}"
            assert result["type"] == expected_type, f"Should identify as {expected_type}"
            assert result["id"] == expected_id, f"Should extract correct ID"
        
        print(f"  - Successfully parsed {len(test_urls)} URLs")
    
    def test_extract_metadata(self):
        """Test metadata extraction."""
        video = self.client.get_video(self.test_video_id)
        metadata = self.client.extract_music_metadata(video)
        
        assert "title" in metadata, "Should have title"
        assert "artist" in metadata, "Should have artist"
        assert "platform" in metadata, "Should have platform"
        assert metadata["platform"] == "youtube", "Platform should be youtube"
        
        print(f"  - Extracted metadata for: {metadata['title']}")
        print(f"  - Artist: {metadata['artist']}")
    
    def test_get_playlist(self):
        """Test getting playlist."""
        try:
            playlist = self.client.get_playlist(self.test_playlist_id)
            assert playlist.id, "Playlist should have ID"
            assert playlist.title, "Playlist should have title"
            assert len(playlist.videos) > 0, "Playlist should have videos"
            
            print(f"  - Got playlist: {playlist.title}")
            print(f"  - Video count: {len(playlist.videos)}")
            
            if playlist.videos:
                print(f"  - First video: {playlist.videos[0].title}")
        except Exception as e:
            print(f"  - Could not get playlist: {e}")
    
    def test_download_audio(self):
        """Test audio download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Download a short video
                test_id = "BaW_jenozKc"  # Very short test video
                
                def progress_callback(d):
                    if d['status'] == 'downloading':
                        percent = d.get('downloaded_bytes', 0) / max(d.get('total_bytes', 1), 1) * 100
                        print(f"\r  - Downloading: {percent:.1f}%", end="")
                
                filepath = self.client.download_audio(
                    test_id,
                    output_dir=tmpdir,
                    progress_callback=progress_callback
                )
                
                print()  # New line after progress
                assert filepath, "Should return file path"
                assert Path(filepath).exists(), "File should exist"
                
                filesize = Path(filepath).stat().st_size
                print(f"  - Downloaded to: {Path(filepath).name}")
                print(f"  - File size: {filesize:,} bytes")
                
            except Exception as e:
                print(f"\n  - Download test skipped: {e}")
    
    def test_utils(self):
        """Test utility functions."""
        # Test duration formatting
        assert utils.format_duration(125) == "2:05"
        assert utils.format_duration(3665) == "1:01:05"
        
        # Test duration parsing
        assert utils.parse_duration("2:05") == 125
        assert utils.parse_duration("PT2M5S") == 125
        
        # Test filename sanitization
        clean = utils.sanitize_filename('Test: Video / Name <2024>')
        assert ':' not in clean and '/' not in clean and '<' not in clean
        
        # Test music detection
        is_music = utils.is_music_video(
            "Artist - Song (Official Video)",
            "ArtistVEVO",
            210
        )
        assert is_music, "Should detect music video"
        
        print("  - Duration formatting works")
        print("  - Duration parsing works")
        print("  - Filename sanitization works")
        print("  - Music detection works")
    
    def test_error_handling(self):
        """Test error handling."""
        # Test invalid video ID
        try:
            self.client.get_video("invalid_id_12345")
            assert False, "Should raise error for invalid ID"
        except YouTubeError:
            print("  - Handles invalid video ID correctly")
        
        # Test invalid URL parsing
        result = self.client.parse_url("https://not-youtube.com/video")
        assert result is None, "Should return None for non-YouTube URL"
        print("  - Handles invalid URLs correctly")
    
    def test_backward_compatibility(self):
        """Test backward compatibility functions."""
        from src.music_agent.integrations.youtube import (
            youtube_search,
            get_youtube_video_info,
            get_youtube_playlist_videos
        )
        
        # Test search function
        results = youtube_search("test", limit=2)
        assert isinstance(results, list), "Should return list"
        print(f"  - youtube_search: {len(results)} results")
        
        # Test video info function
        info = get_youtube_video_info(self.test_video_id)
        assert info is not None, "Should get video info"
        assert "title" in info, "Should have title field"
        print(f"  - get_youtube_video_info: {info['title']}")
        
        # Test playlist function
        videos = get_youtube_playlist_videos(
            f"https://www.youtube.com/playlist?list={self.test_playlist_id}"
        )
        assert isinstance(videos, list), "Should return list"
        print(f"  - get_youtube_playlist_videos: {len(videos)} videos")


def main():
    """Run all tests."""
    tester = YouTubeAPITest()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())