"""
Search manager for SoundCloud.

High-level search interface with caching and result processing.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from ..models.track import Track
from ..models.playlist import Playlist
from ..models.user import User
from ..types import SearchFilters
from ..api import search as search_api
from .filters import FilterBuilder
from .aggregator import SearchAggregator

logger = logging.getLogger(__name__)


class SearchManager:
    """Manages search operations with caching and filtering."""
    
    def __init__(self, client, cache=None):
        """
        Initialize search manager.
        
        Args:
            client: SoundCloud client
            cache: Optional cache instance
        """
        self.client = client
        self.cache = cache
        self.aggregator = SearchAggregator()
    
    async def search(
        self,
        query: str,
        type: str = "all",
        limit: int = 50,
        offset: int = 0,
        filters: Optional[SearchFilters] = None,
        sort: Optional[str] = None
    ) -> Union[List, Dict]:
        """
        Perform a search with optional filtering and sorting.
        
        Args:
            query: Search query
            type: Search type (all, tracks, playlists, users, albums)
            limit: Maximum results
            offset: Pagination offset
            filters: Search filters
            sort: Sort option
            
        Returns:
            Search results (list or dict for "all")
        """
        # Check cache if available
        cache_key = self._get_cache_key(query, type, limit, offset, filters, sort)
        
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for search: {query}")
                return cached
        
        # Perform search based on type
        if type == "tracks":
            results = await search_api.search_tracks(
                self.client, query, limit, offset, filters
            )
        elif type == "playlists":
            results = await search_api.search_playlists(
                self.client, query, limit, offset, filters
            )
        elif type == "users":
            results = await search_api.search_users(
                self.client, query, limit, offset
            )
        elif type == "albums":
            results = await search_api.search_albums(
                self.client, query, limit, offset, filters
            )
        elif type == "all":
            results = await search_api.search_all(
                self.client, query, limit, offset, filters
            )
        else:
            raise ValueError(f"Invalid search type: {type}")
        
        # Apply sorting if requested
        if sort and isinstance(results, list):
            results = self._sort_results(results, sort)
        
        # Cache results
        if self.cache:
            await self.cache.set(cache_key, results, ttl=300)  # 5 minutes
        
        return results
    
    async def search_with_pagination(
        self,
        query: str,
        type: str = "tracks",
        page_size: int = 50,
        max_results: int = 200,
        filters: Optional[SearchFilters] = None
    ) -> List:
        """
        Search with automatic pagination.
        
        Args:
            query: Search query
            type: Search type
            page_size: Results per page
            max_results: Maximum total results
            filters: Search filters
            
        Returns:
            Combined list of all results
        """
        all_results = []
        offset = 0
        
        while len(all_results) < max_results:
            # Calculate limit for this page
            remaining = max_results - len(all_results)
            limit = min(page_size, remaining)
            
            # Perform search
            results = await self.search(
                query, type, limit, offset, filters
            )
            
            # Handle different result formats
            if isinstance(results, dict):
                # For "all" search type
                page_results = []
                for items in results.values():
                    page_results.extend(items)
            else:
                page_results = results
            
            if not page_results:
                # No more results
                break
            
            all_results.extend(page_results)
            offset += limit
            
            # Check if we got fewer results than requested
            if len(page_results) < limit:
                break
        
        return all_results[:max_results]
    
    async def search_by_tags(
        self,
        tags: List[str],
        type: str = "tracks",
        limit: int = 50
    ) -> List:
        """
        Search by tags.
        
        Args:
            tags: List of tags
            type: Search type
            limit: Maximum results
            
        Returns:
            List of results
        """
        # Build tag query
        query = " ".join(f"#{tag}" for tag in tags)
        
        # Create filters with tags
        filters = {"tags": tags}
        
        return await self.search(query, type, limit, filters=filters)
    
    async def search_by_genre(
        self,
        genre: str,
        type: str = "tracks",
        limit: int = 50
    ) -> List:
        """
        Search by genre.
        
        Args:
            genre: Genre name
            type: Search type
            limit: Maximum results
            
        Returns:
            List of results
        """
        filters = {"genre": genre}
        
        # Use genre as query too for better results
        return await self.search(genre, type, limit, filters=filters)
    
    async def search_recent(
        self,
        query: str,
        type: str = "tracks",
        days: int = 7,
        limit: int = 50
    ) -> List:
        """
        Search for recent content.
        
        Args:
            query: Search query
            type: Search type
            days: Number of days to look back
            limit: Maximum results
            
        Returns:
            List of recent results
        """
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        filters = {
            "created_at_from": from_date.isoformat(),
            "created_at_to": to_date.isoformat(),
        }
        
        return await self.search(query, type, limit, filters=filters)
    
    async def search_downloadable(
        self,
        query: str,
        limit: int = 50
    ) -> List[Track]:
        """
        Search for downloadable tracks.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of downloadable tracks
        """
        filters = {"downloadable": True}
        
        return await self.search(query, "tracks", limit, filters=filters)
    
    async def search_streamable(
        self,
        query: str,
        limit: int = 50
    ) -> List[Track]:
        """
        Search for streamable tracks.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of streamable tracks
        """
        filters = {"streamable": True}
        
        return await self.search(query, "tracks", limit, filters=filters)
    
    async def search_by_duration(
        self,
        query: str,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        limit: int = 50
    ) -> List[Track]:
        """
        Search tracks by duration.
        
        Args:
            query: Search query
            min_duration: Minimum duration in milliseconds
            max_duration: Maximum duration in milliseconds
            limit: Maximum results
            
        Returns:
            List of tracks
        """
        filters = {}
        
        if min_duration is not None:
            filters["duration_from"] = min_duration
        
        if max_duration is not None:
            filters["duration_to"] = max_duration
        
        return await self.search(query, "tracks", limit, filters=filters)
    
    async def search_by_bpm(
        self,
        query: str,
        min_bpm: Optional[float] = None,
        max_bpm: Optional[float] = None,
        limit: int = 50
    ) -> List[Track]:
        """
        Search tracks by BPM.
        
        Args:
            query: Search query
            min_bpm: Minimum BPM
            max_bpm: Maximum BPM
            limit: Maximum results
            
        Returns:
            List of tracks
        """
        filters = {}
        
        if min_bpm is not None:
            filters["bpm_from"] = min_bpm
        
        if max_bpm is not None:
            filters["bpm_to"] = max_bpm
        
        return await self.search(query, "tracks", limit, filters=filters)
    
    async def search_by_license(
        self,
        query: str,
        license: str,
        limit: int = 50
    ) -> List[Track]:
        """
        Search tracks by license.
        
        Args:
            query: Search query
            license: License type
            limit: Maximum results
            
        Returns:
            List of tracks
        """
        filters = {"license": license}
        
        return await self.search(query, "tracks", limit, filters=filters)
    
    async def get_trending(
        self,
        type: str = "tracks",
        genre: Optional[str] = None,
        limit: int = 50
    ) -> List:
        """
        Get trending content.
        
        Args:
            type: Content type
            genre: Optional genre filter
            limit: Maximum results
            
        Returns:
            List of trending items
        """
        # Search for popular recent content
        filters = {}
        if genre:
            filters["genre"] = genre
        
        # Use empty query to get all results
        results = await self.search_recent("", type, days=1, limit=limit * 2)
        
        # Sort by popularity metrics
        if type == "tracks":
            results.sort(key=lambda x: x.playback_count, reverse=True)
        elif type == "playlists":
            results.sort(key=lambda x: x.likes_count, reverse=True)
        elif type == "users":
            results.sort(key=lambda x: x.followers_count, reverse=True)
        
        return results[:limit]
    
    async def get_suggestions(
        self,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get search suggestions.
        
        Args:
            partial_query: Partial search query
            limit: Maximum suggestions
            
        Returns:
            List of suggestions
        """
        return await search_api.autocomplete(
            self.client, partial_query, limit
        )
    
    def _get_cache_key(
        self,
        query: str,
        type: str,
        limit: int,
        offset: int,
        filters: Optional[Dict],
        sort: Optional[str]
    ) -> str:
        """Generate cache key for search."""
        import hashlib
        import json
        
        key_data = {
            "query": query,
            "type": type,
            "limit": limit,
            "offset": offset,
            "filters": filters or {},
            "sort": sort or "",
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"search:{key_hash}"
    
    def _sort_results(self, results: List, sort: str) -> List:
        """Sort search results."""
        if not results:
            return results
        
        # Determine sort key based on result type and sort option
        if isinstance(results[0], Track):
            if sort == "popularity":
                return sorted(results, key=lambda x: x.playback_count, reverse=True)
            elif sort == "date":
                return sorted(results, key=lambda x: x.created_at or datetime.min, reverse=True)
            elif sort == "likes":
                return sorted(results, key=lambda x: x.likes_count, reverse=True)
            elif sort == "duration":
                return sorted(results, key=lambda x: x.duration)
        
        elif isinstance(results[0], Playlist):
            if sort == "popularity":
                return sorted(results, key=lambda x: x.likes_count, reverse=True)
            elif sort == "date":
                return sorted(results, key=lambda x: x.created_at or datetime.min, reverse=True)
            elif sort == "tracks":
                return sorted(results, key=lambda x: x.track_count, reverse=True)
        
        elif isinstance(results[0], User):
            if sort == "followers":
                return sorted(results, key=lambda x: x.followers_count, reverse=True)
            elif sort == "tracks":
                return sorted(results, key=lambda x: x.track_count, reverse=True)
        
        return results
    
    async def aggregate_results(
        self,
        results: Union[List, Dict]
    ) -> Dict[str, Any]:
        """
        Aggregate search results with statistics.
        
        Args:
            results: Search results
            
        Returns:
            Aggregated statistics
        """
        return self.aggregator.aggregate(results)


__all__ = ["SearchManager"]