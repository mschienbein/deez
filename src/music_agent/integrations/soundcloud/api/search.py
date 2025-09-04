"""
Search functionality for SoundCloud API.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from urllib.parse import quote

from ..models.track import Track
from ..models.playlist import Playlist
from ..models.user import User
from ..types import SearchFilters
from ..exceptions import APIError

logger = logging.getLogger(__name__)


async def search_tracks(
    client,
    query: str,
    limit: int = 50,
    offset: int = 0,
    filters: Optional[SearchFilters] = None
) -> List[Track]:
    """
    Search for tracks.
    
    Args:
        client: SoundCloud client
        query: Search query
        limit: Maximum number of results
        offset: Offset for pagination
        filters: Optional search filters
        
    Returns:
        List of Track objects
    """
    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
    }
    
    # Apply filters
    if filters:
        _apply_filters(params, filters)
    
    response = await client.request(
        "GET",
        "/tracks",
        params=params
    )
    
    tracks = []
    if isinstance(response, dict):
        for data in response.get("collection", []):
            tracks.append(Track(data, client))
    elif isinstance(response, list):
        for data in response:
            tracks.append(Track(data, client))
    
    return tracks


async def search_playlists(
    client,
    query: str,
    limit: int = 50,
    offset: int = 0,
    filters: Optional[SearchFilters] = None
) -> List[Playlist]:
    """
    Search for playlists.
    
    Args:
        client: SoundCloud client
        query: Search query
        limit: Maximum number of results
        offset: Offset for pagination
        filters: Optional search filters
        
    Returns:
        List of Playlist objects
    """
    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
    }
    
    # Apply filters
    if filters:
        _apply_filters(params, filters)
    
    response = await client.request(
        "GET",
        "/playlists",
        params=params
    )
    
    playlists = []
    if isinstance(response, dict):
        for data in response.get("collection", []):
            playlists.append(Playlist(data, client))
    elif isinstance(response, list):
        for data in response:
            playlists.append(Playlist(data, client))
    
    return playlists


async def search_users(
    client,
    query: str,
    limit: int = 50,
    offset: int = 0
) -> List[User]:
    """
    Search for users.
    
    Args:
        client: SoundCloud client
        query: Search query
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of User objects
    """
    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
    }
    
    response = await client.request(
        "GET",
        "/users",
        params=params
    )
    
    users = []
    if isinstance(response, dict):
        for data in response.get("collection", []):
            users.append(User(data, client))
    elif isinstance(response, list):
        for data in response:
            users.append(User(data, client))
    
    return users


async def search_all(
    client,
    query: str,
    limit: int = 50,
    offset: int = 0,
    filters: Optional[SearchFilters] = None
) -> Dict[str, List]:
    """
    Search across all content types.
    
    Args:
        client: SoundCloud client
        query: Search query
        limit: Maximum number of results per type
        offset: Offset for pagination
        filters: Optional search filters
        
    Returns:
        Dictionary with tracks, playlists, and users
    """
    # Use v2 API for unified search
    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
    }
    
    if filters:
        _apply_filters(params, filters)
    
    try:
        response = await client.request(
            "GET",
            "/search",
            params=params,
            api_version="v2"
        )
        
        results = {
            "tracks": [],
            "playlists": [],
            "users": [],
        }
        
        if isinstance(response, dict):
            # Unified results
            for item in response.get("collection", []):
                kind = item.get("kind")
                if kind == "track":
                    results["tracks"].append(Track(item, client))
                elif kind in ["playlist", "system-playlist"]:
                    results["playlists"].append(Playlist(item, client))
                elif kind == "user":
                    results["users"].append(User(item, client))
        
        return results
        
    except APIError:
        # Fall back to separate searches
        import asyncio
        
        tracks_task = search_tracks(client, query, limit, offset, filters)
        playlists_task = search_playlists(client, query, limit, offset, filters)
        users_task = search_users(client, query, limit, offset)
        
        tracks, playlists, users = await asyncio.gather(
            tracks_task, playlists_task, users_task
        )
        
        return {
            "tracks": tracks,
            "playlists": playlists,
            "users": users,
        }


async def search_albums(
    client,
    query: str,
    limit: int = 50,
    offset: int = 0,
    filters: Optional[SearchFilters] = None
) -> List[Playlist]:
    """
    Search for albums.
    
    Args:
        client: SoundCloud client
        query: Search query
        limit: Maximum number of results
        offset: Offset for pagination
        filters: Optional search filters
        
    Returns:
        List of Playlist objects (albums)
    """
    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
        "filter.playlist_type": "album",
    }
    
    if filters:
        _apply_filters(params, filters)
    
    # Use v2 API for better album support
    response = await client.request(
        "GET",
        "/search/albums",
        params=params,
        api_version="v2"
    )
    
    albums = []
    if isinstance(response, dict):
        for data in response.get("collection", []):
            playlist = Playlist(data, client)
            playlist.is_album = True
            albums.append(playlist)
    
    return albums


async def autocomplete(
    client,
    query: str,
    limit: int = 10,
    facet: Optional[str] = None
) -> List[str]:
    """
    Get search suggestions.
    
    Args:
        client: SoundCloud client
        query: Partial search query
        limit: Maximum number of suggestions
        facet: Type of suggestions (track, user, etc.)
        
    Returns:
        List of suggestions
    """
    params = {
        "q": query,
        "limit": limit,
    }
    
    if facet:
        params["facet"] = facet
    
    # Use v2 API for autocomplete
    response = await client.request(
        "GET",
        "/search/autocomplete",
        params=params,
        api_version="v2"
    )
    
    suggestions = []
    if isinstance(response, dict):
        # Extract suggestions based on response format
        if "queries" in response:
            suggestions = response["queries"]
        elif "collection" in response:
            for item in response["collection"]:
                if "query" in item:
                    suggestions.append(item["query"])
    elif isinstance(response, list):
        suggestions = response
    
    return suggestions


def _apply_filters(params: Dict[str, Any], filters: SearchFilters):
    """Apply search filters to parameters."""
    if filters.get("genre"):
        params["filter.genre"] = filters["genre"]
    
    if filters.get("tags"):
        params["tags"] = ",".join(filters["tags"])
    
    if filters.get("bpm_from") is not None:
        params["filter.bpm[from]"] = filters["bpm_from"]
    
    if filters.get("bpm_to") is not None:
        params["filter.bpm[to]"] = filters["bpm_to"]
    
    if filters.get("duration_from") is not None:
        params["filter.duration[from]"] = filters["duration_from"]
    
    if filters.get("duration_to") is not None:
        params["filter.duration[to]"] = filters["duration_to"]
    
    if filters.get("created_at_from"):
        params["filter.created_at[from]"] = filters["created_at_from"]
    
    if filters.get("created_at_to"):
        params["filter.created_at[to]"] = filters["created_at_to"]
    
    if filters.get("license"):
        params["filter.license"] = filters["license"]
    
    if "streamable" in filters:
        params["filter.streamable"] = str(filters["streamable"]).lower()
    
    if "downloadable" in filters:
        params["filter.downloadable"] = str(filters["downloadable"]).lower()
    
    if "private" in filters:
        params["filter.private"] = str(filters["private"]).lower()


__all__ = [
    "search_tracks",
    "search_playlists",
    "search_users",
    "search_all",
    "search_albums",
    "autocomplete",
]