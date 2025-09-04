"""
Track-related API endpoints for SoundCloud.
"""

import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

from ..models.track import Track
from ..models.comment import Comment
from ..exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


async def get_track(client, track_id: int) -> Track:
    """
    Get a track by ID.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        Track object
        
    Raises:
        NotFoundError: If track not found
    """
    response = await client.request("GET", f"/tracks/{track_id}")
    return Track(response, client)


async def get_tracks(client, track_ids: List[int]) -> List[Track]:
    """
    Get multiple tracks by IDs.
    
    Args:
        client: SoundCloud client
        track_ids: List of track IDs
        
    Returns:
        List of Track objects
    """
    # SoundCloud API supports bulk fetching with ids parameter
    params = {"ids": ",".join(map(str, track_ids))}
    response = await client.request("GET", "/tracks", params=params)
    
    if isinstance(response, list):
        return [Track(data, client) for data in response]
    else:
        return []


async def get_track_comments(
    client,
    track_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Comment]:
    """
    Get comments for a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        limit: Maximum number of comments
        offset: Offset for pagination
        
    Returns:
        List of Comment objects
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        f"/tracks/{track_id}/comments",
        params=params
    )
    
    comments = []
    if isinstance(response, dict):
        # Paginated response
        for data in response.get("collection", []):
            comments.append(Comment(data, client))
    elif isinstance(response, list):
        # Direct list response
        for data in response:
            comments.append(Comment(data, client))
    
    return comments


async def comment(
    client,
    track_id: int,
    body: str,
    timestamp: Optional[int] = None
) -> Comment:
    """
    Post a comment on a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        body: Comment text
        timestamp: Optional timestamp in milliseconds
        
    Returns:
        Created Comment object
    """
    data = {"body": body}
    
    if timestamp is not None:
        data["timestamp"] = timestamp
    
    response = await client.request(
        "POST",
        f"/tracks/{track_id}/comments",
        json=data
    )
    
    return Comment(response, client)


async def delete_comment(client, comment_id: int) -> bool:
    """
    Delete a comment.
    
    Args:
        client: SoundCloud client
        comment_id: Comment ID
        
    Returns:
        True if successful
    """
    try:
        await client.request("DELETE", f"/comments/{comment_id}")
        return True
    except APIError:
        return False


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
    Remove a repost.
    
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


async def get_related_tracks(
    client,
    track_id: int,
    limit: int = 10
) -> List[Track]:
    """
    Get related tracks.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        limit: Maximum number of tracks
        
    Returns:
        List of Track objects
    """
    params = {"limit": limit}
    
    # Try v2 API first
    try:
        response = await client.request(
            "GET",
            f"/tracks/{track_id}/related",
            params=params,
            api_version="v2"
        )
        
        tracks = []
        if isinstance(response, dict):
            for data in response.get("collection", []):
                tracks.append(Track(data, client))
        
        return tracks
        
    except APIError:
        # Fall back to v1 API
        response = await client.request(
            "GET",
            f"/tracks/{track_id}/related",
            params=params
        )
        
        if isinstance(response, list):
            return [Track(data, client) for data in response]
        
        return []


async def get_track_likers(
    client,
    track_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get users who liked a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        limit: Maximum number of users
        
    Returns:
        List of user data dictionaries
    """
    params = {"limit": limit}
    response = await client.request(
        "GET",
        f"/tracks/{track_id}/favoriters",
        params=params
    )
    
    if isinstance(response, dict):
        return response.get("collection", [])
    elif isinstance(response, list):
        return response
    
    return []


async def get_track_reposters(
    client,
    track_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get users who reposted a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        limit: Maximum number of users
        
    Returns:
        List of user data dictionaries
    """
    params = {"limit": limit}
    
    # Use v2 API for reposters
    response = await client.request(
        "GET",
        f"/tracks/{track_id}/reposters",
        params=params,
        api_version="v2"
    )
    
    if isinstance(response, dict):
        return response.get("collection", [])
    elif isinstance(response, list):
        return response
    
    return []


async def upload_track(
    client,
    file_path: str,
    title: str,
    **metadata
) -> Track:
    """
    Upload a track to SoundCloud.
    
    Args:
        client: SoundCloud client
        file_path: Path to audio file
        title: Track title
        **metadata: Additional track metadata
        
    Returns:
        Created Track object
    """
    # Prepare multipart data
    import aiofiles
    
    async with aiofiles.open(file_path, "rb") as f:
        file_data = await f.read()
    
    # Build track data
    track_data = {
        "title": title,
        "sharing": metadata.get("sharing", "public"),
        "streamable": metadata.get("streamable", True),
        "embeddable_by": metadata.get("embeddable_by", "all"),
        "downloadable": metadata.get("downloadable", False),
    }
    
    # Add optional metadata
    for key in ["description", "genre", "tag_list", "label_name", "release",
                "release_date", "purchase_url", "license", "track_type",
                "bpm", "key_signature", "isrc", "commentable"]:
        if key in metadata:
            track_data[key] = metadata[key]
    
    # Create multipart form
    data = aiohttp.FormData()
    data.add_field("track[title]", title)
    
    for key, value in track_data.items():
        data.add_field(f"track[{key}]", str(value))
    
    data.add_field(
        "track[asset_data]",
        file_data,
        filename="audio.mp3",
        content_type="audio/mpeg"
    )
    
    # Upload
    response = await client.request(
        "POST",
        "/tracks",
        data=data
    )
    
    return Track(response, client)


async def update_track(
    client,
    track_id: int,
    **updates
) -> Track:
    """
    Update track metadata.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        **updates: Fields to update
        
    Returns:
        Updated Track object
    """
    # Build update data
    track_data = {}
    
    # Allowed update fields
    allowed_fields = [
        "title", "description", "genre", "tag_list", "label_name",
        "release", "release_date", "streamable", "downloadable",
        "sharing", "embeddable_by", "purchase_url", "license",
        "track_type", "bpm", "key_signature", "isrc", "commentable"
    ]
    
    for key in allowed_fields:
        if key in updates:
            track_data[f"track[{key}]"] = updates[key]
    
    response = await client.request(
        "PUT",
        f"/tracks/{track_id}",
        json=track_data
    )
    
    return Track(response, client)


async def delete_track(client, track_id: int) -> bool:
    """
    Delete a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        
    Returns:
        True if successful
    """
    try:
        await client.request("DELETE", f"/tracks/{track_id}")
        return True
    except APIError:
        return False


__all__ = [
    "get_track",
    "get_tracks",
    "get_track_comments",
    "comment",
    "delete_comment",
    "like_track",
    "unlike_track",
    "repost_track",
    "unrepost_track",
    "get_related_tracks",
    "get_track_likers",
    "get_track_reposters",
    "upload_track",
    "update_track",
    "delete_track",
]