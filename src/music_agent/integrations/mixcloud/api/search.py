"""
Search API endpoints for Mixcloud.

Handles search operations for cloudcasts, users, and tags.
"""

import logging
from typing import Optional, Dict, Any, List, Union

from .base import BaseAPI
from ..models import Cloudcast, User, Tag, PaginatedResult
from ..types import SearchFilters
from ..exceptions import APIError

logger = logging.getLogger(__name__)


class SearchAPI(BaseAPI):
    """API client for search operations."""
    
    async def search(
        self,
        query: str,
        type: str = "cloudcast",
        limit: int = 20,
        offset: int = 0,
        filters: Optional[SearchFilters] = None
    ) -> PaginatedResult:
        """
        Search Mixcloud content.
        
        Args:
            query: Search query string
            type: Type to search ("cloudcast", "user", "tag")
            limit: Number of results to fetch
            offset: Offset for pagination
            filters: Additional search filters
            
        Returns:
            Paginated search results
        """
        endpoint = "search/"
        
        # Build parameters
        params = {
            "q": query,
            "type": type,
            "limit": limit,
            "offset": offset,
        }
        
        # Add filters if provided
        if filters:
            params.update(self._build_filter_params(filters))
        
        # Make request
        data = await self._get(endpoint, params)
        
        # Parse results based on type
        model_class = self._get_model_class(type)
        items = []
        
        results_key = "data" if "data" in data else "results"
        if results_key in data:
            for item_data in data[results_key]:
                items.append(model_class(item_data))
        
        # Get pagination info
        paging = data.get("paging", {})
        
        return PaginatedResult(
            items=items,
            total=data.get("total_results"),
            next_url=paging.get("next"),
            previous_url=paging.get("previous"),
            page=(offset // limit) + 1 if limit else 1,
            per_page=limit
        )
    
    async def search_cloudcasts(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[SearchFilters] = None
    ) -> PaginatedResult:
        """
        Search for cloudcasts.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Pagination offset
            filters: Search filters
            
        Returns:
            Paginated cloudcasts
        """
        return await self.search(query, "cloudcast", limit, offset, filters)
    
    async def search_users(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Search for users.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Paginated users
        """
        return await self.search(query, "user", limit, offset)
    
    async def search_tags(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Search for tags.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Paginated tags
        """
        return await self.search(query, "tag", limit, offset)
    
    async def search_by_tag(
        self,
        tag: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get cloudcasts by tag.
        
        Args:
            tag: Tag name
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Paginated cloudcasts
        """
        # Clean tag name
        tag = tag.lower().replace(" ", "-")
        endpoint = f"tag/{tag}/cloudcasts/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    async def search_by_category(
        self,
        category: str,
        limit: int = 20,
        offset: int = 0
    ) -> PaginatedResult:
        """
        Get cloudcasts by category.
        
        Args:
            category: Category name
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Paginated cloudcasts
        """
        # Clean category name
        category = category.lower().replace(" ", "-")
        endpoint = f"categories/{category}/cloudcasts/"
        
        return await self._get_paginated(
            endpoint,
            Cloudcast,
            limit=limit,
            offset=offset
        )
    
    def _build_filter_params(self, filters: SearchFilters) -> Dict[str, Any]:
        """
        Build query parameters from search filters.
        
        Args:
            filters: Search filters
            
        Returns:
            Query parameters dictionary
        """
        params = {}
        
        # Date range filters
        if filters.get("date_from"):
            params["date_from"] = filters["date_from"]
        if filters.get("date_to"):
            params["date_to"] = filters["date_to"]
        
        # Tags filter
        if filters.get("tags"):
            if isinstance(filters["tags"], list):
                params["tag"] = ",".join(filters["tags"])
            else:
                params["tag"] = filters["tags"]
        
        # Duration filters
        if filters.get("duration_min"):
            params["duration_min"] = filters["duration_min"]
        if filters.get("duration_max"):
            params["duration_max"] = filters["duration_max"]
        
        # User filter
        if filters.get("user"):
            params["user"] = filters["user"]
        
        # Category filter
        if filters.get("category"):
            params["category"] = filters["category"]
        
        # Exclusivity filters
        if filters.get("is_select") is not None:
            params["is_select"] = str(filters["is_select"]).lower()
        if filters.get("is_exclusive") is not None:
            params["is_exclusive"] = str(filters["is_exclusive"]).lower()
        
        return params
    
    def _get_model_class(self, type: str):
        """
        Get model class for search type.
        
        Args:
            type: Search type
            
        Returns:
            Model class
        """
        if type == "cloudcast":
            return Cloudcast
        elif type == "user":
            return User
        elif type == "tag":
            return Tag
        else:
            raise ValueError(f"Invalid search type: {type}")


__all__ = ["SearchAPI"]