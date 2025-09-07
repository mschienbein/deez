"""
Search API functionality for Discogs.
"""

import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlencode

from ..models import SearchType, SearchResult
from ..exceptions import APIError

logger = logging.getLogger(__name__)


class SearchAPI:
    """Handles all search-related operations."""
    
    def __init__(self, client):
        """
        Initialize search API.
        
        Args:
            client: Parent DiscogsClient instance
        """
        self.client = client
    
    def search(
        self,
        query: str,
        type: Optional[SearchType] = None,
        title: Optional[str] = None,
        release_title: Optional[str] = None,
        artist: Optional[str] = None,
        label: Optional[str] = None,
        genre: Optional[str] = None,
        style: Optional[str] = None,
        country: Optional[str] = None,
        year: Optional[Union[int, str]] = None,
        format: Optional[str] = None,
        catno: Optional[str] = None,
        barcode: Optional[str] = None,
        track: Optional[str] = None,
        per_page: int = 50,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Perform advanced search on Discogs database.
        
        Args:
            query: Main search query
            type: Type of results to return (release, master, artist, label)
            title: Search in title
            release_title: Search in release title
            artist: Filter by artist
            label: Filter by label
            genre: Filter by genre
            style: Filter by style
            country: Filter by country
            year: Filter by year or year range (e.g., "1990-2000")
            format: Filter by format (Vinyl, CD, etc.)
            catno: Filter by catalog number
            barcode: Filter by barcode
            track: Search in track titles
            per_page: Number of results per page
            page: Page number
            
        Returns:
            List of SearchResult objects
        """
        # Build search parameters
        params = {"q": query}
        
        if type:
            params["type"] = type.value
        if title:
            params["title"] = title
        if release_title:
            params["release_title"] = release_title
        if artist:
            params["artist"] = artist
        if label:
            params["label"] = label
        if genre:
            params["genre"] = genre
        if style:
            params["style"] = style
        if country:
            params["country"] = country
        if year:
            params["year"] = str(year)
        if format:
            params["format"] = format
        if catno:
            params["catno"] = catno
        if barcode:
            params["barcode"] = barcode
        if track:
            params["track"] = track
        
        params["per_page"] = min(per_page, self.client.config.max_per_page)
        params["page"] = page
        
        logger.debug(f"Searching with params: {params}")
        
        try:
            # Use the underlying client's search method
            results = self.client._client.search(**params)
            
            # Convert to our model - limit to per_page items
            search_results = []
            count = 0
            for item in results:
                if count >= per_page:
                    break
                search_results.append(self._parse_search_result(item))
                count += 1
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise APIError(f"Search failed: {e}")
    
    def _parse_search_result(self, item: Any) -> SearchResult:
        """
        Parse raw search result into SearchResult model.
        
        Args:
            item: Raw search result from API
            
        Returns:
            SearchResult object
        """
        # Determine type
        if hasattr(item, 'type'):
            type_str = item.type
        elif 'type' in item.data:
            type_str = item.data['type']
        else:
            type_str = 'release'
        
        try:
            search_type = SearchType(type_str.lower())
        except ValueError:
            search_type = SearchType.RELEASE
        
        # Extract data depending on the object type
        if hasattr(item, 'data'):
            data = item.data
        else:
            data = item.__dict__ if hasattr(item, '__dict__') else {}
        
        # Extract artist name if available
        artist = None
        if search_type in [SearchType.RELEASE, SearchType.MASTER]:
            # Try to get artist from the title (format: "Artist - Title")
            title_parts = data.get('title', '').split(' - ', 1)
            if len(title_parts) == 2:
                artist = title_parts[0]
        elif search_type == SearchType.ARTIST:
            artist = data.get('title', '')
        
        return SearchResult(
            type=search_type,
            id=data.get('id', 0),
            title=data.get('title', ''),
            artist=artist,
            thumb=data.get('thumb', ''),
            cover_image=data.get('cover_image', ''),
            resource_url=data.get('resource_url', ''),
            uri=data.get('uri', ''),
            country=data.get('country'),
            year=data.get('year'),
            format=data.get('format', []),
            label=data.get('label', []),
            genre=data.get('genre', []),
            style=data.get('style', []),
            barcode=data.get('barcode', []),
            catno=data.get('catno'),
            community=data.get('community'),
            format_quantity=data.get('format_quantity'),
            formats=data.get('formats', [])
        )
    
    def search_artist(
        self,
        artist_name: str,
        per_page: int = 50,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search specifically for artists.
        
        Args:
            artist_name: Artist name to search
            per_page: Results per page
            page: Page number
            
        Returns:
            List of artist search results
        """
        return self.search(
            query=artist_name,
            type=SearchType.ARTIST,
            per_page=per_page,
            page=page
        )
    
    def search_label(
        self,
        label_name: str,
        per_page: int = 50,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search specifically for labels.
        
        Args:
            label_name: Label name to search
            per_page: Results per page
            page: Page number
            
        Returns:
            List of label search results
        """
        return self.search(
            query=label_name,
            type=SearchType.LABEL,
            per_page=per_page,
            page=page
        )
    
    def search_master(
        self,
        query: str,
        artist: Optional[str] = None,
        per_page: int = 50,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search specifically for master releases.
        
        Args:
            query: Search query
            artist: Filter by artist
            per_page: Results per page
            page: Page number
            
        Returns:
            List of master release search results
        """
        return self.search(
            query=query,
            type=SearchType.MASTER,
            artist=artist,
            per_page=per_page,
            page=page
        )