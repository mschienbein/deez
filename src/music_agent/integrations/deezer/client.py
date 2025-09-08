"""
Main Deezer client.

Provides high-level interface for interacting with Deezer.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

import aiohttp
from aiohttp import ClientSession

from .config import DeezerConfig
from .auth import AuthenticationManager
from .api import SearchAPI
from .download import DownloadManager
from .models import (
    Track, Album, Artist, Playlist,
    SearchResult, SearchFilters
)
from .exceptions import DeezerError, AuthenticationError

logger = logging.getLogger(__name__)


class DeezerClient:
    """Main client for interacting with Deezer."""
    
    def __init__(
        self,
        config: Optional[DeezerConfig] = None,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Deezer client.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
            session: Optional aiohttp session (creates one if not provided)
        """
        self.config = config or DeezerConfig.from_env()
        self._session = session
        self._owns_session = session is None
        
        # Initialize components
        self.auth_manager = AuthenticationManager(self.config.auth)
        
        # API clients will be initialized on first use
        self._search_api = None
        self._download_manager = None
        self._is_authenticated = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Connect to Deezer and authenticate if credentials available."""
        if self._session is None:
            self._session = ClientSession()
        
        # Initialize API clients
        self._search_api = SearchAPI(self._session, self.config.api, self.auth_manager)
        self._download_manager = DownloadManager(self._session, self.config.download, self.auth_manager)
        
        # Try to authenticate if ARL is available
        if self.config.auth.arl:
            try:
                self._is_authenticated = await self.auth_manager.authenticate(self._session)
                if self._is_authenticated:
                    logger.info("Successfully authenticated with Deezer")
            except AuthenticationError as e:
                logger.warning(f"Authentication failed: {e}")
                # Continue in unauthenticated mode
    
    async def close(self):
        """Close the client and cleanup resources."""
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._is_authenticated
    
    # Search methods
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 25,
        filters: Optional[SearchFilters] = None
    ) -> List[Track]:
        """
        Search for tracks.
        
        Args:
            query: Search query
            limit: Number of results
            filters: Optional search filters
            
        Returns:
            List of tracks
        """
        if not self._search_api:
            await self.connect()
        
        result = await self._search_api.search_tracks(query, limit, 0, filters)
        return result.data
    
    async def search_albums(
        self,
        query: str,
        limit: int = 25
    ) -> List[Album]:
        """
        Search for albums.
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of albums
        """
        if not self._search_api:
            await self.connect()
        
        result = await self._search_api.search_albums(query, limit)
        return result.data
    
    async def search_artists(
        self,
        query: str,
        limit: int = 25
    ) -> List[Artist]:
        """
        Search for artists.
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of artists
        """
        if not self._search_api:
            await self.connect()
        
        result = await self._search_api.search_artists(query, limit)
        return result.data
    
    async def search_playlists(
        self,
        query: str,
        limit: int = 25
    ) -> List[Playlist]:
        """
        Search for playlists.
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of playlists
        """
        if not self._search_api:
            await self.connect()
        
        result = await self._search_api.search_playlists(query, limit)
        return result.data
    
    async def search(
        self,
        query: str,
        search_type: str = "track",
        limit: int = 25,
        filters: Optional[SearchFilters] = None
    ) -> List[Any]:
        """
        Generic search method.
        
        Args:
            query: Search query
            search_type: Type of search (track, album, artist, playlist)
            limit: Number of results
            filters: Optional search filters
            
        Returns:
            List of results
        """
        if search_type == "track":
            return await self.search_tracks(query, limit, filters)
        elif search_type == "album":
            return await self.search_albums(query, limit)
        elif search_type == "artist":
            return await self.search_artists(query, limit)
        elif search_type == "playlist":
            return await self.search_playlists(query, limit)
        else:
            raise ValueError(f"Invalid search type: {search_type}")
    
    # Track methods
    
    async def get_track(self, track_id: str) -> Track:
        """
        Get track details.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track object
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(f"track/{track_id}")
        return Track.from_api(response)
    
    # Album methods
    
    async def get_album(self, album_id: str) -> Album:
        """
        Get album details.
        
        Args:
            album_id: Album ID
            
        Returns:
            Album object
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(f"album/{album_id}")
        return Album.from_api(response)
    
    async def get_album_tracks(self, album_id: str, limit: int = 100) -> List[Track]:
        """
        Get tracks from an album.
        
        Args:
            album_id: Album ID
            limit: Number of tracks
            
        Returns:
            List of tracks
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            f"album/{album_id}/tracks",
            params={"limit": limit}
        )
        
        return [Track.from_api(item) for item in response.get("data", [])]
    
    # Artist methods
    
    async def get_artist(self, artist_id: str) -> Artist:
        """
        Get artist details.
        
        Args:
            artist_id: Artist ID
            
        Returns:
            Artist object
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(f"artist/{artist_id}")
        return Artist.from_api(response)
    
    async def get_artist_top(self, artist_id: str, limit: int = 10) -> List[Track]:
        """
        Get artist's top tracks.
        
        Args:
            artist_id: Artist ID
            limit: Number of tracks
            
        Returns:
            List of top tracks
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            f"artist/{artist_id}/top",
            params={"limit": limit}
        )
        
        return [Track.from_api(item) for item in response.get("data", [])]
    
    async def get_artist_albums(self, artist_id: str, limit: int = 50) -> List[Album]:
        """
        Get artist's albums.
        
        Args:
            artist_id: Artist ID
            limit: Number of albums
            
        Returns:
            List of albums
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            f"artist/{artist_id}/albums",
            params={"limit": limit}
        )
        
        return [Album.from_api(item) for item in response.get("data", [])]
    
    # Playlist methods
    
    async def get_playlist(self, playlist_id: str) -> Playlist:
        """
        Get playlist details.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            Playlist object
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(f"playlist/{playlist_id}")
        return Playlist.from_api(response)
    
    async def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        """
        Get tracks from a playlist.
        
        Args:
            playlist_id: Playlist ID
            limit: Number of tracks
            
        Returns:
            List of tracks
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            f"playlist/{playlist_id}/tracks",
            params={"limit": limit}
        )
        
        return [Track.from_api(item) for item in response.get("data", [])]
    
    # Charts methods
    
    async def get_chart_tracks(self, limit: int = 50) -> List[Track]:
        """
        Get chart tracks.
        
        Args:
            limit: Number of tracks
            
        Returns:
            List of chart tracks
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            "chart/0/tracks",
            params={"limit": limit}
        )
        
        return [Track.from_api(item) for item in response.get("data", [])]
    
    async def get_chart_albums(self, limit: int = 50) -> List[Album]:
        """
        Get chart albums.
        
        Args:
            limit: Number of albums
            
        Returns:
            List of chart albums
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            "chart/0/albums",
            params={"limit": limit}
        )
        
        return [Album.from_api(item) for item in response.get("data", [])]
    
    async def get_chart_artists(self, limit: int = 50) -> List[Artist]:
        """
        Get chart artists.
        
        Args:
            limit: Number of artists
            
        Returns:
            List of chart artists
        """
        if not self._search_api:
            await self.connect()
        
        response = await self._search_api.get(
            "chart/0/artists",
            params={"limit": limit}
        )
        
        return [Artist.from_api(item) for item in response.get("data", [])]
    
    # Download methods
    
    async def download_track(
        self,
        track: Track,
        output_path: Optional[Path] = None,
        quality: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Path:
        """
        Download a track.
        
        Args:
            track: Track to download
            output_path: Optional output path
            quality: Desired quality (FLAC, MP3_320, MP3_128)
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
            AuthenticationError: If not authenticated
        """
        if not self._is_authenticated:
            raise AuthenticationError("Authentication required for downloads")
        
        if not self._download_manager:
            await self.connect()
        
        return await self._download_manager.download_track(
            track, output_path, quality, progress_callback
        )
    
    async def download_album(
        self,
        album_id: str,
        output_dir: Optional[Path] = None,
        quality: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[Path]:
        """
        Download an entire album.
        
        Args:
            album_id: Album ID
            output_dir: Optional output directory
            quality: Desired quality
            progress_callback: Progress callback
            
        Returns:
            List of paths to downloaded files
        """
        if not self._is_authenticated:
            raise AuthenticationError("Authentication required for downloads")
        
        # Get album tracks
        tracks = await self.get_album_tracks(album_id)
        
        # Download each track
        downloaded = []
        for i, track in enumerate(tracks):
            if progress_callback:
                # Update progress for album
                progress_callback(i + 1, len(tracks), track.title)
            
            try:
                path = await self.download_track(track, quality=quality)
                downloaded.append(path)
            except Exception as e:
                logger.error(f"Failed to download {track.title}: {e}")
        
        return downloaded
    
    async def download_playlist(
        self,
        playlist_id: str,
        output_dir: Optional[Path] = None,
        quality: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[Path]:
        """
        Download an entire playlist.
        
        Args:
            playlist_id: Playlist ID
            output_dir: Optional output directory
            quality: Desired quality
            progress_callback: Progress callback
            
        Returns:
            List of paths to downloaded files
        """
        if not self._is_authenticated:
            raise AuthenticationError("Authentication required for downloads")
        
        # Get playlist tracks
        tracks = await self.get_playlist_tracks(playlist_id)
        
        # Download each track
        downloaded = []
        for i, track in enumerate(tracks):
            if progress_callback:
                # Update progress for playlist
                progress_callback(i + 1, len(tracks), track.title)
            
            try:
                path = await self.download_track(track, quality=quality)
                downloaded.append(path)
            except Exception as e:
                logger.error(f"Failed to download {track.title}: {e}")
        
        return downloaded
    
    async def get_download_info(
        self,
        track: Track,
        quality: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get download information for a track without downloading.
        
        Args:
            track: Track object
            quality: Desired quality
            
        Returns:
            Download information including URL and format
        """
        if not self._is_authenticated:
            raise AuthenticationError("Authentication required for download info")
        
        if not self._download_manager:
            await self.connect()
        
        return await self._download_manager.get_track_download_info(track, quality)