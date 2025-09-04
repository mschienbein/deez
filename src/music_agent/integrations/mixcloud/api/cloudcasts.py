"""
Cloudcast API endpoints for Mixcloud.

Handles cloudcast-related operations.
"""

import logging
from typing import Optional, Dict, Any, List

from .base import BaseAPI
from ..models import Cloudcast, Comment, PaginatedResult
from ..exceptions import NotFoundError, APIError

logger = logging.getLogger(__name__)


class CloudcastsAPI(BaseAPI):
    """API client for cloudcast operations."""
    
    async def get(self, username: str, cloudcast_slug: str) -> Cloudcast:
        """
        Get a specific cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug/identifier
            
        Returns:
            Cloudcast object
        """
        endpoint = f"{username}/{cloudcast_slug}"
        
        try:
            data = await self._get(endpoint)
            return Cloudcast(data)
        except NotFoundError:
            raise NotFoundError(f"Cloudcast not found: {username}/{cloudcast_slug}")
    
    async def get_by_key(self, key: str) -> Cloudcast:
        """
        Get cloudcast by key.
        
        Args:
            key: Cloudcast key (e.g., "/username/cloudcast-name/")
            
        Returns:
            Cloudcast object
        """
        # Remove leading/trailing slashes
        key = key.strip("/")
        
        try:
            data = await self._get(key)
            return Cloudcast(data)
        except NotFoundError:
            raise NotFoundError(f"Cloudcast not found: {key}")
    
    async def get_stream_info(self, username: str, cloudcast_slug: str) -> Dict[str, Any]:
        """
        Get stream information for a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            Stream information dictionary
        """
        # Get cloudcast first
        cloudcast = await self.get(username, cloudcast_slug)
        
        # Check for stream URL in embed endpoint
        embed_endpoint = f"{username}/{cloudcast_slug}/embed-json/"
        
        try:
            embed_data = await self._get(embed_endpoint)
            
            # Extract stream info
            stream_info = {
                "stream_url": embed_data.get("stream_url"),
                "preview_url": embed_data.get("preview_url"),
                "download_url": cloudcast.download_url,
                "duration": cloudcast.duration_seconds,
                "is_exclusive": cloudcast.is_exclusive,
                "is_select": cloudcast.is_select,
            }
            
            # Add HLS info if available
            if "hls_url" in embed_data:
                stream_info["hls_url"] = embed_data["hls_url"]
            
            return stream_info
            
        except Exception as e:
            logger.warning(f"Could not get embed info: {e}")
            return cloudcast.get_stream_info()
    
    async def get_comments(
        self,
        username: str,
        cloudcast_slug: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get comments for a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            limit: Number of comments to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated comments
        """
        endpoint = f"{username}/{cloudcast_slug}/comments/"
        
        return await self._get_paginated(
            endpoint,
            Comment,
            limit=limit,
            offset=offset
        )
    
    async def get_favorites(
        self,
        username: str,
        cloudcast_slug: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get users who favorited a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            limit: Number of users to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated users
        """
        from ..models import User
        
        endpoint = f"{username}/{cloudcast_slug}/favorites/"
        
        return await self._get_paginated(
            endpoint,
            User,
            limit=limit,
            offset=offset
        )
    
    async def get_listeners(
        self,
        username: str,
        cloudcast_slug: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get users who listened to a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            limit: Number of users to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated users
        """
        from ..models import User
        
        endpoint = f"{username}/{cloudcast_slug}/listeners/"
        
        return await self._get_paginated(
            endpoint,
            User,
            limit=limit,
            offset=offset
        )
    
    async def get_similar(
        self,
        username: str,
        cloudcast_slug: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get similar cloudcasts.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = f"{username}/{cloudcast_slug}/similar/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def favorite(self, username: str, cloudcast_slug: str) -> bool:
        """
        Favorite a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/{cloudcast_slug}/favorite/"
        
        try:
            await self._post(endpoint)
            logger.info(f"Favorited cloudcast: {username}/{cloudcast_slug}")
            return True
        except APIError as e:
            logger.error(f"Failed to favorite cloudcast: {e}")
            return False
    
    async def unfavorite(self, username: str, cloudcast_slug: str) -> bool:
        """
        Unfavorite a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/{cloudcast_slug}/favorite/"
        
        try:
            await self._delete(endpoint)
            logger.info(f"Unfavorited cloudcast: {username}/{cloudcast_slug}")
            return True
        except APIError as e:
            logger.error(f"Failed to unfavorite cloudcast: {e}")
            return False
    
    async def repost(self, username: str, cloudcast_slug: str) -> bool:
        """
        Repost a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/{cloudcast_slug}/repost/"
        
        try:
            await self._post(endpoint)
            logger.info(f"Reposted cloudcast: {username}/{cloudcast_slug}")
            return True
        except APIError as e:
            logger.error(f"Failed to repost cloudcast: {e}")
            return False
    
    async def unrepost(self, username: str, cloudcast_slug: str) -> bool:
        """
        Remove a repost.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/{cloudcast_slug}/repost/"
        
        try:
            await self._delete(endpoint)
            logger.info(f"Removed repost: {username}/{cloudcast_slug}")
            return True
        except APIError as e:
            logger.error(f"Failed to remove repost: {e}")
            return False
    
    async def add_comment(
        self,
        username: str,
        cloudcast_slug: str,
        comment: str,
        time: Optional[int] = None
    ) -> bool:
        """
        Add a comment to a cloudcast.
        
        Args:
            username: Username of cloudcast owner
            cloudcast_slug: Cloudcast slug
            comment: Comment text
            time: Optional timestamp in seconds for timed comment
            
        Returns:
            True if successful
        """
        endpoint = f"{username}/{cloudcast_slug}/comments/"
        
        data = {"comment": comment}
        if time is not None:
            data["time"] = time
        
        try:
            await self._post(endpoint, data=data)
            logger.info(f"Added comment to cloudcast: {username}/{cloudcast_slug}")
            return True
        except APIError as e:
            logger.error(f"Failed to add comment: {e}")
            return False


__all__ = ["CloudcastsAPI"]