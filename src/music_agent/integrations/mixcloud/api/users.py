"""
User API endpoints for Mixcloud.

Handles user-related operations.
"""

import logging
from typing import Optional, Dict, Any

from .base import BaseAPI
from ..models import User, Cloudcast, Playlist, PaginatedResult
from ..exceptions import NotFoundError, APIError

logger = logging.getLogger(__name__)


class UsersAPI(BaseAPI):
    """API client for user operations."""
    
    async def get(self, username: str) -> User:
        """
        Get user information.
        
        Args:
            username: Username to fetch
            
        Returns:
            User object
        """
        endpoint = username
        
        try:
            data = await self._get(endpoint)
            return User(data)
        except NotFoundError:
            raise NotFoundError(f"User not found: {username}")
    
    async def get_me(self) -> User:
        """
        Get current authenticated user.
        
        Returns:
            User object for authenticated user
        """
        endpoint = "me/"
        
        try:
            data = await self._get(endpoint, authenticated=True)
            return User(data)
        except APIError as e:
            logger.error(f"Failed to get current user: {e}")
            raise
    
    async def get_cloudcasts(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0,
        order_by: Optional[str] = None
    ) -> PaginatedResult:
        """
        Get user's cloudcasts.
        
        Args:
            username: Username
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            order_by: Order by field (e.g., "created_time", "play_count")
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = f"{username}/cloudcasts/"
        
        params = {}
        if order_by:
            params["order_by"] = order_by
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            params=params,
            limit=limit,
            offset=offset
        )
    
    async def get_favorites(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get user's favorite cloudcasts.
        
        Args:
            username: Username
            limit: Number of favorites to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated favorite cloudcasts
        """
        endpoint = f"{username}/favorites/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_listens(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get user's listening history.
        
        Args:
            username: Username
            limit: Number of listens to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = f"{username}/listens/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_playlists(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get user's playlists.
        
        Args:
            username: Username
            limit: Number of playlists to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated playlists
        """
        endpoint = f"{username}/playlists/"
        
        return await self._get_paginated(
            endpoint,
            Playlist,
            limit=limit,
            offset=offset
        )
    
    async def get_followers(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get user's followers.
        
        Args:
            username: Username
            limit: Number of followers to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated users
        """
        endpoint = f"{username}/followers/"
        
        return await self._get_paginated(
            endpoint,
            User,
            limit=limit,
            offset=offset
        )
    
    async def get_following(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get users that this user follows.
        
        Args:
            username: Username
            limit: Number of users to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated users
        """
        endpoint = f"{username}/following/"
        
        return await self._get_paginated(
            endpoint,
            User,
            limit=limit,
            offset=offset
        )
    
    async def get_feed(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get user's feed (activity from followed users).
        
        Args:
            username: Username
            limit: Number of items to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated feed items
        """
        endpoint = f"{username}/feed/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_uploads(
        self,
        username: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get user's uploads (alias for cloudcasts).
        
        Args:
            username: Username
            limit: Number of uploads to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        return await self.get_cloudcasts(username, limit, offset)
    
    async def follow(self, username: str) -> bool:
        """
        Follow a user.
        
        Args:
            username: Username to follow
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/follow/"
        
        try:
            await self._post(endpoint)
            logger.info(f"Followed user: {username}")
            return True
        except APIError as e:
            logger.error(f"Failed to follow user: {e}")
            return False
    
    async def unfollow(self, username: str) -> bool:
        """
        Unfollow a user.
        
        Args:
            username: Username to unfollow
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/follow/"
        
        try:
            await self._delete(endpoint)
            logger.info(f"Unfollowed user: {username}")
            return True
        except APIError as e:
            logger.error(f"Failed to unfollow user: {e}")
            return False
    
    async def get_stats(self, username: str) -> Dict[str, int]:
        """
        Get detailed user statistics.
        
        Args:
            username: Username
            
        Returns:
            Dictionary with user statistics
        """
        user = await self.get(username)
        return user.get_stats()


__all__ = ["UsersAPI"]