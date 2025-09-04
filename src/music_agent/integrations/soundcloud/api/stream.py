"""
Stream and activity feed for SoundCloud.
"""

import logging
from typing import List, Dict, Any, Optional, Union

from ..models.track import Track
from ..models.playlist import Playlist
from ..models.user import User
from ..exceptions import APIError

logger = logging.getLogger(__name__)


async def get_stream(
    client,
    limit: int = 50,
    offset: int = 0
) -> List[Union[Track, Playlist, Dict]]:
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
                # Raw item for other types (reposts, etc.)
                items.append(item)
    
    return items


async def get_activities(
    client,
    limit: int = 50,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the authenticated user's activity feed.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of activities
        cursor: Cursor for pagination
        
    Returns:
        Dictionary with activities and next cursor
    """
    params = {"limit": limit}
    
    if cursor:
        params["cursor"] = cursor
    
    response = await client.request(
        "GET",
        "/me/activities",
        params=params
    )
    
    result = {
        "collection": [],
        "next_href": None,
        "cursor": None
    }
    
    if isinstance(response, dict):
        # Parse activities
        for activity in response.get("collection", []):
            parsed = _parse_activity(activity, client)
            if parsed:
                result["collection"].append(parsed)
        
        # Get pagination info
        result["next_href"] = response.get("next_href")
        if result["next_href"] and "cursor=" in result["next_href"]:
            # Extract cursor from next_href
            import re
            match = re.search(r"cursor=([^&]+)", result["next_href"])
            if match:
                result["cursor"] = match.group(1)
    
    return result


async def get_user_stream(
    client,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Union[Track, Playlist, Dict]]:
    """
    Get a user's public stream.
    
    Args:
        client: SoundCloud client
        user_id: User ID
        limit: Maximum number of items
        offset: Offset for pagination
        
    Returns:
        List of stream items
    """
    params = {"limit": limit, "offset": offset}
    
    # Use v2 API
    response = await client.request(
        "GET",
        f"/stream/users/{user_id}",
        params=params,
        api_version="v2"
    )
    
    items = []
    if isinstance(response, dict):
        for item in response.get("collection", []):
            if item.get("track"):
                items.append(Track(item["track"], client))
            elif item.get("playlist"):
                items.append(Playlist(item["playlist"], client))
            elif item.get("kind") == "track":
                items.append(Track(item, client))
            elif item.get("kind") in ["playlist", "system-playlist"]:
                items.append(Playlist(item, client))
            else:
                items.append(item)
    
    return items


async def get_related_activities(
    client,
    track_id: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get activities related to a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID (optional)
        limit: Maximum number of activities
        
    Returns:
        List of activity dictionaries
    """
    params = {"limit": limit}
    
    if track_id:
        params["track_id"] = track_id
    
    # Use v2 API
    response = await client.request(
        "GET",
        "/activities/related",
        params=params,
        api_version="v2"
    )
    
    activities = []
    if isinstance(response, dict):
        for activity in response.get("collection", []):
            parsed = _parse_activity(activity, client)
            if parsed:
                activities.append(parsed)
    
    return activities


def _parse_activity(activity: Dict[str, Any], client) -> Optional[Dict[str, Any]]:
    """
    Parse an activity item.
    
    Args:
        activity: Raw activity data
        client: SoundCloud client
        
    Returns:
        Parsed activity dictionary
    """
    parsed = {
        "type": activity.get("type"),
        "created_at": activity.get("created_at"),
        "tags": activity.get("tags", []),
    }
    
    # Parse based on activity type
    activity_type = activity.get("type")
    
    if activity_type in ["track", "track-repost", "track-like"]:
        # Track activity
        if activity.get("track"):
            parsed["track"] = Track(activity["track"], client)
    
    elif activity_type in ["playlist", "playlist-repost", "playlist-like"]:
        # Playlist activity
        if activity.get("playlist"):
            parsed["playlist"] = Playlist(activity["playlist"], client)
    
    elif activity_type in ["comment"]:
        # Comment activity
        from ..models.comment import Comment
        if activity.get("comment"):
            parsed["comment"] = Comment(activity["comment"], client)
    
    elif activity_type in ["favoriting", "following"]:
        # Social activity
        if activity.get("user"):
            parsed["user"] = User(activity["user"], client)
    
    # Add origin (user who performed the activity)
    if activity.get("origin"):
        parsed["origin"] = User(activity["origin"], client)
    
    return parsed


async def get_notifications(
    client,
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get notifications for authenticated user.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of notifications
        offset: Offset for pagination
        unread_only: Only return unread notifications
        
    Returns:
        List of notification dictionaries
    """
    params = {
        "limit": limit,
        "offset": offset,
    }
    
    if unread_only:
        params["filter"] = "unread"
    
    # Use v2 API for notifications
    response = await client.request(
        "GET",
        "/notifications",
        params=params,
        api_version="v2"
    )
    
    notifications = []
    if isinstance(response, dict):
        for notif in response.get("collection", []):
            notifications.append({
                "id": notif.get("id"),
                "type": notif.get("type"),
                "is_read": notif.get("is_read", False),
                "created_at": notif.get("created_at"),
                "message": notif.get("message"),
                "data": notif.get("data"),
            })
    
    return notifications


async def mark_notifications_read(client, notification_ids: List[int]) -> bool:
    """
    Mark notifications as read.
    
    Args:
        client: SoundCloud client
        notification_ids: List of notification IDs
        
    Returns:
        True if successful
    """
    try:
        data = {"notification_ids": notification_ids}
        
        await client.request(
            "PUT",
            "/notifications/mark-as-read",
            json=data,
            api_version="v2"
        )
        return True
    except APIError:
        return False


__all__ = [
    "get_stream",
    "get_activities",
    "get_user_stream",
    "get_related_activities",
    "get_notifications",
    "mark_notifications_read",
]