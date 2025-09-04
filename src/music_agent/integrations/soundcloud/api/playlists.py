"""
Playlist-related API endpoints for SoundCloud.
"""

import logging
from typing import Optional, List, Dict, Any

from ..models.playlist import Playlist
from ..exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


async def get_playlist(client, playlist_id: int) -> Playlist:
    """
    Get a playlist by ID.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        Playlist object
        
    Raises:
        NotFoundError: If playlist not found
    """
    # Try v2 API first for more complete data
    try:
        response = await client.request(
            "GET",
            f"/playlists/{playlist_id}",
            api_version="v2"
        )
    except APIError:
        # Fall back to v1
        response = await client.request("GET", f"/playlists/{playlist_id}")
    
    return Playlist(response, client)


async def get_playlist_tracks(
    client,
    playlist_id: int,
    limit: int = 500
) -> List["Track"]:
    """
    Get all tracks in a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        limit: Maximum number of tracks
        
    Returns:
        List of Track objects
    """
    from ..models.track import Track
    
    # Get playlist with tracks
    playlist = await get_playlist(client, playlist_id)
    
    # If tracks are already loaded
    if playlist.tracks:
        return playlist.tracks[:limit]
    
    # Load tracks if only IDs are present
    if playlist._track_ids:
        await playlist.load_tracks()
        return playlist.tracks[:limit]
    
    # Fallback: get tracks separately
    params = {"limit": limit}
    response = await client.request(
        "GET",
        f"/playlists/{playlist_id}/tracks",
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


async def create_playlist(
    client,
    title: str,
    tracks: Optional[List[int]] = None,
    **metadata
) -> Playlist:
    """
    Create a new playlist.
    
    Args:
        client: SoundCloud client
        title: Playlist title
        tracks: Optional list of track IDs
        **metadata: Additional playlist metadata
        
    Returns:
        Created Playlist object
    """
    # Build playlist data
    playlist_data = {
        "playlist": {
            "title": title,
            "sharing": metadata.get("sharing", "public"),
            "tracks": []
        }
    }
    
    # Add tracks
    if tracks:
        playlist_data["playlist"]["tracks"] = [
            {"id": track_id} for track_id in tracks
        ]
    
    # Add optional metadata
    for key in ["description", "genre", "tag_list", "label_name",
                "release", "release_date", "purchase_url", "license",
                "playlist_type", "ean"]:
        if key in metadata:
            playlist_data["playlist"][key] = metadata[key]
    
    response = await client.request(
        "POST",
        "/playlists",
        json=playlist_data
    )
    
    return Playlist(response, client)


async def update_playlist(
    client,
    playlist_id: int,
    **updates
) -> Playlist:
    """
    Update playlist metadata.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        **updates: Fields to update
        
    Returns:
        Updated Playlist object
    """
    # Build update data
    playlist_data = {"playlist": {}}
    
    # Allowed update fields
    allowed_fields = [
        "title", "description", "genre", "tag_list", "label_name",
        "release", "release_date", "sharing", "embeddable_by",
        "purchase_url", "license", "playlist_type", "ean"
    ]
    
    for key in allowed_fields:
        if key in updates:
            playlist_data["playlist"][key] = updates[key]
    
    # Handle tracks update specially
    if "tracks" in updates:
        playlist_data["playlist"]["tracks"] = [
            {"id": track_id} for track_id in updates["tracks"]
        ]
    
    response = await client.request(
        "PUT",
        f"/playlists/{playlist_id}",
        json=playlist_data
    )
    
    return Playlist(response, client)


async def delete_playlist(client, playlist_id: int) -> bool:
    """
    Delete a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        
    Returns:
        True if successful
    """
    try:
        await client.request("DELETE", f"/playlists/{playlist_id}")
        return True
    except APIError:
        return False


async def add_track(
    client,
    playlist_id: int,
    track_id: int,
    position: Optional[int] = None
) -> bool:
    """
    Add a track to a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        track_id: Track ID to add
        position: Optional position (None = end)
        
    Returns:
        True if successful
    """
    # Get current playlist
    playlist = await get_playlist(client, playlist_id)
    
    # Get current track IDs
    track_ids = [t.id for t in playlist.tracks] if playlist.tracks else []
    
    # Add new track
    if position is not None and 0 <= position < len(track_ids):
        track_ids.insert(position, track_id)
    else:
        track_ids.append(track_id)
    
    # Update playlist
    try:
        await update_playlist(client, playlist_id, tracks=track_ids)
        return True
    except APIError:
        return False


async def remove_track(
    client,
    playlist_id: int,
    track_id: int
) -> bool:
    """
    Remove a track from a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        track_id: Track ID to remove
        
    Returns:
        True if successful
    """
    # Get current playlist
    playlist = await get_playlist(client, playlist_id)
    
    # Get current track IDs
    track_ids = [t.id for t in playlist.tracks if t.id != track_id]
    
    # Update playlist
    try:
        await update_playlist(client, playlist_id, tracks=track_ids)
        return True
    except APIError:
        return False


async def reorder_tracks(
    client,
    playlist_id: int,
    track_ids: List[int]
) -> bool:
    """
    Reorder tracks in a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        track_ids: List of track IDs in new order
        
    Returns:
        True if successful
    """
    try:
        await update_playlist(client, playlist_id, tracks=track_ids)
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
        # Use system_playlists endpoint for likes
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


async def get_playlist_likers(
    client,
    playlist_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get users who liked a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        limit: Maximum number of users
        
    Returns:
        List of user data dictionaries
    """
    params = {"limit": limit}
    
    # Use v2 API
    response = await client.request(
        "GET",
        f"/playlists/{playlist_id}/likers",
        params=params,
        api_version="v2"
    )
    
    if isinstance(response, dict):
        return response.get("collection", [])
    elif isinstance(response, list):
        return response
    
    return []


async def get_playlist_reposters(
    client,
    playlist_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get users who reposted a playlist.
    
    Args:
        client: SoundCloud client
        playlist_id: Playlist ID
        limit: Maximum number of users
        
    Returns:
        List of user data dictionaries
    """
    params = {"limit": limit}
    
    # Use v2 API
    response = await client.request(
        "GET",
        f"/playlists/{playlist_id}/reposters",
        params=params,
        api_version="v2"
    )
    
    if isinstance(response, dict):
        return response.get("collection", [])
    elif isinstance(response, list):
        return response
    
    return []


__all__ = [
    "get_playlist",
    "get_playlist_tracks",
    "create_playlist",
    "update_playlist",
    "delete_playlist",
    "add_track",
    "remove_track",
    "reorder_tracks",
    "like_playlist",
    "unlike_playlist",
    "repost_playlist",
    "unrepost_playlist",
    "get_playlist_likers",
    "get_playlist_reposters",
]