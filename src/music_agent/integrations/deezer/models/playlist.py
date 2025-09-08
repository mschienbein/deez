"""
Playlist model for Deezer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional



@dataclass
class Playlist:
    """Represents a Deezer playlist."""
    
    # Base fields
    id: str
    type: str = "playlist"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Playlist fields
    title: str = ""
    description: Optional[str] = None
    duration: int = 0
    public: bool = True
    is_loved_track: bool = False
    collaborative: bool = False
    nb_tracks: int = 0
    fans: int = 0
    link: Optional[str] = None
    share: Optional[str] = None
    picture: Optional[str] = None
    picture_small: Optional[str] = None
    picture_medium: Optional[str] = None
    picture_big: Optional[str] = None
    picture_xl: Optional[str] = None
    checksum: Optional[str] = None
    tracklist: Optional[str] = None
    creation_date: Optional[datetime] = None
    md5_image: Optional[str] = None
    picture_type: Optional[str] = None
    
    # Creator info
    creator_id: Optional[str] = None
    creator_name: Optional[str] = None
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "playlist"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Playlist":
        """Create Playlist from API response."""
        # Parse creation date
        creation_date = None
        if data.get("creation_date"):
            try:
                creation_date = datetime.fromisoformat(data["creation_date"])
            except (ValueError, TypeError):
                pass
        
        # Extract creator info
        creator_id = None
        creator_name = None
        if data.get("creator"):
            creator_id = str(data["creator"].get("id", ""))
            creator_name = data["creator"].get("name", "")
        elif data.get("user"):
            creator_id = str(data["user"].get("id", ""))
            creator_name = data["user"].get("name", "")
        
        return cls(
            id=str(data.get("id", "")),
            type="playlist",
            title=data.get("title", ""),
            description=data.get("description"),
            duration=data.get("duration", 0),
            public=data.get("public", True),
            is_loved_track=data.get("is_loved_track", False),
            collaborative=data.get("collaborative", False),
            nb_tracks=data.get("nb_tracks", 0),
            fans=data.get("fans", 0),
            link=data.get("link"),
            share=data.get("share"),
            picture=data.get("picture"),
            picture_small=data.get("picture_small"),
            picture_medium=data.get("picture_medium"),
            picture_big=data.get("picture_big"),
            picture_xl=data.get("picture_xl"),
            checksum=data.get("checksum"),
            tracklist=data.get("tracklist"),
            creation_date=creation_date,
            md5_image=data.get("md5_image"),
            picture_type=data.get("picture_type"),
            creator_id=creator_id,
            creator_name=creator_name,
            raw_data=data,
        )