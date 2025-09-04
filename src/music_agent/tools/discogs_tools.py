"""
Discogs API tools for the Music Agent.

Provides a comprehensive set of tools for interacting with Discogs:
- Database search and retrieval
- Collection management
- Wantlist management
- Marketplace operations
- User profile and contributions
"""

from typing import Optional, List, Dict, Any, Union

from ..integrations.discogs import (
    DiscogsIntegration,
    SearchType,
    SearchFilters,
    ListingCondition,
    ListingStatus,
    Currency
)


# Initialize integration
discogs = DiscogsIntegration()


# ====================================
# Database Search & Retrieval Tools
# ====================================

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


def discogs_get_release(release_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific release.
    
    Args:
        release_id: Discogs release ID
    
    Returns:
        Detailed release information including:
        - Artists, labels, formats
        - Tracklist with durations
        - Genres and styles
        - Images and videos
        - Community data (have/want counts, ratings)
        - Marketplace data (for sale count, lowest price)
    """
    return discogs.get_release(release_id)


def discogs_get_master(master_id: int) -> Dict[str, Any]:
    """
    Get master release information.
    
    A master release is a set of similar releases (different versions/pressings).
    
    Args:
        master_id: Discogs master release ID
    
    Returns:
        Master release information with main version details
    """
    return discogs.get_master(master_id)


def discogs_get_artist(artist_id: int) -> Dict[str, Any]:
    """
    Get detailed artist information.
    
    Args:
        artist_id: Discogs artist ID
    
    Returns:
        Artist information including:
        - Profile and real name
        - Images
        - Name variations and aliases
        - Members (for groups)
        - Groups (for individual artists)
    """
    return discogs.get_artist(artist_id)


def discogs_get_label(label_id: int) -> Dict[str, Any]:
    """
    Get detailed label information.
    
    Args:
        label_id: Discogs label ID
    
    Returns:
        Label information including:
        - Profile and contact info
        - Parent label and sublabels
        - Images and URLs
    """
    return discogs.get_label(label_id)


def discogs_get_release_stats(release_id: int) -> Dict[str, Any]:
    """
    Get community statistics for a release.
    
    Args:
        release_id: Discogs release ID
    
    Returns:
        Statistics including:
        - Number of users who have it
        - Number of users who want it
        - Average rating and rating count
        - Number for sale and lowest price
    """
    return discogs.get_release_stats(release_id)


# ====================================
# User & Profile Tools
# ====================================

def discogs_get_identity() -> Dict[str, Any]:
    """
    Get authenticated user's identity.
    
    Returns:
        User identity information
    """
    return discogs.get_identity()


def discogs_get_user(username: str) -> Dict[str, Any]:
    """
    Get public user profile information.
    
    Args:
        username: Discogs username
    
    Returns:
        User profile including:
        - Location and registration date
        - Rating as seller
        - Collection and wantlist counts
        - Number of items for sale
    """
    return discogs.get_user(username)


def discogs_get_user_submissions(
    username: str,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """
    Get user's database submissions (edits to existing entries).
    
    Args:
        username: Discogs username
        page: Page number for pagination
        per_page: Results per page
    
    Returns:
        List of user's submissions/edits
    """
    return discogs.get_user_submissions(username, page, per_page)


def discogs_get_user_contributions(
    username: str,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """
    Get user's database contributions (new releases added).
    
    Args:
        username: Discogs username
        page: Page number for pagination
        per_page: Results per page
    
    Returns:
        List of user's contributions
    """
    return discogs.get_user_contributions(username, page, per_page)


# ====================================
# Collection Management Tools
# ====================================

def discogs_get_collection_folders(username: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get user's collection folders.
    
    Args:
        username: Discogs username (None for authenticated user)
    
    Returns:
        List of collection folders with counts
    """
    return discogs.get_collection_folders(username)


def discogs_get_collection_folder(
    folder_id: int,
    username: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    sort: str = 'added',
    sort_order: str = 'desc'
) -> Dict[str, Any]:
    """
    Get releases in a collection folder.
    
    Args:
        folder_id: Collection folder ID (1 = All folder)
        username: Discogs username (None for authenticated user)
        page: Page number for pagination
        per_page: Results per page
        sort: Sort by (added, artist, title, year, rating)
        sort_order: Sort order (asc, desc)
    
    Returns:
        Folder info and releases with pagination
    """
    return discogs.get_collection_folder(
        folder_id, username, page, per_page, sort, sort_order
    )


def discogs_add_to_collection(
    release_id: int,
    folder_id: int = 1,
    notes: Optional[str] = None,
    rating: Optional[int] = None
) -> bool:
    """
    Add a release to your collection.
    
    Args:
        release_id: Discogs release ID
        folder_id: Target folder ID (1 = All folder)
        notes: Optional notes about the release
        rating: Optional rating (1-5)
    
    Returns:
        True if successful
    """
    return discogs.add_to_collection(release_id, folder_id, notes, rating)


def discogs_remove_from_collection(
    release_id: int,
    instance_id: int,
    folder_id: int = 1
) -> bool:
    """
    Remove a release from your collection.
    
    Args:
        release_id: Discogs release ID
        instance_id: Collection instance ID
        folder_id: Folder ID (1 = All folder)
    
    Returns:
        True if successful
    """
    return discogs.remove_from_collection(release_id, instance_id, folder_id)


def discogs_get_collection_value(username: Optional[str] = None) -> Dict[str, Any]:
    """
    Get estimated collection value.
    
    Args:
        username: Discogs username (None for authenticated user)
    
    Returns:
        Collection value statistics (min, median, max in USD)
    """
    return discogs.get_collection_value(username)


def discogs_get_collection_fields(username: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get user-defined collection fields.
    
    Args:
        username: Discogs username (None for authenticated user)
    
    Returns:
        List of custom collection fields
    """
    return discogs.get_collection_fields(username)


# ====================================
# Wantlist Tools
# ====================================

def discogs_get_wantlist(
    username: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """
    Get user's wantlist.
    
    Args:
        username: Discogs username (None for authenticated user)
        page: Page number for pagination
        per_page: Results per page
    
    Returns:
        Wantlist items with pagination
    """
    return discogs.get_wantlist(username, page, per_page)


def discogs_add_to_wantlist(
    release_id: int,
    notes: Optional[str] = None,
    rating: Optional[int] = None
) -> bool:
    """
    Add a release to your wantlist.
    
    Args:
        release_id: Discogs release ID
        notes: Optional notes about why you want it
        rating: Optional rating (1-5)
    
    Returns:
        True if successful
    """
    return discogs.add_to_wantlist(release_id, notes, rating)


def discogs_remove_from_wantlist(release_id: int) -> bool:
    """
    Remove a release from your wantlist.
    
    Args:
        release_id: Discogs release ID
    
    Returns:
        True if successful
    """
    return discogs.remove_from_wantlist(release_id)


# ====================================
# Marketplace Tools
# ====================================

def discogs_get_inventory(
    username: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    status: Optional[str] = None,
    sort: str = 'listed',
    sort_order: str = 'desc'
) -> Dict[str, Any]:
    """
    Get marketplace inventory/listings.
    
    Args:
        username: Discogs username (None for authenticated user)
        page: Page number for pagination
        per_page: Results per page
        status: Filter by status (For Sale, Draft, Expired, Sold, Deleted)
        sort: Sort by (listed, price, item, artist, label, catno, audio, status, location)
        sort_order: Sort order (asc, desc)
    
    Returns:
        Marketplace listings with pagination
    """
    status_enum = ListingStatus(status) if status else None
    return discogs.get_inventory(username, page, per_page, status_enum, sort, sort_order)


def discogs_create_listing(
    release_id: int,
    condition: str,
    price: float,
    status: str = "For Sale",
    sleeve_condition: Optional[str] = None,
    comments: Optional[str] = None,
    allow_offers: bool = False,
    external_id: Optional[str] = None,
    location: Optional[str] = None,
    weight: Optional[float] = None,
    format_quantity: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a marketplace listing.
    
    Args:
        release_id: Discogs release ID
        condition: Media condition (Mint (M), Near Mint (NM or M-), Very Good Plus (VG+), 
                   Very Good (VG), Good Plus (G+), Good (G), Fair (F), Poor (P))
        price: Price in your default currency
        status: Listing status (For Sale, Draft, Expired, Sold, Deleted)
        sleeve_condition: Sleeve/cover condition (same options as condition)
        comments: Additional comments about the item
        allow_offers: Whether to accept offers
        external_id: Your external reference ID
        location: Item location
        weight: Item weight in grams
        format_quantity: Number of formats
    
    Returns:
        Created listing details
    """
    condition_enum = ListingCondition(condition)
    status_enum = ListingStatus(status)
    sleeve_enum = ListingCondition(sleeve_condition) if sleeve_condition else None
    
    return discogs.create_listing(
        release_id, condition_enum, price, status_enum,
        sleeve_enum, comments, allow_offers, external_id,
        location, weight, format_quantity
    )


def discogs_update_listing(listing_id: int, **kwargs) -> Dict[str, Any]:
    """
    Update a marketplace listing.
    
    Args:
        listing_id: Listing ID
        **kwargs: Fields to update (price, condition, comments, etc.)
    
    Returns:
        Updated listing details
    """
    return discogs.update_listing(listing_id, **kwargs)


def discogs_delete_listing(listing_id: int) -> bool:
    """
    Delete a marketplace listing.
    
    Args:
        listing_id: Listing ID
    
    Returns:
        True if successful
    """
    return discogs.delete_listing(listing_id)


def discogs_get_price_suggestions(release_id: int) -> Dict[str, Any]:
    """
    Get marketplace price suggestions for a release.
    
    Args:
        release_id: Discogs release ID
    
    Returns:
        Price statistics and suggestions including:
        - Number for sale
        - Lowest current price
        - Price statistics (min, median, max)
    """
    return discogs.get_marketplace_price_suggestions(release_id)


# ====================================
# Order Management Tools
# ====================================

def discogs_get_orders(
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    sort: str = 'created',
    sort_order: str = 'desc'
) -> Dict[str, Any]:
    """
    Get marketplace orders.
    
    Args:
        status: Filter by status
        page: Page number for pagination
        per_page: Results per page
        sort: Sort by field
        sort_order: Sort order (asc, desc)
    
    Returns:
        Orders with pagination
    """
    return discogs.get_orders(status, page, per_page, sort, sort_order)


def discogs_get_order(order_id: str) -> Dict[str, Any]:
    """
    Get specific order details.
    
    Args:
        order_id: Order ID
    
    Returns:
        Complete order information
    """
    return discogs.get_order(order_id)


def discogs_get_order_messages(order_id: str) -> List[Dict[str, Any]]:
    """
    Get messages for an order.
    
    Args:
        order_id: Order ID
    
    Returns:
        List of order messages
    """
    return discogs.get_order_messages(order_id)


def discogs_send_order_message(
    order_id: str,
    message: str,
    subject: Optional[str] = None
) -> bool:
    """
    Send a message about an order.
    
    Args:
        order_id: Order ID
        message: Message content
        subject: Optional message subject
    
    Returns:
        True if successful
    """
    return discogs.send_order_message(order_id, message, subject)


# ====================================
# Batch Operations Tools
# ====================================

def discogs_search_and_add_to_collection(
    query: str,
    search_type: str = "release",
    auto_add: bool = False,
    folder_id: int = 1
) -> Dict[str, Any]:
    """
    Search for a release and optionally add to collection.
    
    Args:
        query: Search query
        search_type: Type of search (release, master, artist, label)
        auto_add: Automatically add first result to collection
        folder_id: Collection folder ID
    
    Returns:
        Search results and add status
    """
    results = discogs.search(query=query, page=1, per_page=10)
    
    if auto_add and results['results']:
        first_result = results['results'][0]
        if first_result['type'] == 'release':
            success = discogs.add_to_collection(first_result['id'], folder_id)
            results['added_to_collection'] = success
    
    return results


def discogs_search_and_add_to_wantlist(
    query: str,
    auto_add: bool = False
) -> Dict[str, Any]:
    """
    Search for a release and optionally add to wantlist.
    
    Args:
        query: Search query
        auto_add: Automatically add first result to wantlist
    
    Returns:
        Search results and add status
    """
    results = discogs.search(query=query, page=1, per_page=10)
    
    if auto_add and results['results']:
        first_result = results['results'][0]
        if first_result['type'] == 'release':
            success = discogs.add_to_wantlist(first_result['id'])
            results['added_to_wantlist'] = success
    
    return results


def discogs_find_in_marketplace(
    query: str,
    max_price: Optional[float] = None,
    min_condition: str = "Good (G)",
    country: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for a release and check marketplace availability.
    
    Args:
        query: Search query
        max_price: Maximum acceptable price
        min_condition: Minimum acceptable condition
        country: Preferred seller country
    
    Returns:
        Search results with marketplace information
    """
    results = discogs.search(query=query, page=1, per_page=10)
    
    marketplace_results = []
    for result in results.get('results', []):
        if result['type'] == 'release':
            stats = discogs.get_release_stats(result['id'])
            
            item = {
                'release': result,
                'marketplace': stats.get('marketplace', {}),
                'community': stats.get('community', {})
            }
            
            # Check if it meets criteria
            if max_price and stats.get('lowest_price'):
                item['meets_price_criteria'] = stats['lowest_price'] <= max_price
            
            marketplace_results.append(item)
    
    return {
        'results': marketplace_results,
        'search_criteria': {
            'query': query,
            'max_price': max_price,
            'min_condition': min_condition,
            'country': country
        }
    }


# Export all tools for easy import
__all__ = [
    # Database tools
    'discogs_search',
    'discogs_get_release',
    'discogs_get_master',
    'discogs_get_artist',
    'discogs_get_label',
    'discogs_get_release_stats',
    
    # User tools
    'discogs_get_identity',
    'discogs_get_user',
    'discogs_get_user_submissions',
    'discogs_get_user_contributions',
    
    # Collection tools
    'discogs_get_collection_folders',
    'discogs_get_collection_folder',
    'discogs_add_to_collection',
    'discogs_remove_from_collection',
    'discogs_get_collection_value',
    'discogs_get_collection_fields',
    
    # Wantlist tools
    'discogs_get_wantlist',
    'discogs_add_to_wantlist',
    'discogs_remove_from_wantlist',
    
    # Marketplace tools
    'discogs_get_inventory',
    'discogs_create_listing',
    'discogs_update_listing',
    'discogs_delete_listing',
    'discogs_get_price_suggestions',
    
    # Order tools
    'discogs_get_orders',
    'discogs_get_order',
    'discogs_get_order_messages',
    'discogs_send_order_message',
    
    # Batch operation tools
    'discogs_search_and_add_to_collection',
    'discogs_search_and_add_to_wantlist',
    'discogs_find_in_marketplace'
]