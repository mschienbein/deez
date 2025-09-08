"""
Chat room-related models for Soulseek.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class RoomMessage:
    """A message in a chat room."""
    
    username: str
    message: str
    timestamp: datetime
    room_name: str
    is_action: bool = False
    
    @classmethod
    def from_api(cls, data: dict) -> "RoomMessage":
        """Create RoomMessage from slskd API response."""
        return cls(
            username=data.get("username", ""),
            message=data.get("message", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            room_name=data.get("roomName", ""),
            is_action=data.get("isAction", False)
        )


@dataclass
class Room:
    """A Soulseek chat room."""
    
    name: str
    users: List[str] = field(default_factory=list)
    messages: List[RoomMessage] = field(default_factory=list)
    is_joined: bool = False
    is_private: bool = False
    owner: Optional[str] = None
    operators: List[str] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: dict) -> "Room":
        """Create Room from slskd API response."""
        messages = [RoomMessage.from_api(m) for m in data.get("messages", [])]
        
        return cls(
            name=data.get("name", ""),
            users=data.get("users", []),
            messages=messages,
            is_joined=data.get("isJoined", False),
            is_private=data.get("isPrivate", False),
            owner=data.get("owner"),
            operators=data.get("operators", [])
        )
    
    @property
    def user_count(self) -> int:
        """Get number of users in room."""
        return len(self.users)
    
    def add_message(self, message: RoomMessage):
        """Add a message to the room."""
        self.messages.append(message)
    
    def get_recent_messages(self, limit: int = 50) -> List[RoomMessage]:
        """Get recent messages."""
        return self.messages[-limit:] if self.messages else []