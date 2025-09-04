"""
Discovery API endpoints for Mixcloud.

Handles discovery of popular, trending, and featured content.
"""

import logging
from typing import Optional, Dict, Any, List

from .base import BaseAPI
from ..models import Cloudcast, User, Tag, Category, PaginatedResult
from ..exceptions import APIError

logger = logging.getLogger(__name__)


class DiscoverAPI(BaseAPI):
    """API client for discovery operations."""
    
    async def get_popular(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get popular cloudcasts.
        
        Args:
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = "popular/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_hot(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get hot/trending cloudcasts.
        
        Args:
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = "popular/hot/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_new(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get new/recent cloudcasts.
        
        Args:
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = "new/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_featured(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get featured cloudcasts.
        
        Args:
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = "featured/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_categories(self) -> List[Category]:
        """
        Get all categories.
        
        Returns:
            List of categories
        """
        endpoint = "categories/"
        
        try:
            data = await self._get(endpoint)
            
            categories = []
            results_key = "data" if "data" in data else "results"
            if results_key in data:
                for cat_data in data[results_key]:
                    categories.append(Category(cat_data))
            
            return categories
            
        except APIError as e:
            logger.error(f"Failed to get categories: {e}")
            return []
    
    async def get_category(self, slug: str) -> Category:
        """
        Get a specific category.
        
        Args:
            slug: Category slug
            
        Returns:
            Category object
        """
        endpoint = f"categories/{slug}/"
        
        try:
            data = await self._get(endpoint)
            return Category(data)
        except APIError as e:
            logger.error(f"Failed to get category {slug}: {e}")
            raise
    
    async def get_category_cloudcasts(
        self,
        category: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get cloudcasts in a category.
        
        Args:
            category: Category slug
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = f"categories/{category}/cloudcasts/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_chart(
        self,
        chart_type: str = "popular",
        genre: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 20
    ) -> List[Cloudcast]:
        """
        Get chart cloudcasts.
        
        Args:
            chart_type: Type of chart ("popular", "trending", "latest")
            genre: Optional genre filter
            country: Optional country filter
            limit: Number of cloudcasts
            
        Returns:
            List of cloudcasts
        """
        # Build endpoint
        if chart_type == "trending":
            endpoint = "popular/hot/"
        elif chart_type == "latest":
            endpoint = "new/"
        else:
            endpoint = "popular/"
        
        # Build params
        params = {"limit": limit}
        if genre:
            params["tag"] = genre
        if country:
            params["country"] = country
        
        try:
            data = await self._get(endpoint, params)
            
            cloudcasts = []
            results_key = "data" if "data" in data else "results"
            if results_key in data:
                for cc_data in data[results_key]:
                    cloudcasts.append(Cloudcast(cc_data))
            
            return cloudcasts
            
        except APIError as e:
            logger.error(f"Failed to get chart: {e}")
            return []
    
    async def get_exclusive(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get Mixcloud Select exclusive content.
        
        Args:
            limit: Number of cloudcasts to fetch
            offset: Offset for pagination
            
        Returns:
            Paginated cloudcasts
        """
        endpoint = "select/exclusive/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def get_recommended(
        self,
        limit: int = 20
    ) -> List[Cloudcast]:
        """
        Get recommended cloudcasts for authenticated user.
        
        Args:
            limit: Number of cloudcasts
            
        Returns:
            List of cloudcasts
        """
        endpoint = "me/recommended/"
        
        try:
            data = await self._get(endpoint, {"limit": limit}, authenticated=True)
            
            cloudcasts = []
            results_key = "data" if "data" in data else "results"
            if results_key in data:
                for cc_data in data[results_key]:
                    cloudcasts.append(Cloudcast(cc_data))
            
            return cloudcasts
            
        except APIError as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []


__all__ = ["DiscoverAPI"]