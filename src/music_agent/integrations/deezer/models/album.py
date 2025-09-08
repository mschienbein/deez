"""
Album model for Deezer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum



class AlbumType(Enum):
    """Album types."""
    ALBUM = "album"
    SINGLE = "single"
    EP = "ep"
    COMPILATION = "compilation"
    PODCAST = "podcast"
    AUDIOBOOK = "audiobook"


@dataclass
class Album:
    """Represents a Deezer album."""
    
    # Base fields
    id: str
    type: str = "album"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Album fields
    title: str = ""
    upc: Optional[str] = None
    link: Optional[str] = None
    share: Optional[str] = None
    cover: Optional[str] = None
    cover_small: Optional[str] = None
    cover_medium: Optional[str] = None
    cover_big: Optional[str] = None
    cover_xl: Optional[str] = None
    md5_image: Optional[str] = None
    genre_id: Optional[int] = None
    nb_tracks: int = 0
    duration: int = 0  # Total duration in seconds
    fans: int = 0
    release_date: Optional[datetime] = None
    record_type: Optional[AlbumType] = None
    available: bool = True
    explicit_lyrics: bool = False
    explicit_content_lyrics: int = 0
    explicit_content_cover: int = 0
    
    # Related objects
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    
    # Track list (populated separately)
    tracklist: Optional[str] = None
    tracks_data: List[Dict[str, Any]] = field(default_factory=list)
    
    # Contributors
    contributors: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "album"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Album":
        """Create Album from API response."""
        # Parse release date
        release_date = None
        if data.get("release_date"):
            try:
                release_date = datetime.strptime(data["release_date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
        
        # Parse record type
        record_type = None
        if data.get("record_type"):
            try:
                record_type = AlbumType(data["record_type"].lower())
            except (ValueError, KeyError):
                pass
        
        # Extract artist info
        artist_id = None
        artist_name = None
        if data.get("artist"):
            artist_id = str(data["artist"].get("id", ""))
            artist_name = data["artist"].get("name", "")
        
        return cls(
            id=str(data.get("id", "")),
            type="album",
            title=data.get("title", ""),
            upc=data.get("upc"),
            link=data.get("link"),
            share=data.get("share"),
            cover=data.get("cover"),
            cover_small=data.get("cover_small"),
            cover_medium=data.get("cover_medium"),
            cover_big=data.get("cover_big"),
            cover_xl=data.get("cover_xl"),
            md5_image=data.get("md5_image"),
            genre_id=data.get("genre_id"),
            nb_tracks=data.get("nb_tracks", 0),
            duration=data.get("duration", 0),
            fans=data.get("fans", 0),
            release_date=release_date,
            record_type=record_type,
            available=data.get("available", True),
            explicit_lyrics=data.get("explicit_lyrics", False),
            explicit_content_lyrics=data.get("explicit_content_lyrics", 0),
            explicit_content_cover=data.get("explicit_content_cover", 0),
            artist_id=artist_id,
            artist_name=artist_name,
            tracklist=data.get("tracklist"),
            tracks_data=data.get("tracks", {}).get("data", []) if "tracks" in data else [],
            contributors=data.get("contributors", []),
            raw_data=data,
        )
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration:
            return "0:00"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    @property
    def year(self) -> Optional[int]:
        """Get release year."""
        if self.release_date:
            return self.release_date.year
        return None
    
    @property
    def is_single(self) -> bool:
        """Check if this is a single."""
        return self.record_type == AlbumType.SINGLE
    
    @property
    def is_ep(self) -> bool:
        """Check if this is an EP."""
        return self.record_type == AlbumType.EP
    
    @property
    def is_compilation(self) -> bool:
        """Check if this is a compilation."""
        return self.record_type == AlbumType.COMPILATION