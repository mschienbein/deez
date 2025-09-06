"""
Discogs search tools.

Provides comprehensive search functionality for the Discogs database.
"""

from typing import Optional, Dict, Any, Union
from strands import tool

from ....integrations.discogs import (
    DiscogsIntegration,
    SearchType,
    SearchFilters
)


# Initialize integration
discogs = DiscogsIntegration()


@tool
def discogs_search(
    query: str,
    search_type: Optional[str] = None,
    artist: Optional[str] = None,
    label: Optional[str] = None,
    genre: Optional[str] = None,
    style: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[Union[int, str]] = None,
    format: Optional[str] = None,
    catno: Optional[str] = None,
    barcode: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """
    Search Discogs database with advanced filters.
    
    Args:
        query: Main search query
        search_type: Type of result (release, master, artist, label)
        artist: Filter by artist name
        label: Filter by label name
        genre: Filter by genre (Electronic, Rock, Jazz, etc.)
        style: Filter by style (House, Techno, etc.)
        country: Filter by country
        year: Filter by year or range (e.g., "1990-2000")
        format: Filter by format (Vinyl, CD, Cassette, etc.)
        catno: Filter by catalog number
        barcode: Filter by barcode
        page: Page number for pagination
        per_page: Results per page (max 100)
    
    Returns:
        Search results with pagination info
    
    Example:
        >>> results = discogs_search(
        >>>     query="Daft Punk", 
        >>>     search_type="release",
        >>>     genre="Electronic",
        >>>     year="2001"
        >>> )
        >>> for release in results.get("results", []):
        >>>     print(f"{release['title']} ({release['year']})")
    """
    filters = SearchFilters(
        query=query,
        type=SearchType(search_type) if search_type else None,
        artist=artist,
        label=label,
        genre=genre,
        style=style,
        country=country,
        year=year,
        format=format,
        catno=catno,
        barcode=barcode
    )
    
    return discogs.search(filters=filters, page=page, per_page=per_page)