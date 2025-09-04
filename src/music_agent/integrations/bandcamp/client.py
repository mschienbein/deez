"""
Main Bandcamp client.
"""

import asyncio
import logging
from typing import Optional, List, Union
import aiohttp
from aiohttp import ClientSession

from .config import BandcampConfig
from .scraper import AlbumScraper, SearchScraper
from .download import DownloadManager
from .models import Album, Track
from .types import SearchResult, DownloadOptions
from .utils import parse_bandcamp_url, is_bandcamp_url
from .exceptions import BandcampError, InvalidURLError

logger = logging.getLogger(__name__)


class BandcampClient:
    """Main client for Bandcamp integration."""
    
    def __init__(
        self,
        config: Optional[BandcampConfig] = None,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Bandcamp client.
        
        Args:
            config: Optional configuration
            session: Optional aiohttp session
        """
        self.config = config or BandcampConfig.from_env()
        self._session = session
        self._owns_session = session is None
        
        # Initialize components
        self._album_scraper = None
        self._search_scraper = None
        self._download_manager = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize the client."""
        # Create session if needed
        if not self._session:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(connector=connector)
        
        # Initialize scrapers
        self._album_scraper = AlbumScraper(self._session, self.config.scraper)
        self._search_scraper = SearchScraper(self._session, self.config.scraper)
        
        # Initialize download manager if enabled
        if self.config.enable_downloads:
            self._download_manager = DownloadManager(self._session, self.config.download)
        
        logger.info("Bandcamp client initialized")
    
    async def close(self):
        """Close the client and cleanup resources."""
        if self._owns_session and self._session:
            await self._session.close()
        
        logger.info("Bandcamp client closed")
    
    # Album methods
    
    async def get_album(self, url: str) -> Album:
        """
        Get album information.
        
        Args:
            url: Album URL
            
        Returns:
            Album object
        """
        if not is_bandcamp_url(url):
            raise InvalidURLError(f"Not a Bandcamp URL: {url}")
        
        album_info = await self._album_scraper.scrape_album(url)
        return Album(album_info)
    
    async def get_album_from_artist(self, artist: str, album_name: str) -> Album:
        """
        Get album by artist and album name.
        
        Args:
            artist: Artist name (subdomain)
            album_name: Album name/slug
            
        Returns:
            Album object
        """
        from .utils import get_bandcamp_url, sanitize_for_url
        
        artist_slug = sanitize_for_url(artist)
        album_slug = sanitize_for_url(album_name)
        url = get_bandcamp_url(artist_slug, "album", album_slug)
        
        return await self.get_album(url)
    
    # Track methods
    
    async def get_track(self, url: str) -> Track:
        """
        Get track information.
        
        Args:
            url: Track URL
            
        Returns:
            Track object
        """
        if not is_bandcamp_url(url):
            raise InvalidURLError(f"Not a Bandcamp URL: {url}")
        
        # Parse as album (single track)
        page_data = await self._album_scraper.scrape_page(url)
        
        if page_data["type"] != "track":
            raise InvalidURLError(f"URL is not a track page: {url}")
        
        # Extract track data
        data = page_data["data"]
        stream_data = page_data.get("stream_data", {})
        
        track_info = {
            "id": data.get("id", ""),
            "title": data.get("title", ""),
            "artist": data.get("artist", ""),
            "album": data.get("album"),
            "url": url,
            "duration": data.get("duration"),
            "stream_url": stream_data.get("mp3_url"),
            "lyrics": data.get("lyrics"),
            "tags": data.get("tags", []),
            "price": stream_data.get("price"),
            "currency": stream_data.get("currency"),
            "free": stream_data.get("free", False),
        }
        
        return Track(track_info)
    
    # Search methods
    
    async def search(
        self,
        query: str,
        search_type: str = "all",
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search Bandcamp.
        
        Args:
            query: Search query
            search_type: Type to search ("all", "artists", "albums", "tracks")
            page: Page number
            
        Returns:
            List of search results
        """
        if not self.config.enable_search:
            raise BandcampError("Search is disabled")
        
        return await self._search_scraper.search(query, search_type, page)
    
    async def search_albums(self, query: str, page: int = 1) -> List[SearchResult]:
        """Search for albums."""
        return await self.search(query, "albums", page)
    
    async def search_artists(self, query: str, page: int = 1) -> List[SearchResult]:
        """Search for artists."""
        return await self.search(query, "artists", page)
    
    async def search_tracks(self, query: str, page: int = 1) -> List[SearchResult]:
        """Search for tracks."""
        return await self.search(query, "tracks", page)
    
    # Download methods
    
    async def download_album(
        self,
        album: Union[Album, str],
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> List[str]:
        """
        Download an album.
        
        Args:
            album: Album object or URL
            output_dir: Output directory
            options: Download options
            
        Returns:
            List of downloaded file paths
        """
        if not self.config.enable_downloads or not self._download_manager:
            raise BandcampError("Downloads are disabled")
        
        # Get album object if URL provided
        if isinstance(album, str):
            album = await self.get_album(album)
        
        return await self._download_manager.download_album(album, output_dir, options)
    
    async def download_track(
        self,
        track: Union[Track, str],
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> str:
        """
        Download a track.
        
        Args:
            track: Track object or URL
            output_dir: Output directory
            options: Download options
            
        Returns:
            Path to downloaded file
        """
        if not self.config.enable_downloads or not self._download_manager:
            raise BandcampError("Downloads are disabled")
        
        # Get track object if URL provided
        if isinstance(track, str):
            track = await self.get_track(track)
        
        return await self._download_manager.download_track(track, output_dir, options)
    
    # Utility methods
    
    async def get_from_url(self, url: str) -> Union[Album, Track, None]:
        """
        Get album or track from URL.
        
        Args:
            url: Bandcamp URL
            
        Returns:
            Album, Track, or None
        """
        if not is_bandcamp_url(url):
            raise InvalidURLError(f"Not a Bandcamp URL: {url}")
        
        url_type, _, _ = parse_bandcamp_url(url)
        
        if url_type == "album":
            return await self.get_album(url)
        elif url_type == "track":
            return await self.get_track(url)
        else:
            return None


__all__ = ["BandcampClient"]