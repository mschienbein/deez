"""
Radio model for Deezer.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Radio:
    """Represents a Deezer radio station."""
    
    # Base fields
    id: str
    type: str = "radio"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Radio fields
    title: str = ""
    description: Optional[str] = None
    share: Optional[str] = None
    picture: Optional[str] = None
    picture_small: Optional[str] = None
    picture_medium: Optional[str] = None
    picture_big: Optional[str] = None
    picture_xl: Optional[str] = None
    tracklist: Optional[str] = None
    md5_image: Optional[str] = None
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "radio"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Radio":
        """Create Radio from API response."""
        return cls(
            id=str(data.get("id", "")),
            type="radio",
            title=data.get("title", ""),
            description=data.get("description"),
            share=data.get("share"),
            picture=data.get("picture"),
            picture_small=data.get("picture_small"),
            picture_medium=data.get("picture_medium"),
            picture_big=data.get("picture_big"),
            picture_xl=data.get("picture_xl"),
            tracklist=data.get("tracklist"),
            md5_image=data.get("md5_image"),
            raw_data=data,
        )