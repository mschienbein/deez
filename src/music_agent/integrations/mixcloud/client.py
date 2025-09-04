"""
Main Mixcloud client.

Provides high-level interface for interacting with Mixcloud.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import aiohttp
from aiohttp import ClientSession

from .config import MixcloudConfig
from .auth import AuthenticationManager
from .api import CloudcastsAPI, UsersAPI, SearchAPI, DiscoverAPI
from .download import DownloadManager
from .models import Cloudcast, User, Tag, Category, Playlist
from .types import SearchFilters, DownloadOptions
from .utils import parse_mixcloud_url, is_mixcloud_url
from .exceptions import MixcloudError, NotFoundError

logger = logging.getLogger(__name__)


class MixcloudClient:
    """Main client for interacting with Mixcloud."""
    
    def __init__(
        self,
        config: Optional[MixcloudConfig] = None,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Mixcloud client.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
            session: Optional aiohttp session (creates one if not provided)
        """
        self.config = config or MixcloudConfig.from_env()
        self._session = session
        self._owns_session = session is None
        
        # Initialize components
        self.auth_manager = AuthenticationManager(self.config.auth)
        
        # API clients will be initialized on first use
        self._cloudcasts_api = None
        self._users_api = None
        self._search_api = None
        self._discover_api = None
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
            self._session = aiohttp.ClientSession()
        
        # Initialize auth
        await self.auth_manager.initialize()
        
        # Initialize API clients
        self._cloudcasts_api = CloudcastsAPI(self._session, self.config.api, self.auth_manager)
        self._users_api = UsersAPI(self._session, self.config.api, self.auth_manager)
        self._search_api = SearchAPI(self._session, self.config.api, self.auth_manager)
        self._discover_api = DiscoverAPI(self._session, self.config.api, self.auth_manager)
        
        # Initialize download manager if downloads are enabled
        if self.config.enable_downloads:
            self._download_manager = DownloadManager(self._session, self.config.download)
        
        logger.info("Mixcloud client initialized")
    
    async def close(self):
        """Close the client and cleanup resources."""
        # Close session if we own it
        if self._owns_session and self._session:
            await self._session.close()
        
        logger.info("Mixcloud client closed")
    
    # Authentication methods
    
    async def authenticate(self) -> str:
        """
        Authenticate with Mixcloud.
        
        Returns:
            Access token
        """
        return await self.auth_manager.authenticate_interactive()
    
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.auth_manager.is_authenticated()
    
    # Cloudcast methods
    
    async def get_cloudcast(
        self,
        username: str,
        cloudcast_slug: str
    ) -> Cloudcast:
        """
        Get a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            Cloudcast object
        """
        return await self._cloudcasts_api.get(username, cloudcast_slug)
    
    async def get_cloudcast_from_url(self, url: str) -> Cloudcast:
        """
        Get cloudcast from URL.
        
        Args:
            url: Mixcloud URL
            
        Returns:
            Cloudcast object
        """
        if not is_mixcloud_url(url):
            raise ValueError(f"Invalid Mixcloud URL: {url}")
        
        parsed = parse_mixcloud_url(url)
        if not parsed:
            raise ValueError(f"Could not parse Mixcloud URL: {url}")
        
        username, cloudcast_slug = parsed
        return await self.get_cloudcast(username, cloudcast_slug)
    
    # User methods
    
    async def get_user(self, username: str) -> User:
        """
        Get user information.
        
        Args:
            username: Username
            
        Returns:
            User object
        """
        return await self._users_api.get(username)
    
    async def get_me(self) -> User:
        """
        Get current authenticated user.
        
        Returns:
            User object
        """
        return await self._users_api.get_me()
    
    async def get_user_cloudcasts(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Cloudcast]:
        """
        Get user's cloudcasts.
        
        Args:
            username: Username
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            List of cloudcasts
        """
        result = await self._users_api.get_cloudcasts(username, limit, offset)
        return result.items
    
    async def get_user_favorites(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Cloudcast]:
        """
        Get user's favorites.
        
        Args:
            username: Username
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            List of cloudcasts
        """
        result = await self._users_api.get_favorites(username, limit, offset)
        return result.items
    
    # Search methods
    
    async def search_cloudcasts(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[SearchFilters] = None
    ) -> List[Cloudcast]:
        """
        Search for cloudcasts.
        
        Args:
            query: Search query
            limit: Number of results
            filters: Optional search filters
            
        Returns:
            List of cloudcasts
        """
        result = await self._search_api.search_cloudcasts(query, limit, 0, filters)
        return result.items
    
    async def search_users(
        self,
        query: str,
        limit: int = 20
    ) -> List[User]:
        """
        Search for users.
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of users
        """
        result = await self._search_api.search_users(query, limit)
        return result.items
    
    async def search_tags(
        self,
        query: str,
        limit: int = 20
    ) -> List[Tag]:
        """
        Search for tags.
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            List of tags
        """
        result = await self._search_api.search_tags(query, limit)
        return result.items
    
    # Discovery methods
    
    async def get_popular(self, limit: int = 20) -> List[Cloudcast]:
        """
        Get popular cloudcasts.
        
        Args:
            limit: Number of results
            
        Returns:
            List of cloudcasts
        """
        result = await self._discover_api.get_popular(limit)
        return result.items
    
    async def get_hot(self, limit: int = 20) -> List[Cloudcast]:
        """
        Get hot/trending cloudcasts.
        
        Args:
            limit: Number of results
            
        Returns:
            List of cloudcasts
        """
        result = await self._discover_api.get_hot(limit)
        return result.items
    
    async def get_new(self, limit: int = 20) -> List[Cloudcast]:
        """
        Get new cloudcasts.
        
        Args:
            limit: Number of results
            
        Returns:
            List of cloudcasts
        """
        result = await self._discover_api.get_new(limit)
        return result.items
    
    async def get_categories(self) -> List[Category]:
        """
        Get all categories.
        
        Returns:
            List of categories
        """
        return await self._discover_api.get_categories()
    
    # Download methods
    
    async def download_cloudcast(
        self,
        cloudcast: Union[Cloudcast, str],
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> str:
        """
        Download a cloudcast.
        
        Args:
            cloudcast: Cloudcast object or URL
            output_dir: Optional output directory
            options: Download options
            
        Returns:
            Path to downloaded file
        """
        if not self.config.enable_downloads or not self._download_manager:
            raise MixcloudError("Downloads are not enabled")
        
        # Get cloudcast object if URL provided
        if isinstance(cloudcast, str):
            cloudcast = await self.get_cloudcast_from_url(cloudcast)
        
        return await self._download_manager.download_cloudcast(
            cloudcast,
            output_dir,
            options
        )
    
    async def download_playlist(
        self,
        cloudcasts: List[Union[Cloudcast, str]],
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> List[str]:
        """
        Download multiple cloudcasts.
        
        Args:
            cloudcasts: List of cloudcast objects or URLs
            output_dir: Optional output directory
            options: Download options
            
        Returns:
            List of downloaded file paths
        """
        if not self.config.enable_downloads or not self._download_manager:
            raise MixcloudError("Downloads are not enabled")
        
        # Convert URLs to cloudcast objects
        cloudcast_objects = []
        for item in cloudcasts:
            if isinstance(item, str):
                cloudcast_objects.append(await self.get_cloudcast_from_url(item))
            else:
                cloudcast_objects.append(item)
        
        return await self._download_manager.download_playlist(
            cloudcast_objects,
            output_dir,
            options
        )
    
    # Social methods
    
    async def favorite_cloudcast(
        self,
        username: str,
        cloudcast_slug: str
    ) -> bool:
        """
        Favorite a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            True if successful
        """
        return await self._cloudcasts_api.favorite(username, cloudcast_slug)
    
    async def unfavorite_cloudcast(
        self,
        username: str,
        cloudcast_slug: str
    ) -> bool:
        """
        Unfavorite a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            True if successful
        """
        return await self._cloudcasts_api.unfavorite(username, cloudcast_slug)
    
    async def follow_user(self, username: str) -> bool:
        """
        Follow a user.
        
        Args:
            username: Username to follow
            
        Returns:
            True if successful
        """
        return await self._users_api.follow(username)
    
    async def unfollow_user(self, username: str) -> bool:
        """
        Unfollow a user.
        
        Args:
            username: Username to unfollow
            
        Returns:
            True if successful
        """
        return await self._users_api.unfollow(username)


__all__ = ["MixcloudClient"]