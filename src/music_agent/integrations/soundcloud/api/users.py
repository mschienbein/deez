"""
User-related API endpoints for SoundCloud.
"""

import logging
from typing import Optional, List, Dict, Any

from ..models.user import User
from ..models.track import Track
from ..models.playlist import Playlist
from ..exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


async def get_user(client, user_id: int) -> User:
    """
    Get a user by ID.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        
    Returns:
        User object
        
    Raises:
        NotFoundError: If user not found
    """
    response = await client.request("GET", f"/users/{user_id}")
    return User(response, client)


async def get_me(client) -> User:
    """
    Get the authenticated user.
    
    Args:
        client: SoundCloud client
        
    Returns:
        User object
    """
    response = await client.request("GET", "/me")
    user = User(response, client)
    
    # Store user ID in client for convenience
    client.user_id = user.id
    
    return user


async def get_tracks(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Track]:
    """
    Get tracks by a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of tracks
        offset: Offset for pagination
        
    Returns:
        List of Track objects
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        f"/users/{user_id}/tracks",
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


async def get_playlists(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Playlist]:
    """
    Get playlists by a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of playlists
        offset: Offset for pagination
        
    Returns:
        List of Playlist objects
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        f"/users/{user_id}/playlists",
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


async def get_likes(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Track]:
    """
    Get tracks liked by a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of tracks
        offset: Offset for pagination
        
    Returns:
        List of Track objects
    """
    params = {"limit": limit, "offset": offset}
    
    # Try v2 API first
    try:
        response = await client.request(
            "GET",
            f"/users/{user_id}/likes",
            params=params,
            api_version="v2"
        )
        
        tracks = []
        if isinstance(response, dict):
            for item in response.get("collection", []):
                # Likes can contain tracks or playlists
                if item.get("track"):
                    tracks.append(Track(item["track"], client))
                elif item.get("kind") == "track":
                    tracks.append(Track(item, client))
        
        return tracks
        
    except APIError:
        # Fall back to v1 API
        response = await client.request(
            "GET",
            f"/users/{user_id}/favorites",
            params=params
        )
        
        if isinstance(response, list):
            return [Track(data, client) for data in response]
        
        return []


async def get_reposts(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Any]:
    """
    Get items reposted by a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of items
        offset: Offset for pagination
        
    Returns:
        List of Track/Playlist objects
    """
    params = {"limit": limit, "offset": offset}
    
    # Use v2 API for reposts
    response = await client.request(
        "GET",
        f"/stream/users/{user_id}/reposts",
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


async def get_followers(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[User]:
    """
    Get followers of a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of users
        offset: Offset for pagination
        
    Returns:
        List of User objects
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        f"/users/{user_id}/followers",
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


async def get_followings(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[User]:
    """
    Get users followed by a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of users
        offset: Offset for pagination
        
    Returns:
        List of User objects
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        f"/users/{user_id}/followings",
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


async def follow(client, user_id: int) -> bool:
    """
    Follow a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID to follow
        
    Returns:
        True if successful
    """
    try:
        # Get authenticated user ID
        if not hasattr(client, "user_id"):
            me = await get_me(client)
            client.user_id = me.id
        
        await client.request(
            "PUT",
            f"/users/{client.user_id}/followings/{user_id}"
        )
        return True
    except APIError:
        return False


async def unfollow(client, user_id: int) -> bool:
    """
    Unfollow a user.
    
    Args:
        client: SoundCloud client
        user_id: User ID to unfollow
        
    Returns:
        True if successful
    """
    try:
        # Get authenticated user ID
        if not hasattr(client, "user_id"):
            me = await get_me(client)
            client.user_id = me.id
        
        await client.request(
            "DELETE",
            f"/users/{client.user_id}/followings/{user_id}"
        )
        return True
    except APIError:
        return False


async def get_stream(
    client,
    limit: int = 50,
    offset: int = 0
) -> List[Any]:
    """
    Get the authenticated user's stream.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of items
        offset: Offset for pagination
        
    Returns:
        List of stream items
    """
    params = {"limit": limit, "offset": offset}
    
    # Use v2 API for stream
    response = await client.request(
        "GET",
        "/stream",
        params=params,
        api_version="v2"
    )
    
    items = []
    if isinstance(response, dict):
        for item in response.get("collection", []):
            # Stream can contain various types
            if item.get("track"):
                items.append(Track(item["track"], client))
            elif item.get("playlist"):
                items.append(Playlist(item["playlist"], client))
            elif item.get("kind") == "track":
                items.append(Track(item, client))
            elif item.get("kind") in ["playlist", "system-playlist"]:
                items.append(Playlist(item, client))
            else:
                # Raw item for other types
                items.append(item)
    
    return items


async def get_activities(
    client,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get the authenticated user's activities.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of activities
        offset: Offset for pagination
        
    Returns:
        List of activity dictionaries
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        "/me/activities",
        params=params
    )
    
    if isinstance(response, dict):
        return response.get("collection", [])
    elif isinstance(response, list):
        return response
    
    return []


async def get_connections(client) -> List[Dict[str, Any]]:
    """
    Get the authenticated user's connected accounts.
    
    Args:
        client: SoundCloud client
        
    Returns:
        List of connection dictionaries
    """
    response = await client.request("GET", "/me/connections")
    
    if isinstance(response, list):
        return response
    
    return []


async def update_profile(client, **updates) -> User:
    """
    Update the authenticated user's profile.
    
    Args:
        client: SoundCloud client
        **updates: Profile fields to update
        
    Returns:
        Updated User object
    """
    # Build update data
    user_data = {}
    
    # Allowed update fields
    allowed_fields = [
        "username", "full_name", "first_name", "last_name",
        "description", "city", "country", "website", "website_title",
        "discogs_name", "myspace_name"
    ]
    
    for key in allowed_fields:
        if key in updates:
            user_data[key] = updates[key]
    
    response = await client.request(
        "PUT",
        "/me",
        json=user_data
    )
    
    return User(response, client)


async def get_web_profiles(client, user_id: int) -> List[Dict[str, Any]]:
    """
    Get a user's web profiles (social links).
    
    Args:
        client: SoundCloud client
        user_id: User ID
        
    Returns:
        List of web profile dictionaries
    """
    response = await client.request(
        "GET",
        f"/users/{user_id}/web-profiles"
    )
    
    if isinstance(response, list):
        return response
    
    return []


__all__ = [
    "get_user",
    "get_me",
    "get_tracks",
    "get_playlists",
    "get_likes",
    "get_reposts",
    "get_followers",
    "get_followings",
    "follow",
    "unfollow",
    "get_stream",
    "get_activities",
    "get_connections",
    "update_profile",
    "get_web_profiles",
]