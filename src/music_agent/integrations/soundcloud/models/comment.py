"""
Comment model for SoundCloud.

Represents a comment on a SoundCloud track.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from .base import BaseModel
from ..types import CommentResponse


class Comment(BaseModel):
    """Represents a comment on a SoundCloud track."""
    
    def __init__(self, data: Dict[str, Any], client=None):
        """
        Initialize comment from API data.
        
        Args:
            data: Comment data from API
            client: Optional SoundCloud client
        """
        # Core attributes
        self.id: int = 0
        self.body: str = ""
        self.created_at: Optional[datetime] = None
        
        # Track reference
        self.track_id: int = 0
        self.timestamp: Optional[int] = None  # Position in track (milliseconds)
        
        # User info
        self.user_id: int = 0
        self.user: Optional[Dict[str, Any]] = None
        self.username: Optional[str] = None
        self.user_avatar: Optional[str] = None
        
        # URI
        self.uri: str = ""
        
        super().__init__(data, client)
    
    def _parse_data(self, data: Dict[str, Any]):
        """Parse raw API data into comment attributes."""
        # Core attributes
        self.id = data.get("id", 0)
        self.body = data.get("body", "")
        self.created_at = self._parse_datetime(data.get("created_at"))
        
        # Track reference
        self.track_id = data.get("track_id", 0)
        self.timestamp = data.get("timestamp")
        
        # User info
        self.user_id = data.get("user_id", 0)
        self.user = data.get("user")
        if self.user:
            self.username = self.user.get("username")
            self.user_avatar = self.user.get("avatar_url")
        
        # URI
        self.uri = data.get("uri", "")
    
    @property
    def timestamp_seconds(self) -> Optional[float]:
        """Get timestamp in seconds."""
        if self.timestamp is not None:
            return self.timestamp / 1000.0
        return None
    
    @property
    def timestamp_formatted(self) -> Optional[str]:
        """Get formatted timestamp (MM:SS)."""
        if self.timestamp is None:
            return None
        
        total_seconds = int(self.timestamp_seconds)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    @property
    def is_timed(self) -> bool:
        """Check if comment is at a specific timestamp."""
        return self.timestamp is not None
    
    async def delete(self) -> bool:
        """
        Delete this comment.
        
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required to delete comment")
        
        from ..api import tracks
        return await tracks.delete_comment(self._client, self.id)
    
    async def reply(self, body: str) -> "Comment":
        """
        Reply to this comment.
        
        Note: SoundCloud doesn't have nested comments,
        this will create a new comment at the same timestamp.
        
        Args:
            body: Reply text
            
        Returns:
            New comment
        """
        if not self._client:
            raise RuntimeError("Client required to reply")
        
        from ..api import tracks
        
        # Create reply with mention
        reply_body = f"@{self.username} {body}" if self.username else body
        
        return await tracks.comment(
            self._client,
            self.track_id,
            reply_body,
            self.timestamp
        )
    
    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to format suitable for music agent.
        
        Returns:
            Dictionary with agent-compatible fields
        """
        return {
            "id": f"soundcloud:comment:{self.id}",
            "text": self.body,
            "track_id": f"soundcloud:{self.track_id}",
            "timestamp": self.timestamp_seconds,
            "timestamp_formatted": self.timestamp_formatted,
            "user": {
                "id": self.user_id,
                "username": self.username,
                "avatar": self.user_avatar,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "source": "soundcloud",
        }


__all__ = ["Comment"]