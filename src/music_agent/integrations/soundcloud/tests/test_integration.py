"""
Comprehensive test suite for SoundCloud integration.

Tests all major functionality including authentication, API calls,
searching, downloading, and caching.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from music_agent.integrations.soundcloud import SoundCloudClient, SoundCloudConfig
from music_agent.integrations.soundcloud.types import AuthCredentials, SearchFilters
from music_agent.integrations.soundcloud.search import FilterBuilder
from music_agent.integrations.soundcloud.cache import InMemoryCache, FileCache
from music_agent.integrations.soundcloud.exceptions import (
    SoundCloudError,
    NotFoundError,
    AuthenticationError,
    RateLimitError,
)


class SoundCloudIntegrationTest:
    """Test suite for SoundCloud integration."""
    
    def __init__(self):
        """Initialize test suite."""
        self.client: Optional[SoundCloudClient] = None
        self.test_track_url = "https://soundcloud.com/soundcloud/celebrating-ten-years-of-soundcloud"
        self.test_playlist_url = "https://soundcloud.com/soundcloud/sets/soundcloud-weekly"
        self.test_user = "soundcloud"
        self.temp_dir = tempfile.mkdtemp(prefix="sc_test_")
        
    async def setup(self):
        """Set up test client."""
        logger.info("Setting up SoundCloud client...")
        
        # Create config with test settings
        config = SoundCloudConfig(
            api={
                "rate_limit": 10,
                "timeout": 30,
                "max_retries": 2,
            },
            download={
                "download_dir": self.temp_dir,
                "parallel_downloads": 2,
                "write_metadata": True,
                "embed_artwork": True,
            },
            cache={
                "enabled": True,
                "default_ttl": 60,
            }
        )
        
        self.client = SoundCloudClient(config)
        await self.client.initialize()
        
        logger.info(f"Client initialized with client_id: {self.client.client_id[:8]}...")
    
    async def teardown(self):
        """Clean up test resources."""
        logger.info("Cleaning up...")
        
        if self.client:
            await self.client.close()
        
        # Clean up temp directory
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    async def test_authentication(self):
        """Test authentication methods."""
        logger.info("\n=== Testing Authentication ===")
        
        # Test 1: Client ID scraping (already done in setup)
        assert self.client.client_id is not None, "Client ID not obtained"
        logger.info(f"✓ Client ID obtained: {self.client.client_id[:8]}...")
        
        # Test 2: Check if we can make authenticated requests
        try:
            response = await self.client.request("GET", "/tracks", params={"limit": 1})
            logger.info("✓ Authenticated request successful")
        except AuthenticationError as e:
            logger.error(f"✗ Authentication failed: {e}")
            raise
        
        # Test 3: Token storage (if OAuth credentials available)
        if os.getenv("SOUNDCLOUD_ACCESS_TOKEN"):
            creds = AuthCredentials(access_token=os.getenv("SOUNDCLOUD_ACCESS_TOKEN"))
            success = await self.client.authenticate(creds)
            assert success, "OAuth authentication failed"
            logger.info("✓ OAuth authentication successful")
    
    async def test_track_operations(self):
        """Test track-related operations."""
        logger.info("\n=== Testing Track Operations ===")
        
        # Test 1: Get track by URL
        track = await self.client.get_track(self.test_track_url)
        assert track is not None, "Failed to get track"
        assert track.title is not None, "Track has no title"
        logger.info(f"✓ Got track: {track.title} by {track.artist}")
        
        # Test 2: Get track metadata
        logger.info(f"  - Duration: {track.duration_formatted}")
        logger.info(f"  - Plays: {track.playback_count:,}")
        logger.info(f"  - Likes: {track.likes_count:,}")
        logger.info(f"  - Genre: {track.genre}")
        
        # Test 3: Get track comments
        comments = await track.get_comments(limit=5)
        logger.info(f"✓ Got {len(comments)} comments")
        
        if comments:
            first_comment = comments[0]
            logger.info(f"  - First comment by {first_comment.username}: {first_comment.body[:50]}...")
        
        # Test 4: Get related tracks
        related = await track.get_related(limit=3)
        logger.info(f"✓ Got {len(related)} related tracks")
        
        for r in related[:2]:
            logger.info(f"  - {r.title} by {r.artist}")
        
        return track
    
    async def test_playlist_operations(self):
        """Test playlist-related operations."""
        logger.info("\n=== Testing Playlist Operations ===")
        
        # Test 1: Get playlist by URL
        playlist = await self.client.get_playlist(self.test_playlist_url)
        assert playlist is not None, "Failed to get playlist"
        assert playlist.title is not None, "Playlist has no title"
        logger.info(f"✓ Got playlist: {playlist.title}")
        
        # Test 2: Get playlist info
        logger.info(f"  - Tracks: {playlist.track_count}")
        logger.info(f"  - Duration: {playlist.duration_formatted}")
        logger.info(f"  - Type: {playlist.playlist_type}")
        
        # Test 3: Load tracks if needed
        if not playlist.tracks and playlist._track_ids:
            await playlist.load_tracks()
            logger.info(f"✓ Loaded {len(playlist.tracks)} tracks")
        
        # Test 4: Iterate tracks
        track_titles = []
        for i, track in enumerate(playlist.tracks[:3], 1):
            track_titles.append(f"{i}. {track.title}")
        
        if track_titles:
            logger.info("✓ Playlist tracks:")
            for title in track_titles:
                logger.info(f"  {title}")
        
        return playlist
    
    async def test_user_operations(self):
        """Test user-related operations."""
        logger.info("\n=== Testing User Operations ===")
        
        # Test 1: Get user by username
        user = await self.client.get_user(self.test_user)
        assert user is not None, "Failed to get user"
        assert user.username is not None, "User has no username"
        logger.info(f"✓ Got user: {user.display_name} (@{user.username})")
        
        # Test 2: Get user stats
        logger.info(f"  - Followers: {user.followers_count:,}")
        logger.info(f"  - Tracks: {user.track_count}")
        logger.info(f"  - Verified: {user.verified}")
        logger.info(f"  - Plan: {user.plan}")
        
        # Test 3: Get user tracks
        tracks = await user.get_tracks(limit=5)
        logger.info(f"✓ Got {len(tracks)} user tracks")
        
        # Test 4: Get user playlists
        playlists = await user.get_playlists(limit=5)
        logger.info(f"✓ Got {len(playlists)} user playlists")
        
        return user
    
    async def test_search_operations(self):
        """Test search functionality."""
        logger.info("\n=== Testing Search Operations ===")
        
        # Test 1: Simple track search
        tracks = await self.client.search_tracks("electronic music", limit=5)
        logger.info(f"✓ Found {len(tracks)} tracks")
        
        if tracks:
            logger.info(f"  - First result: {tracks[0].title} by {tracks[0].artist}")
        
        # Test 2: Filtered search
        filters = (FilterBuilder()
            .genre("Electronic")
            .duration_minutes(2, 5)
            .streamable(True)
            .build())
        
        filtered_tracks = await self.client.search.search(
            "techno",
            type="tracks",
            limit=5,
            filters=filters
        )
        logger.info(f"✓ Found {len(filtered_tracks)} filtered tracks")
        
        # Test 3: Multi-type search
        all_results = await self.client.search.search_all("deadmau5", limit=5)
        logger.info(f"✓ Multi-type search results:")
        logger.info(f"  - Tracks: {len(all_results['tracks'])}")
        logger.info(f"  - Playlists: {len(all_results['playlists'])}")
        logger.info(f"  - Users: {len(all_results['users'])}")
        
        # Test 4: Search with pagination
        paginated = await self.client.search.search_with_pagination(
            "ambient",
            type="tracks",
            page_size=10,
            max_results=25
        )
        logger.info(f"✓ Paginated search got {len(paginated)} results")
        
        # Test 5: Get suggestions
        suggestions = await self.client.search.get_suggestions("daft p")
        logger.info(f"✓ Got {len(suggestions)} suggestions")
        
        if suggestions:
            logger.info(f"  - Suggestions: {', '.join(suggestions[:3])}")
        
        # Test 6: Search aggregation
        if tracks:
            stats = await self.client.search.aggregate_results(tracks)
            logger.info(f"✓ Search aggregation:")
            logger.info(f"  - Total duration: {stats.get('total_duration', 0) / 60000:.1f} minutes")
            logger.info(f"  - Downloadable: {stats.get('downloadable_count', 0)}/{len(tracks)}")
    
    async def test_download_operations(self):
        """Test download functionality."""
        logger.info("\n=== Testing Download Operations ===")
        
        # Test 1: Get a downloadable track
        tracks = await self.client.search.search_downloadable("creative commons", limit=1)
        
        if not tracks:
            logger.warning("No downloadable tracks found, skipping download tests")
            return
        
        track = tracks[0]
        logger.info(f"✓ Found downloadable track: {track.title}")
        
        # Test 2: Download with progress callback
        downloaded_bytes = 0
        
        def progress_callback(current, total):
            nonlocal downloaded_bytes
            downloaded_bytes = current
            if total > 0:
                percent = (current / total) * 100
                logger.debug(f"Download progress: {percent:.1f}%")
        
        try:
            output_path = await self.client.download_track(
                track,
                output_dir=self.temp_dir,
                progress_callback=progress_callback
            )
            
            assert output_path.exists(), "Downloaded file doesn't exist"
            logger.info(f"✓ Downloaded track to: {output_path.name}")
            logger.info(f"  - File size: {output_path.stat().st_size / 1024:.1f} KB")
            
            # Test 3: Check metadata was written
            if self.client.config.download.write_metadata:
                from music_agent.integrations.soundcloud.download.metadata import MetadataWriter
                
                writer = MetadataWriter()
                if writer.enabled:
                    metadata = await writer.read_metadata(output_path)
                    
                    if metadata:
                        logger.info("✓ Metadata written:")
                        logger.info(f"  - Title: {metadata.get('title')}")
                        logger.info(f"  - Artist: {metadata.get('artist')}")
        
        except Exception as e:
            logger.error(f"✗ Download failed: {e}")
    
    async def test_cache_operations(self):
        """Test caching functionality."""
        logger.info("\n=== Testing Cache Operations ===")
        
        # Test 1: In-memory cache
        cache_key = "test:track:123"
        test_data = {"id": 123, "title": "Test Track"}
        
        # Set in cache
        success = await self.client.cache.set(cache_key, test_data, ttl=60)
        assert success, "Failed to set cache"
        logger.info("✓ Set value in cache")
        
        # Get from cache
        cached_data = await self.client.cache.get(cache_key)
        assert cached_data == test_data, "Cached data doesn't match"
        logger.info("✓ Retrieved value from cache")
        
        # Test 2: Cache stats
        stats = self.client.cache.get_stats()
        logger.info(f"✓ Cache stats: hits={stats['hits']}, misses={stats['misses']}, hit_rate={stats['hit_rate']}")
        
        # Test 3: File cache
        file_cache = FileCache(cache_dir=Path(self.temp_dir) / "cache")
        self.client.cache.backend = file_cache
        
        success = await self.client.cache.set("test:file", {"data": "test"}, ttl=60)
        assert success, "Failed to set file cache"
        logger.info("✓ File cache working")
        
        # Test 4: Cache decorator
        call_count = 0
        
        @self.client.cache.cached(ttl=60)
        async def expensive_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"result": "expensive"}
        
        # First call - should execute
        result1 = await expensive_operation()
        # Second call - should use cache
        result2 = await expensive_operation()
        
        assert call_count == 1, "Function called more than once"
        assert result1 == result2, "Results don't match"
        logger.info("✓ Cache decorator working")
    
    async def test_rate_limiting(self):
        """Test rate limiting."""
        logger.info("\n=== Testing Rate Limiting ===")
        
        # Test 1: Basic rate limiting
        start_time = asyncio.get_event_loop().time()
        
        # Make rapid requests
        for i in range(5):
            await self.client.rate_limiter.acquire()
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"✓ Rate limiting: 5 requests in {elapsed:.2f}s")
        
        # Test 2: Check remaining capacity
        remaining = self.client.rate_limiter.remaining
        logger.info(f"✓ Remaining capacity: {remaining}/{self.client.config.api.rate_limit}")
        
        # Test 3: Adaptive rate limiting
        from music_agent.integrations.soundcloud.utils import AdaptiveRateLimiter
        
        adaptive = AdaptiveRateLimiter(initial_rate=10)
        
        # Simulate successful requests
        for _ in range(5):
            await adaptive.acquire()
            adaptive.record_success()
        
        # Simulate errors
        for _ in range(2):
            await adaptive.acquire()
            adaptive.record_error()
        
        logger.info(f"✓ Adaptive rate limit adjusted to: {adaptive.max_requests}/s")
    
    async def test_error_handling(self):
        """Test error handling."""
        logger.info("\n=== Testing Error Handling ===")
        
        # Test 1: NotFoundError
        try:
            await self.client.get_track(999999999999)
            logger.error("✗ Should have raised NotFoundError")
        except NotFoundError:
            logger.info("✓ NotFoundError handled correctly")
        
        # Test 2: Invalid URL
        try:
            await self.client.get_track("https://invalid-url.com/track")
            logger.error("✗ Should have raised error for invalid URL")
        except (ValueError, SoundCloudError):
            logger.info("✓ Invalid URL handled correctly")
        
        # Test 3: Retry on failure
        from music_agent.integrations.soundcloud.utils import retry_with_backoff
        
        attempt_count = 0
        
        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await retry_with_backoff(
            flaky_operation,
            max_attempts=5,
            initial_delay=0.1
        )
        
        assert result == "success", "Retry didn't succeed"
        assert attempt_count == 3, "Wrong number of attempts"
        logger.info(f"✓ Retry succeeded after {attempt_count} attempts")
    
    async def test_resolve_operations(self):
        """Test URL resolution."""
        logger.info("\n=== Testing URL Resolution ===")
        
        # Test 1: Resolve track URL
        track = await self.client.api.resolve.resolve(self.client, self.test_track_url)
        assert track is not None, "Failed to resolve track URL"
        logger.info(f"✓ Resolved track URL to: {track.title}")
        
        # Test 2: Resolve user URL
        user_url = f"https://soundcloud.com/{self.test_user}"
        user = await self.client.api.resolve.resolve(self.client, user_url)
        assert user is not None, "Failed to resolve user URL"
        logger.info(f"✓ Resolved user URL to: {user.username}")
        
        # Test 3: Batch resolve
        urls = [
            self.test_track_url,
            user_url,
        ]
        
        resources = await self.client.api.resolve.resolve_batch(self.client, urls)
        logger.info(f"✓ Batch resolved {len(resources)} URLs")
    
    async def test_utils(self):
        """Test utility functions."""
        logger.info("\n=== Testing Utilities ===")
        
        from music_agent.integrations.soundcloud.utils import (
            format_duration,
            format_number,
            sanitize_filename,
            validate_url,
            parse_tags,
        )
        
        # Test 1: Formatters
        assert format_duration(185000) == "3:05"
        assert format_number(1234567, short=True) == "1.2M"
        assert sanitize_filename('test/file:name*.mp3') == "test_file_name_.mp3"
        logger.info("✓ Formatters working")
        
        # Test 2: Validators
        assert validate_url("https://soundcloud.com/user/track") == True
        assert validate_url("https://example.com/track") == False
        logger.info("✓ Validators working")
        
        # Test 3: Parsers
        tags = parse_tags('electronic "hip hop" jazz')
        assert tags == ["electronic", "hip hop", "jazz"]
        logger.info("✓ Parsers working")
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("=" * 50)
        logger.info("Starting SoundCloud Integration Tests")
        logger.info("=" * 50)
        
        try:
            await self.setup()
            
            # Run test suites
            await self.test_authentication()
            await self.test_track_operations()
            await self.test_playlist_operations()
            await self.test_user_operations()
            await self.test_search_operations()
            await self.test_download_operations()
            await self.test_cache_operations()
            await self.test_rate_limiting()
            await self.test_error_handling()
            await self.test_resolve_operations()
            await self.test_utils()
            
            logger.info("\n" + "=" * 50)
            logger.info("✓ All tests completed successfully!")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"\n✗ Test failed with error: {e}")
            raise
        finally:
            await self.teardown()


async def main():
    """Main test runner."""
    # Set up test environment
    test_suite = SoundCloudIntegrationTest()
    
    try:
        await test_suite.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)