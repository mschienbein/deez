"""
Deezer search tools.

Provides search functionality for tracks, albums, and artists on Deezer.
"""

from typing import List, Dict, Any
from strands import tool

from ...operations.search import SearchOperation
from ....integrations.deezer import DeezerIntegration


class DeezerSearch(SearchOperation):
    """Deezer-specific search implementation."""
    
    platform_name = "deezer"
    
    def __init__(self):
        self.client = DeezerIntegration()
    
    async def search_tracks(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for tracks on Deezer."""
        raw_results = self.client.search(query, limit)
        return [self.standardize_track_result(r) for r in raw_results]
    
    async def search_albums(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for albums on Deezer."""
        # Note: Deezer integration might need album search method
        raw_results = self.client.search_albums(query, limit) if hasattr(self.client, 'search_albums') else []
        return [self.standardize_album_result(r) for r in raw_results]
    
    def _extract_artist(self, raw_result: Dict) -> str:
        """Extract artist name from Deezer result."""
        return raw_result.get('artist', 'Unknown')
    
    def _extract_album(self, raw_result: Dict) -> str:
        """Extract album name from Deezer result."""
        return raw_result.get('album', '')
    
    def _extract_duration(self, raw_result: Dict) -> int:
        """Extract duration from Deezer result."""
        return raw_result.get('duration', 0)


# Initialize search instance
deezer_search = DeezerSearch()


@tool
def search_deezer_tracks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for tracks on Deezer.
    
    Args:
        query: Search query (artist, track name, etc.)
        limit: Maximum number of results to return
    
    Returns:
        List of standardized track results from Deezer
    
    Example:
        >>> results = search_deezer_tracks("Daft Punk Get Lucky")
        >>> print(f"Found {len(results)} tracks")
    """
    import asyncio
    return asyncio.run(deezer_search.search_tracks(query, limit))


@tool
def search_deezer_albums(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for albums on Deezer.
    
    Args:
        query: Search query (artist, album name, etc.)
        limit: Maximum number of results to return
    
    Returns:
        List of standardized album results from Deezer
    
    Example:
        >>> results = search_deezer_albums("Random Access Memories")
        >>> print(f"Found {len(results)} albums")
    """
    import asyncio
    return asyncio.run(deezer_search.search_albums(query, limit))