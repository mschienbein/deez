"""
Search API functionality for MusicBrainz.
"""

import logging
from typing import Optional, List, Dict, Any
from urllib.parse import quote

from ..models import (
    EntityType,
    SearchField,
    SearchResult,
    SearchResults,
)
from ..exceptions import APIError, InvalidQueryError
from .parsers import DataParser

logger = logging.getLogger(__name__)


class SearchAPI:
    """Handles all search-related operations."""
    
    def __init__(self, client):
        """
        Initialize search API.
        
        Args:
            client: Parent MusicBrainzClient instance
        """
        self.client = client
        self.parser = DataParser()
    
    def search(
        self,
        query: str,
        entity_type: EntityType,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """
        Perform a search on MusicBrainz.
        
        Args:
            query: Search query string
            entity_type: Type of entity to search for
            limit: Number of results to return
            offset: Offset for pagination
            **filters: Additional search filters
            
        Returns:
            SearchResults object
        """
        if not query:
            raise InvalidQueryError("Query cannot be empty")
        
        # Build the search query
        search_query = self._build_query(query, **filters)
        
        logger.debug(f"Searching {entity_type.value} with query: {search_query}")
        
        try:
            # Use the underlying musicbrainzngs search
            result = self._perform_search(
                entity_type,
                search_query,
                limit=min(limit, self.client.config.max_limit),
                offset=offset
            )
            
            # Parse results
            return self._parse_search_results(result, entity_type)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise APIError(f"Search failed: {e}")
    
    def search_artist(
        self,
        artist_name: str,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """Search for artists."""
        return self.search(artist_name, EntityType.ARTIST, limit, offset, **filters)
    
    def search_release(
        self,
        query: str,
        artist: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """Search for releases."""
        if artist:
            filters['artist'] = artist
        return self.search(query, EntityType.RELEASE, limit, offset, **filters)
    
    def search_recording(
        self,
        query: str,
        artist: Optional[str] = None,
        release: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """Search for recordings."""
        if artist:
            filters['artist'] = artist
        if release:
            filters['release'] = release
        return self.search(query, EntityType.RECORDING, limit, offset, **filters)
    
    def search_label(
        self,
        label_name: str,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """Search for labels."""
        return self.search(label_name, EntityType.LABEL, limit, offset, **filters)
    
    def _build_query(self, query: str, **filters) -> str:
        """
        Build a search query string with filters.
        
        Args:
            query: Base query string
            **filters: Additional filters
            
        Returns:
            Formatted query string
        """
        parts = [query]
        
        # Add filters
        for key, value in filters.items():
            if value is not None:
                # Handle special fields
                if key == 'year':
                    parts.append(f'date:{value}')
                elif key == 'country':
                    parts.append(f'country:{value}')
                elif key == 'format':
                    parts.append(f'format:"{value}"')
                elif key == 'status':
                    parts.append(f'status:{value}')
                elif key == 'type':
                    parts.append(f'type:{value}')
                elif key == 'tag':
                    parts.append(f'tag:{value}')
                else:
                    # Generic field:value format
                    parts.append(f'{key}:"{value}"')
        
        return ' AND '.join(parts)
    
    def _perform_search(
        self,
        entity_type: EntityType,
        query: str,
        limit: int,
        offset: int
    ) -> Dict[str, Any]:
        """
        Perform the actual search using musicbrainzngs.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            limit: Result limit
            offset: Result offset
            
        Returns:
            Raw search results
        """
        import musicbrainzngs as mb
        
        # Map entity type to search function
        search_functions = {
            EntityType.ARTIST: mb.search_artists,
            EntityType.RELEASE: mb.search_releases,
            EntityType.RELEASE_GROUP: mb.search_release_groups,
            EntityType.RECORDING: mb.search_recordings,
            EntityType.LABEL: mb.search_labels,
        }
        
        search_func = search_functions.get(entity_type)
        if not search_func:
            raise InvalidQueryError(f"Unsupported entity type: {entity_type}")
        
        # Perform search
        return search_func(query=query, limit=limit, offset=offset)
    
    def _parse_search_results(
        self,
        data: Dict[str, Any],
        entity_type: EntityType
    ) -> SearchResults:
        """
        Parse raw search results into SearchResults object.
        
        Args:
            data: Raw search results
            entity_type: Type of entity searched
            
        Returns:
            SearchResults object
        """
        # Get the results list based on entity type
        entity_key = entity_type.value + '-list'
        entity_count_key = entity_type.value + '-count'
        entity_offset_key = entity_type.value + '-offset'
        
        results_data = data.get(entity_key, [])
        total_count = data.get(entity_count_key, 0)
        offset = data.get(entity_offset_key, 0)
        
        # Parse individual results
        results = []
        for item in results_data:
            try:
                result = self.parser.parse_search_result(item, entity_type)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse search result: {e}")
                continue
        
        return SearchResults(
            results=results,
            total_count=total_count,
            offset=offset,
            limit=len(results)
        )