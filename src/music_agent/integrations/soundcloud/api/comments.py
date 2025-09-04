"""
Comment management for SoundCloud.
"""

import logging
from typing import List, Optional

from ..models.comment import Comment
from ..exceptions import APIError

logger = logging.getLogger(__name__)


async def get_comment(client, comment_id: int) -> Comment:
    """
    Get a comment by ID.
    
    Args:
        client: SoundCloud client
        comment_id: Comment ID
        
    Returns:
        Comment object
    """
    response = await client.request("GET", f"/comments/{comment_id}")
    return Comment(response, client)


async def create_comment(
    client,
    track_id: int,
    body: str,
    timestamp: Optional[int] = None
) -> Comment:
    """
    Create a comment on a track.
    
    Args:
        client: SoundCloud client
        track_id: Track ID
        body: Comment text
        timestamp: Optional timestamp in milliseconds
        
    Returns:
        Created Comment object
    """
    data = {
        "body": body,
        "timestamp": timestamp
    } if timestamp else {"body": body}
    
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


async def get_my_comments(
    client,
    limit: int = 50,
    offset: int = 0
) -> List[Comment]:
    """
    Get authenticated user's comments.
    
    Args:
        client: SoundCloud client
        limit: Maximum number of comments
        offset: Offset for pagination
        
    Returns:
        List of Comment objects
    """
    params = {"limit": limit, "offset": offset}
    response = await client.request(
        "GET",
        "/me/comments",
        params=params
    )
    
    comments = []
    if isinstance(response, dict):
        for data in response.get("collection", []):
            comments.append(Comment(data, client))
    elif isinstance(response, list):
        for data in response:
            comments.append(Comment(data, client))
    
    return comments


__all__ = [
    "get_comment",
    "create_comment",
    "delete_comment",
    "get_my_comments",
]