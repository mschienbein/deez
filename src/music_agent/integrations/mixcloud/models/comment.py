"""
Comment model for Mixcloud.

Represents a comment on a cloudcast.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseModel
from .user import User
from ..types import CommentResponse


class Comment(BaseModel):
    """Represents a comment on a Mixcloud cloudcast."""
    
    def _parse_data(self):
        """Parse comment data."""
        # Basic info
        self.key = self._raw_data.get("key", "")
        self.url = self._raw_data.get("url", "")
        self.comment = self._raw_data.get("comment", "")
        self.text = self.comment  # Alias
        
        # User
        user_data = self._raw_data.get("user")
        self.user = User(user_data) if user_data else None
        
        # Timestamps
        self.created_time = self._parse_datetime(self._raw_data.get("created_time"))
        self.submit_date = self._parse_datetime(self._raw_data.get("submit_date"))
        
        # Position in cloudcast (if timed comment)
        self.start_time = self._parse_int(self._raw_data.get("start_time"))
        self.end_time = self._parse_int(self._raw_data.get("end_time"))
        
        # Parent comment (for replies)
        self.parent_key = self._raw_data.get("parent_key")
        self.is_reply = bool(self.parent_key)
    
    @property
    def id(self) -> str:
        """Get comment ID."""
        return self.key.strip("/").split("/")[-1] if self.key else ""
    
    @property
    def username(self) -> str:
        """Get username of commenter."""
        return self.user.username if self.user else ""
    
    @property
    def user_display_name(self) -> str:
        """Get display name of commenter."""
        return self.user.display_name if self.user else ""
    
    @property
    def timestamp(self) -> datetime:
        """Get comment timestamp."""
        return self.created_time or self.submit_date
    
    @property
    def is_timed(self) -> bool:
        """Check if this is a timed comment."""
        return self.start_time is not None
    
    @property
    def position_formatted(self) -> Optional[str]:
        """Get formatted position string for timed comments."""
        if not self.is_timed or self.start_time is None:
            return None
        
        minutes = self.start_time // 60
        seconds = self.start_time % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def to_display_format(self) -> Dict[str, Any]:
        """
        Convert to display format.
        
        Returns:
            Dictionary with comment display information
        """
        result = {
            "id": self.id,
            "text": self.text,
            "username": self.username,
            "user_display_name": self.user_display_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_reply": self.is_reply,
        }
        
        if self.is_timed:
            result.update({
                "is_timed": True,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "position": self.position_formatted,
            })
        
        if self.parent_key:
            result["parent_id"] = self.parent_key.strip("/").split("/")[-1]
        
        return result
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"user='{self.username}', text='{text_preview}'"


__all__ = ["Comment"]