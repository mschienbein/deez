"""
Genre model for Deezer.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Genre:
    """Represents a Deezer genre."""
    
    # Base fields
    id: str
    type: str = "genre"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Genre fields
    name: str = ""
    picture: Optional[str] = None
    picture_small: Optional[str] = None
    picture_medium: Optional[str] = None
    picture_big: Optional[str] = None
    picture_xl: Optional[str] = None
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "genre"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Genre":
        """Create Genre from API response."""
        return cls(
            id=str(data.get("id", "")),
            type="genre",
            name=data.get("name", ""),
            picture=data.get("picture"),
            picture_small=data.get("picture_small"),
            picture_medium=data.get("picture_medium"),
            picture_big=data.get("picture_big"),
            picture_xl=data.get("picture_xl"),
            raw_data=data,
        )