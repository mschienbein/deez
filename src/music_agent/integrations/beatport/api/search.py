"""
Search API for Beatport.
"""

from typing import Optional, List, Dict, Any

from .base import BaseAPI
from ..models import (
    SearchQuery, SearchResult, SearchType,
    Track, Release, Artist, Label
)
from ..utils.parser import ResponseParser


class SearchAPI(BaseAPI):
    """Handle search operations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize search API."""
        super().__init__(*args, **kwargs)
        self.parser = ResponseParser()
    
    def search(self, query: SearchQuery) -> SearchResult:
        """
        Perform search.
        
        Args:
            query: Search query parameters
            
        Returns:
            Search results
        """
        # Determine endpoint based on search type
        endpoint = f"catalog/{query.search_type.value}"
        
        # Get parameters
        params = query.to_params()
        
        # Make request
        response = self.get(endpoint, params)
        
        # Parse results based on type
        result = SearchResult(
            query=query,
            total=response.get('count', 0),
            page=query.page,
            per_page=query.per_page
        )
        
        results = response.get('results', [])
        
        if query.search_type == SearchType.TRACKS:
            result.tracks = [self.parser.parse_track(t) for t in results]
        elif query.search_type == SearchType.RELEASES:
            result.releases = [self.parser.parse_release(r) for r in results]
        elif query.search_type == SearchType.ARTISTS:
            result.artists = [self.parser.parse_artist(a) for a in results]
        elif query.search_type == SearchType.LABELS:
            result.labels = [self.parser.parse_label(l) for l in results]
        
        return result
    
    def search_tracks(
        self,
        query: str,
        **filters
    ) -> List[Track]:
        """
        Search for tracks.
        
        Args:
            query: Search query
            **filters: Additional filters
            
        Returns:
            List of tracks
        """
        search_query = SearchQuery(
            query=query,
            search_type=SearchType.TRACKS,
            **filters
        )
        result = self.search(search_query)
        return result.tracks
    
    def search_releases(
        self,
        query: str,
        **filters
    ) -> List[Release]:
        """
        Search for releases.
        
        Args:
            query: Search query
            **filters: Additional filters
            
        Returns:
            List of releases
        """
        search_query = SearchQuery(
            query=query,
            search_type=SearchType.RELEASES,
            **filters
        )
        result = self.search(search_query)
        return result.releases
    
    def search_artists(
        self,
        query: str,
        **filters
    ) -> List[Artist]:
        """
        Search for artists.
        
        Args:
            query: Search query
            **filters: Additional filters
            
        Returns:
            List of artists
        """
        search_query = SearchQuery(
            query=query,
            search_type=SearchType.ARTISTS,
            **filters
        )
        result = self.search(search_query)
        return result.artists
    
    def search_labels(
        self,
        query: str,
        **filters
    ) -> List[Label]:
        """
        Search for labels.
        
        Args:
            query: Search query
            **filters: Additional filters
            
        Returns:
            List of labels
        """
        search_query = SearchQuery(
            query=query,
            search_type=SearchType.LABELS,
            **filters
        )
        result = self.search(search_query)
        return result.labels
    
    def autocomplete(
        self,
        query: str,
        search_type: Optional[SearchType] = None
    ) -> Dict[str, List[str]]:
        """
        Get autocomplete suggestions.
        
        Args:
            query: Partial query string
            search_type: Type to search for
            
        Returns:
            Suggestions by type
        """
        endpoint = "catalog/autocomplete"
        params = {'q': query}
        
        if search_type:
            params['type'] = search_type.value
        
        response = self.get(endpoint, params)
        
        return {
            'tracks': response.get('tracks', []),
            'releases': response.get('releases', []),
            'artists': response.get('artists', []),
            'labels': response.get('labels', [])
        }