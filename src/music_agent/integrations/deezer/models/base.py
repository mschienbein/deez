"""
Base model for Deezer data objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class BaseModel:
    """Base class for all Deezer models."""
    
    id: str
    type: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model from API response."""
        raise NotImplementedError
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if key == "raw_data":
                continue
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, BaseModel):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [
                        item.to_dict() if isinstance(item, BaseModel) else item
                        for item in value
                    ]
                else:
                    result[key] = value
        return result
    
    @property
    def api_url(self) -> str:
        """Get API URL for this object."""
        return f"https://api.deezer.com/{self.type}/{self.id}"
    
    @property
    def web_url(self) -> str:
        """Get web URL for this object."""
        type_map = {
            "track": "track",
            "album": "album",
            "artist": "artist",
            "playlist": "playlist",
            "user": "profile",
            "radio": "radio",
        }
        url_type = type_map.get(self.type, self.type)
        
        # Handle language-specific URLs
        if self.type == "track":
            return f"https://www.deezer.com/track/{self.id}"
        elif self.type == "album":
            return f"https://www.deezer.com/album/{self.id}"
        elif self.type == "artist":
            return f"https://www.deezer.com/artist/{self.id}"
        elif self.type == "playlist":
            return f"https://www.deezer.com/playlist/{self.id}"
        elif self.type == "user":
            return f"https://www.deezer.com/profile/{self.id}"
        else:
            return f"https://www.deezer.com/{url_type}/{self.id}"