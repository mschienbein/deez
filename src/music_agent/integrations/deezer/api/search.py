"""
Search API for Deezer.
"""

import logging
from typing import List, Optional
from urllib.parse import quote_plus

from .base import BaseAPI
from ..models import (
    Track, Album, Artist, Playlist,
    SearchResult, SearchFilters
)

logger = logging.getLogger(__name__)


class SearchAPI(BaseAPI):
    """Search API endpoints."""
    
    async def search_tracks(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        filters: Optional[SearchFilters] = None
    ) -> SearchResult[Track]:
        """
        Search for tracks.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Result offset for pagination
            filters: Optional search filters
            
        Returns:
            Search results
        """
        # Build search query
        search_query = query
        if filters:
            filter_query = filters.to_query_string()
            if filter_query:
                search_query = f"{query} {filter_query}"
        
        # Make request
        params = {
            "q": search_query,
            "limit": limit,
            "index": offset,
        }
        
        if filters and filters.order:
            params["order"] = filters.order
        
        response = await self.get("search/track", params=params)
        
        # Parse results
        tracks = [Track.from_api(item) for item in response.get("data", [])]
        
        return SearchResult(
            data=tracks,
            total=response.get("total", 0),
            next=response.get("next"),
            prev=response.get("prev"),
        )
    
    async def search_albums(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0
    ) -> SearchResult[Album]:
        """
        Search for albums.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Result offset
            
        Returns:
            Search results
        """
        params = {
            "q": query,
            "limit": limit,
            "index": offset,
        }
        
        response = await self.get("search/album", params=params)
        
        albums = [Album.from_api(item) for item in response.get("data", [])]
        
        return SearchResult(
            data=albums,
            total=response.get("total", 0),
            next=response.get("next"),
            prev=response.get("prev"),
        )
    
    async def search_artists(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0
    ) -> SearchResult[Artist]:
        """
        Search for artists.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Result offset
            
        Returns:
            Search results
        """
        params = {
            "q": query,
            "limit": limit,
            "index": offset,
        }
        
        response = await self.get("search/artist", params=params)
        
        artists = [Artist.from_api(item) for item in response.get("data", [])]
        
        return SearchResult(
            data=artists,
            total=response.get("total", 0),
            next=response.get("next"),
            prev=response.get("prev"),
        )
    
    async def search_playlists(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0
    ) -> SearchResult[Playlist]:
        """
        Search for playlists.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Result offset
            
        Returns:
            Search results
        """
        params = {
            "q": query,
            "limit": limit,
            "index": offset,
        }
        
        response = await self.get("search/playlist", params=params)
        
        playlists = [Playlist.from_api(item) for item in response.get("data", [])]
        
        return SearchResult(
            data=playlists,
            total=response.get("total", 0),
            next=response.get("next"),
            prev=response.get("prev"),
        )
    
    async def search_all(
        self,
        query: str,
        limit: int = 10
    ) -> dict:
        """
        Search all content types.
        
        Args:
            query: Search query
            limit: Number of results per type
            
        Returns:
            Dictionary with results for each type
        """
        # Search all types in parallel
        import asyncio
        
        tasks = [
            self.search_tracks(query, limit),
            self.search_albums(query, limit),
            self.search_artists(query, limit),
            self.search_playlists(query, limit),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = {}
        
        # Process tracks
        if not isinstance(results[0], Exception):
            output["tracks"] = results[0]
        else:
            logger.error(f"Track search failed: {results[0]}")
            output["tracks"] = SearchResult(data=[], total=0)
        
        # Process albums
        if not isinstance(results[1], Exception):
            output["albums"] = results[1]
        else:
            logger.error(f"Album search failed: {results[1]}")
            output["albums"] = SearchResult(data=[], total=0)
        
        # Process artists
        if not isinstance(results[2], Exception):
            output["artists"] = results[2]
        else:
            logger.error(f"Artist search failed: {results[2]}")
            output["artists"] = SearchResult(data=[], total=0)
        
        # Process playlists
        if not isinstance(results[3], Exception):
            output["playlists"] = results[3]
        else:
            logger.error(f"Playlist search failed: {results[3]}")
            output["playlists"] = SearchResult(data=[], total=0)
        
        return output