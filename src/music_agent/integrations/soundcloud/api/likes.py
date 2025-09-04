"""
Like/favorite management for SoundCloud.
"""

import logging
from typing import List, Union

from ..models.track import Track
from ..models.playlist import Playlist
from ..exceptions import APIError

logger = logging.getLogger(__name__)


async def like_track(client, track_id: int) -> bool:
    """
    Like a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if successful
    """
    try:
        await client.request("PUT", f"/me/favorites/{track_id}")
        return True
    except APIError:
        return False


async def unlike_track(client, track_id: int) -> bool:
    """
    Unlike a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if successful
    """
    try:
        await client.request("DELETE", f"/me/favorites/{track_id}")
        return True
    except APIError:
        return False


async def like_playlist(client, playlist_id: int) -> bool:
    """
    Like a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        True if successful
    """
    try:
        # Use v2 API for playlist likes
        await client.request(
            "PUT",
            f"/users/{client.user_id}/playlist_likes/{playlist_id}",
            api_version="v2"
        )
        return True
    except APIError:
        return False


async def unlike_playlist(client, playlist_id: int) -> bool:
    """
    Unlike a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        True if successful
    """
    try:
        await client.request(
            "DELETE",
            f"/users/{client.user_id}/playlist_likes/{playlist_id}",
            api_version="v2"
        )
        return True
    except APIError:
        return False


async def get_my_likes(
    client,
    limit: int = 50,
    offset: int = 0
) -> List[Union[Track, Playlist]]:
    """
    Get authenticated user's likes.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of items
        offset: Offset for pagination
        
    Returns:
        List of liked Track/Playlist objects
    """
    params = {"limit": limit, "offset": offset}
    
    # Use v2 API for comprehensive likes
    response = await client.request(
        "GET",
        f"/users/{client.user_id}/likes",
        params=params,
        api_version="v2"
    )
    
    items = []
    if isinstance(response, dict):
        for item in response.get("collection", []):
            # Likes can contain tracks or playlists
            if item.get("track"):
                items.append(Track(item["track"], client))
            elif item.get("playlist"):
                items.append(Playlist(item["playlist"], client))
            elif item.get("kind") == "track":
                items.append(Track(item, client))
            elif item.get("kind") in ["playlist", "system-playlist"]:
                items.append(Playlist(item, client))
    
    return items


async def get_track_likes(client, track_id: int) -> int:
    """
    Get like count for a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        Number of likes
    """
    track = await client.api.tracks.get_track(client, track_id)
    return track.likes_count


async def check_track_liked(client, track_id: int) -> bool:
    """
    Check if authenticated user liked a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if liked
    """
    try:
        # Try to get the like status
        await client.request("GET", f"/me/favorites/{track_id}")
        return True
    except APIError:
        return False


__all__ = [
    "like_track",
    "unlike_track",
    "like_playlist",
    "unlike_playlist",
    "get_my_likes",
    "get_track_likes",
    "check_track_liked",
]