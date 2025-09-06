"""
Discogs marketplace tools.

Provides marketplace search and listing functionality.
"""

from typing import Optional, Dict, Any
from strands import tool

from ....integrations.discogs import (
    DiscogsIntegration,
    ListingCondition,
    ListingStatus,
    Currency
)


# Initialize integration  
discogs = DiscogsIntegration()


@tool
def discogs_search_marketplace(
    release_id: Optional[int] = None,
    artist: Optional[str] = None,
    title: Optional[str] = None,
    condition: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    currency: str = "USD",
    page: int = 1,
    per_page: int = 20
) -> Dict[str, Any]:
    """
    Search Discogs marketplace for items for sale.
    
    Args:
        release_id: Specific release ID to find listings for
        artist: Filter by artist name
        title: Filter by release title
        condition: Filter by condition (Mint, Near Mint, Very Good Plus, etc.)
        min_price: Minimum price filter
        max_price: Maximum price filter
        currency: Currency code (USD, EUR, GBP, etc.)
        page: Page number for pagination
        per_page: Results per page
    
    Returns:
        Marketplace listings with seller info and prices
    
    Example:
        >>> listings = discogs_search_marketplace(
        >>>     artist="Daft Punk", 
        >>>     title="Random Access Memories",
        >>>     condition="Near Mint",
        >>>     max_price=50.0
        >>> )
        >>> for listing in listings.get("listings", []):
        >>>     print(f"{listing['condition']} - ${listing['price']['value']}")
    """
    return discogs.search_marketplace(
        release_id=release_id,
        artist=artist,
        title=title,
        condition=ListingCondition(condition) if condition else None,
        min_price=min_price,
        max_price=max_price,
        currency=Currency(currency),
        page=page,
        per_page=per_page
    )


@tool
def discogs_get_listing(listing_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific marketplace listing.
    
    Args:
        listing_id: Discogs listing ID
    
    Returns:
        Detailed listing information including seller details
    
    Example:
        >>> listing = discogs_get_listing(123456789)
        >>> print(f"Price: ${listing['price']['value']}")
        >>> print(f"Seller: {listing['seller']['username']}")
    """
    return discogs.get_listing(listing_id)