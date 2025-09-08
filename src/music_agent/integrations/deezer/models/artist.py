"""
Artist model for Deezer.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional



@dataclass
class Artist:
    """Represents a Deezer artist."""
    
    # Base fields
    id: str
    type: str = "artist"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Artist fields
    name: str = ""
    link: Optional[str] = None
    share: Optional[str] = None
    picture: Optional[str] = None
    picture_small: Optional[str] = None
    picture_medium: Optional[str] = None
    picture_big: Optional[str] = None
    picture_xl: Optional[str] = None
    nb_album: int = 0
    nb_fan: int = 0
    radio: bool = False
    tracklist: Optional[str] = None
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "artist"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Artist":
        """Create Artist from API response."""
        return cls(
            id=str(data.get("id", "")),
            type="artist",
            name=data.get("name", ""),
            link=data.get("link"),
            share=data.get("share"),
            picture=data.get("picture"),
            picture_small=data.get("picture_small"),
            picture_medium=data.get("picture_medium"),
            picture_big=data.get("picture_big"),
            picture_xl=data.get("picture_xl"),
            nb_album=data.get("nb_album", 0),
            nb_fan=data.get("nb_fan", 0),
            radio=data.get("radio", False),
            tracklist=data.get("tracklist"),
            raw_data=data,
        )