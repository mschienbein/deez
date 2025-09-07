"""
Beatport API client.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from .config import BeatportConfig
from .auth import BeatportAuth
from .models import Track, Release, Artist, Label, Genre, Chart
from .exceptions import (
    BeatportError,
    APIError,
    RateLimitError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)


class BeatportClient:
    """Main client for Beatport API integration."""
    
    def __init__(
        self,
        config: Optional[BeatportConfig] = None,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Beatport client.
        
        Args:
            config: Optional configuration
            session: Optional aiohttp session
        """
        self.config = config or BeatportConfig.from_env()
        self._session = session
        self._owns_session = session is None
        self._auth = None
        self._last_request_time = 0
    
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
            timeout = ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        
        # Initialize auth handler
        self._auth = BeatportAuth(self.config, self._session)
        
        # Authenticate
        try:
            await self._auth.authenticate()
            logger.info("Beatport client initialized and authenticated")
        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            raise
    
    async def close(self):
        """Close the client and cleanup resources."""
        if self._owns_session and self._session:
            await self._session.close()
        logger.info("Beatport client closed")
    
    # Search methods
    
    async def search(
        self,
        query: str,
        type: str = "tracks",
        page: int = 1,
        per_page: int = 25,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search Beatport catalog.
        
        Args:
            query: Search query
            type: Search type (tracks, releases, artists, labels)
            page: Page number
            per_page: Results per page
            **kwargs: Additional search parameters
            
        Returns:
            Search results
        """
        params = {
            "q": query,
            "page": page,
            "per_page": per_page,
            **kwargs
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        endpoint = f"/catalog/{type}/"
        return await self._request("GET", endpoint, params=params)
    
    async def search_tracks(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25,
        **kwargs
    ) -> List[Track]:
        """
        Search for tracks.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            **kwargs: Additional filters (genre_id, label_id, etc.)
            
        Returns:
            List of tracks
        """
        results = await self.search(query, "tracks", page, per_page, **kwargs)
        tracks = results.get("results", [])
        return [Track.from_api(t) for t in tracks]
    
    async def search_releases(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25,
        **kwargs
    ) -> List[Release]:
        """
        Search for releases.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            **kwargs: Additional filters
            
        Returns:
            List of releases
        """
        results = await self.search(query, "releases", page, per_page, **kwargs)
        releases = results.get("results", [])
        return [Release.from_api(r) for r in releases]
    
    async def search_artists(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25
    ) -> List[Artist]:
        """
        Search for artists.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            List of artists
        """
        results = await self.search(query, "artists", page, per_page)
        artists = results.get("results", [])
        return [Artist.from_api(a) for a in artists]
    
    async def search_labels(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25
    ) -> List[Label]:
        """
        Search for labels.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            List of labels
        """
        results = await self.search(query, "labels", page, per_page)
        labels = results.get("results", [])
        return [Label.from_api(l) for l in labels]
    
    # Get specific items
    
    async def get_track(self, track_id: int) -> Track:
        """
        Get track by ID.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track object
        """
        endpoint = f"/catalog/tracks/{track_id}/"
        data = await self._request("GET", endpoint)
        return Track.from_api(data)
    
    async def get_release(self, release_id: int) -> Release:
        """
        Get release by ID.
        
        Args:
            release_id: Release ID
            
        Returns:
            Release object
        """
        endpoint = f"/catalog/releases/{release_id}/"
        data = await self._request("GET", endpoint)
        return Release.from_api(data)
    
    async def get_artist(self, artist_id: int) -> Artist:
        """
        Get artist by ID.
        
        Args:
            artist_id: Artist ID
            
        Returns:
            Artist object
        """
        endpoint = f"/catalog/artists/{artist_id}/"
        data = await self._request("GET", endpoint)
        return Artist.from_api(data)
    
    async def get_label(self, label_id: int) -> Label:
        """
        Get label by ID.
        
        Args:
            label_id: Label ID
            
        Returns:
            Label object
        """
        endpoint = f"/catalog/labels/{label_id}/"
        data = await self._request("GET", endpoint)
        return Label.from_api(data)
    
    # Charts
    
    async def get_charts(
        self,
        genre_id: Optional[int] = None,
        type: str = "top-100"
    ) -> List[Track]:
        """
        Get Beatport charts.
        
        Args:
            genre_id: Optional genre ID to filter by
            type: Chart type (top-100, top-10, hype, etc.)
            
        Returns:
            List of tracks
        """
        endpoint = "/catalog/charts/"
        params = {
            "chart_type": type,
        }
        
        if genre_id:
            params["genre_id"] = genre_id
        
        data = await self._request("GET", endpoint, params=params)
        tracks = data.get("results", [])
        return [Track.from_api(t) for t in tracks]
    
    async def get_top_100(self, genre_id: Optional[int] = None) -> List[Track]:
        """
        Get top 100 tracks.
        
        Args:
            genre_id: Optional genre ID to filter by
            
        Returns:
            List of top 100 tracks
        """
        return await self.get_charts(genre_id, "top-100")
    
    async def get_hype_tracks(self, genre_id: Optional[int] = None) -> List[Track]:
        """
        Get hype (trending) tracks.
        
        Args:
            genre_id: Optional genre ID to filter by
            
        Returns:
            List of hype tracks
        """
        return await self.get_charts(genre_id, "hype")
    
    # Genres
    
    async def get_genres(self) -> List[Genre]:
        """
        Get all genres.
        
        Returns:
            List of genres
        """
        endpoint = "/catalog/genres/"
        data = await self._request("GET", endpoint)
        genres = data.get("results", [])
        return [Genre.from_api(g) for g in genres]
    
    async def get_genre(self, genre_id: int) -> Genre:
        """
        Get genre by ID.
        
        Args:
            genre_id: Genre ID
            
        Returns:
            Genre object
        """
        endpoint = f"/catalog/genres/{genre_id}/"
        data = await self._request("GET", endpoint)
        return Genre.from_api(data)
    
    # Artist methods
    
    async def get_artist_tracks(
        self,
        artist_id: int,
        page: int = 1,
        per_page: int = 25
    ) -> List[Track]:
        """
        Get tracks by artist.
        
        Args:
            artist_id: Artist ID
            page: Page number
            per_page: Results per page
            
        Returns:
            List of tracks
        """
        endpoint = f"/catalog/artists/{artist_id}/tracks/"
        params = {
            "page": page,
            "per_page": per_page,
        }
        
        data = await self._request("GET", endpoint, params=params)
        tracks = data.get("results", [])
        return [Track.from_api(t) for t in tracks]
    
    async def get_artist_releases(
        self,
        artist_id: int,
        page: int = 1,
        per_page: int = 25
    ) -> List[Release]:
        """
        Get releases by artist.
        
        Args:
            artist_id: Artist ID
            page: Page number
            per_page: Results per page
            
        Returns:
            List of releases
        """
        endpoint = f"/catalog/artists/{artist_id}/releases/"
        params = {
            "page": page,
            "per_page": per_page,
        }
        
        data = await self._request("GET", endpoint, params=params)
        releases = data.get("results", [])
        return [Release.from_api(r) for r in releases]
    
    # Label methods
    
    async def get_label_tracks(
        self,
        label_id: int,
        page: int = 1,
        per_page: int = 25
    ) -> List[Track]:
        """
        Get tracks by label.
        
        Args:
            label_id: Label ID
            page: Page number
            per_page: Results per page
            
        Returns:
            List of tracks
        """
        endpoint = f"/catalog/labels/{label_id}/tracks/"
        params = {
            "page": page,
            "per_page": per_page,
        }
        
        data = await self._request("GET", endpoint, params=params)
        tracks = data.get("results", [])
        return [Track.from_api(t) for t in tracks]
    
    async def get_label_releases(
        self,
        label_id: int,
        page: int = 1,
        per_page: int = 25
    ) -> List[Release]:
        """
        Get releases by label.
        
        Args:
            label_id: Label ID
            page: Page number
            per_page: Results per page
            
        Returns:
            List of releases
        """
        endpoint = f"/catalog/labels/{label_id}/releases/"
        params = {
            "page": page,
            "per_page": per_page,
        }
        
        data = await self._request("GET", endpoint, params=params)
        releases = data.get("results", [])
        return [Release.from_api(r) for r in releases]
    
    # Private methods
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            **kwargs: Additional request arguments
            
        Returns:
            API response data
        """
        # Apply rate limiting
        await self._apply_rate_limit()
        
        # Ensure authenticated
        access_token = await self._auth.ensure_authenticated()
        
        # Build URL
        url = f"{self.config.base_url}{endpoint}"
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        
        if data:
            headers["Content-Type"] = "application/json"
        
        # Make request
        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(
                    method,
                    url,
                    params=params,
                    json=data,
                    headers=headers,
                    **kwargs
                ) as response:
                    # Check for rate limiting
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise RateLimitError(
                            f"Rate limit exceeded, retry after {retry_after} seconds",
                            retry_after=retry_after
                        )
                    
                    # Check for auth errors
                    if response.status == 401:
                        # Try to re-authenticate once
                        if attempt == 0:
                            await self._auth.authenticate()
                            continue
                        raise AuthenticationError("Authentication failed")
                    
                    # Check for other errors
                    if response.status >= 400:
                        error_data = None
                        try:
                            error_data = await response.json()
                        except:
                            pass
                        
                        raise APIError(
                            f"API request failed: {response.status}",
                            status_code=response.status,
                            response_data=error_data
                        )
                    
                    # Parse response
                    return await response.json()
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise BeatportError(f"Request failed after {self.config.max_retries} attempts: {e}")
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        import time
        
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - time_since_last)
        
        self._last_request_time = time.time()


__all__ = ["BeatportClient"]