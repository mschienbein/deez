"""
Discogs metadata tools.

Provides detailed metadata retrieval for releases, masters, artists, and labels.
"""

from typing import Dict, Any
from strands import tool

from ....integrations.discogs import DiscogsIntegration


# Initialize integration
discogs = DiscogsIntegration()


@tool
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
    
    Example:
        >>> release = discogs_get_release(1234567)
        >>> print(f"Title: {release['title']}")
        >>> print(f"Artists: {[a['name'] for a in release['artists']]}")
    """
    return discogs.get_release(release_id)


@tool
def discogs_get_master(master_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a master release.
    
    Args:
        master_id: Discogs master release ID
    
    Returns:
        Master release information including all versions
    
    Example:
        >>> master = discogs_get_master(123456)
        >>> print(f"Main release: {master['title']}")
        >>> print(f"Versions: {len(master.get('versions', []))}")
    """
    return discogs.get_master(master_id)


@tool
def discogs_get_artist(artist_id: int) -> Dict[str, Any]:
    """
    Get detailed information about an artist.
    
    Args:
        artist_id: Discogs artist ID
    
    Returns:
        Artist information including discography and profile
    
    Example:
        >>> artist = discogs_get_artist(123456)
        >>> print(f"Artist: {artist['name']}")
        >>> print(f"Real name: {artist.get('realname', 'N/A')}")
    """
    return discogs.get_artist(artist_id)


@tool
def discogs_get_label(label_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a record label.
    
    Args:
        label_id: Discogs label ID
    
    Returns:
        Label information including catalog and profile
    
    Example:
        >>> label = discogs_get_label(123456)
        >>> print(f"Label: {label['name']}")
        >>> print(f"Founded: {label.get('profile', '')}")
    """
    return discogs.get_label(label_id)