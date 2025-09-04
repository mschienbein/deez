"""
Repost management for SoundCloud.
"""

import logging
from typing import List, Union

from ..models.track import Track
from ..models.playlist import Playlist
from ..exceptions import APIError

logger = logging.getLogger(__name__)


async def repost_track(client, track_id: int) -> bool:
    """
    Repost a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if successful
    """
    try:
        # Use v2 API for reposts
        await client.request(
            "PUT",
            f"/stream/users/{client.user_id}/reposts/tracks/{track_id}",
            api_version="v2"
        )
        return True
    except APIError:
        return False


async def unrepost_track(client, track_id: int) -> bool:
    """
    Remove a track repost.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if successful
    """
    try:
        await client.request(
            "DELETE",
            f"/stream/users/{client.user_id}/reposts/tracks/{track_id}",
            api_version="v2"
        )
        return True
    except APIError:
        return False


async def repost_playlist(client, playlist_id: int) -> bool:
    """
    Repost a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        True if successful
    """
    try:
        await client.request(
            "PUT",
            f"/stream/users/{client.user_id}/reposts/playlists/{playlist_id}",
            api_version="v2"
        )
        return True
    except APIError:
        return False


async def unrepost_playlist(client, playlist_id: int) -> bool:
    """
    Remove a playlist repost.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        True if successful
    """
    try:
        await client.request(
            "DELETE",
            f"/stream/users/{client.user_id}/reposts/playlists/{playlist_id}",
            api_version="v2"
        )
        return True
    except APIError:
        return False


async def get_my_reposts(
    client,
    limit: int = 50,
    offset: int = 0
) -> List[Union[Track, Playlist]]:
    """
    Get authenticated user's reposts.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of items
        offset: Offset for pagination
        
    Returns:
        List of reposted Track/Playlist objects
    """
    params = {"limit": limit, "offset": offset}
    
    # Use v2 API for reposts
    response = await client.request(
        "GET",
        f"/stream/users/{client.user_id}/reposts",
        params=params,
        api_version="v2"
    )
    
    items = []
    if isinstance(response, dict):
        for item in response.get("collection", []):
            # Reposts can contain tracks or playlists
            if item.get("track"):
                items.append(Track(item["track"], client))
            elif item.get("playlist"):
                items.append(Playlist(item["playlist"], client))
            elif item.get("kind") == "track":
                items.append(Track(item, client))
            elif item.get("kind") in ["playlist", "system-playlist"]:
                items.append(Playlist(item, client))
    
    return items


async def check_track_reposted(client, track_id: int) -> bool:
    """
    Check if authenticated user reposted a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if reposted
    """
    # Get user's reposts and check if track is in them
    reposts = await get_my_reposts(client, limit=100)
    
    for item in reposts:
        if isinstance(item, Track) and item.id == track_id:
            return True
    
    return False


async def check_playlist_reposted(client, playlist_id: int) -> bool:
    """
    Check if authenticated user reposted a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        True if reposted
    """
    # Get user's reposts and check if playlist is in them
    reposts = await get_my_reposts(client, limit=100)
    
    for item in reposts:
        if isinstance(item, Playlist) and item.id == playlist_id:
            return True
    
    return False


__all__ = [
    "repost_track",
    "unrepost_track",
    "repost_playlist",
    "unrepost_playlist",
    "get_my_reposts",
    "check_track_reposted",
    "check_playlist_reposted",
]