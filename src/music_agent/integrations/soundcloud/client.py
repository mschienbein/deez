"""
Main SoundCloud client implementation.

Coordinates all components and provides the main interface.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

import aiohttp

from .config import SoundCloudConfig
from .auth import AuthenticationManager
from .types import AuthCredentials
from .cache import CacheManager, InMemoryCache
from .search import SearchManager
from .download import DownloadManager
from .utils import RateLimiter
from .exceptions import (
    SoundCloudError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ServerError,
)

# Import API modules
from . import api

logger = logging.getLogger(__name__)


class SoundCloudClient:
    """Main SoundCloud client."""
    
    def __init__(
        self,
        config: Optional[SoundCloudConfig] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Initialize SoundCloud client.
        
        Args:
            config: Configuration object
            session: Optional aiohttp session
        """
        self.config = config or SoundCloudConfig()
        
        # HTTP session
        self._session = session
        self._owns_session = session is None
        
        # Components
        self.auth = AuthenticationManager(config.auth)
        self.cache = CacheManager(
            backend=InMemoryCache() if config.cache.enabled else None,
            default_ttl=config.cache.default_ttl
        )
        self.search = SearchManager(self, self.cache)
        self.download = DownloadManager(self, config.download)
        self.rate_limiter = RateLimiter(
            max_requests=config.api.rate_limit,
            time_window=1
        )
        
        # API modules
        self.tracks = api.tracks
        self.playlists = api.playlists
        self.users = api.users
        self.resolve = api.resolve
        
        # State
        self.client_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self.user_id: Optional[int] = None
        
        # API endpoints
        self.base_url = "https://api.soundcloud.com"
        self.base_url_v2 = "https://api-v2.soundcloud.com"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize client and authenticate."""
        # Create session if needed
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.api.timeout),
                headers={
                    "User-Agent": self.config.api.user_agent,
                    "Accept": "application/json",
                }
            )
        
        self.session = self._session
        
        # Authenticate
        if not await self.authenticate():
            raise AuthenticationError("Failed to authenticate with SoundCloud")
    
    async def close(self):
        """Close client and clean up resources."""
        # Close session if we own it
        if self._owns_session and self._session:
            await self._session.close()
        
        # Clean up cache
        if isinstance(self.cache.backend, InMemoryCache):
            del self.cache.backend
    
    async def authenticate(
        self,
        credentials: Optional[AuthCredentials] = None
    ) -> bool:
        """
        Authenticate with SoundCloud.
        
        Args:
            credentials: Optional authentication credentials
            
        Returns:
            True if authenticated
        """
        # Try provided credentials
        if credentials:
            success = await self.auth.authenticate(credentials)
            if success:
                self.access_token = self.auth.access_token
                self.client_id = self.auth.client_id
                return True
        
        # Try stored credentials
        if self.auth.has_stored_credentials():
            success = await self.auth.authenticate()
            if success:
                self.access_token = self.auth.access_token
                self.client_id = self.auth.client_id
                return True
        
        # Fall back to client ID scraping
        client_id = await self.auth.get_client_id()
        if client_id:
            self.client_id = client_id
            return True
        
        return False
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        api_version: str = "v1"
    ) -> Any:
        """
        Make API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            data: Form data
            api_version: API version (v1 or v2)
            
        Returns:
            Response data
        """
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Build URL
        base_url = self.base_url if api_version == "v1" else self.base_url_v2
        url = f"{base_url}{endpoint}"
        
        # Add authentication
        if params is None:
            params = {}
        
        if self.access_token:
            # OAuth authentication
            headers = {"Authorization": f"OAuth {self.access_token}"}
        else:
            # Client ID authentication
            params["client_id"] = self.client_id
            headers = {}
        
        # Make request
        try:
            async with self.session.request(
                method,
                url,
                params=params,
                json=json,
                data=data,
                headers=headers
            ) as response:
                # Check for rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(f"Rate limited, retry after {retry_after}s")
                
                # Check for errors
                if response.status >= 400:
                    error_data = await response.json()
                    self._handle_api_error(response.status, error_data)
                
                # Return response data
                if response.content_type == "application/json":
                    return await response.json()
                else:
                    return await response.text()
                    
        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {e}")
    
    def _handle_api_error(self, status: int, error_data: Dict[str, Any]):
        """Handle API error response."""
        from .utils.parsers import parse_api_error
        
        error_code, error_message = parse_api_error(error_data)
        
        if status == 401:
            raise AuthenticationError(error_message)
        elif status == 403:
            from .exceptions import ForbiddenError
            raise ForbiddenError(error_message)
        elif status == 404:
            from .exceptions import NotFoundError
            raise NotFoundError(error_message)
        elif status >= 500:
            raise ServerError(error_message)
        else:
            raise APIError(f"API error {status}: {error_message}")
    
    # High-level methods
    
    async def get_track(self, track_id: Union[int, str]) -> "Track":
        """
        Get a track by ID or URL.
        
        Args:
            track_id: Track ID or URL
            
        Returns:
            Track object
        """
        from .models.track import Track
        
        # Handle URL
        if isinstance(track_id, str) and track_id.startswith("http"):
            resolved = await self.resolve.resolve(self, track_id)
            if isinstance(resolved, Track):
                return resolved
            raise ValueError(f"URL does not resolve to a track: {track_id}")
        
        return await self.tracks.get_track(self, int(track_id))
    
    async def get_playlist(self, playlist_id: Union[int, str]) -> "Playlist":
        """
        Get a playlist by ID or URL.
        
        Args:
            playlist_id: Playlist ID or URL
            
        Returns:
            Playlist object
        """
        from .models.playlist import Playlist
        
        # Handle URL
        if isinstance(playlist_id, str) and playlist_id.startswith("http"):
            resolved = await self.resolve.resolve(self, playlist_id)
            if isinstance(resolved, Playlist):
                return resolved
            raise ValueError(f"URL does not resolve to a playlist: {playlist_id}")
        
        return await self.playlists.get_playlist(self, int(playlist_id))
    
    async def get_user(self, user_id: Union[int, str]) -> "User":
        """
        Get a user by ID or URL.
        
        Args:
            user_id: User ID or URL
            
        Returns:
            User object
        """
        from .models.user import User
        
        # Handle URL
        if isinstance(user_id, str) and user_id.startswith("http"):
            resolved = await self.resolve.resolve(self, user_id)
            if isinstance(resolved, User):
                return resolved
            raise ValueError(f"URL does not resolve to a user: {user_id}")
        
        return await self.users.get_user(self, int(user_id))
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 50,
        **kwargs
    ) -> List["Track"]:
        """
        Search for tracks.
        
        Args:
            query: Search query
            limit: Maximum results
            **kwargs: Additional search options
            
        Returns:
            List of tracks
        """
        return await self.search.search(query, "tracks", limit, **kwargs)
    
    async def search_playlists(
        self,
        query: str,
        limit: int = 50,
        **kwargs
    ) -> List["Playlist"]:
        """
        Search for playlists.
        
        Args:
            query: Search query
            limit: Maximum results
            **kwargs: Additional search options
            
        Returns:
            List of playlists
        """
        return await self.search.search(query, "playlists", limit, **kwargs)
    
    async def search_users(
        self,
        query: str,
        limit: int = 50,
        **kwargs
    ) -> List["User"]:
        """
        Search for users.
        
        Args:
            query: Search query
            limit: Maximum results
            **kwargs: Additional search options
            
        Returns:
            List of users
        """
        return await self.search.search(query, "users", limit, **kwargs)
    
    async def download_track(
        self,
        track: Union["Track", int, str],
        output_dir: Optional[str] = None,
        **options
    ) -> Path:
        """
        Download a track.
        
        Args:
            track: Track object, ID, or URL
            output_dir: Output directory
            **options: Download options
            
        Returns:
            Path to downloaded file
        """
        # Get track object if needed
        if not hasattr(track, "download"):
            track = await self.get_track(track)
        
        # Set output directory
        if output_dir:
            options["output_path"] = Path(output_dir) / f"{track.artist} - {track.title}.mp3"
        
        return await self.download.download_track(track, options)
    
    async def download_playlist(
        self,
        playlist: Union["Playlist", int, str],
        output_dir: Optional[str] = None,
        **options
    ) -> List[Path]:
        """
        Download a playlist.
        
        Args:
            playlist: Playlist object, ID, or URL
            output_dir: Output directory
            **options: Download options
            
        Returns:
            List of downloaded file paths
        """
        # Get playlist object if needed
        if not hasattr(playlist, "tracks"):
            playlist = await self.get_playlist(playlist)
        
        return await self.download.download_playlist(
            playlist,
            output_dir,
            options
        )
    
    async def get_stream(self, limit: int = 50) -> List[Any]:
        """
        Get authenticated user's stream.
        
        Args:
            limit: Maximum items
            
        Returns:
            List of stream items
        """
        from .api import stream
        return await stream.get_stream(self, limit)
    
    async def get_me(self) -> "User":
        """
        Get authenticated user.
        
        Returns:
            User object
        """
        return await self.users.get_me(self)


def create_client(
    client_id: Optional[str] = None,
    access_token: Optional[str] = None,
    **config_kwargs
) -> SoundCloudClient:
    """
    Create SoundCloud client with credentials.
    
    Args:
        client_id: Optional client ID
        access_token: Optional access token
        **config_kwargs: Configuration options
        
    Returns:
        SoundCloud client
    """
    config = SoundCloudConfig(**config_kwargs)
    
    # Set credentials if provided
    if client_id:
        config.auth.client_id = client_id
    if access_token:
        config.auth.access_token = access_token
    
    return SoundCloudClient(config)


__all__ = ["SoundCloudClient", "create_client"]