"""
Track model for Deezer.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum


class TrackFormat(Enum):
    """Available track formats."""
    FLAC = "FLAC"
    MP3_320 = "MP3_320"
    MP3_128 = "MP3_128"
    MP3_64 = "MP3_64"
    MP3_32 = "MP3_32"
    AAC_64 = "AAC_64"
    
    @property
    def bitrate(self) -> int:
        """Get bitrate in kbps."""
        rates = {
            "FLAC": 1411,
            "MP3_320": 320,
            "MP3_128": 128,
            "MP3_64": 64,
            "MP3_32": 32,
            "AAC_64": 64,
        }
        return rates.get(self.value, 0)
    
    @property
    def is_lossless(self) -> bool:
        """Check if format is lossless."""
        return self == TrackFormat.FLAC


@dataclass
class Track:
    """Represents a Deezer track."""
    
    # Base fields
    id: str
    type: str = "track"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # Track fields
    title: str = ""
    title_short: str = ""
    title_version: Optional[str] = None
    isrc: Optional[str] = None
    link: Optional[str] = None
    duration: int = 0  # in seconds
    track_position: Optional[int] = None
    disk_number: Optional[int] = None
    rank: Optional[int] = None
    release_date: Optional[datetime] = None
    explicit_lyrics: bool = False
    explicit_content_lyrics: int = 0
    explicit_content_cover: int = 0
    preview: Optional[str] = None
    bpm: Optional[float] = None
    gain: Optional[float] = None
    
    # Related objects (will be populated separately)
    artist_id: Optional[str] = None
    artist_name: Optional[str] = None
    album_id: Optional[str] = None
    album_title: Optional[str] = None
    
    # Contributors
    contributors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Media information
    md5_image: Optional[str] = None
    available_countries: List[str] = field(default_factory=list)
    alternative: Optional["Track"] = None
    
    # Download/stream info (populated when authenticated)
    readable: bool = True
    available_formats: List[TrackFormat] = field(default_factory=list)
    media_version: Optional[str] = None
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "track"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Track":
        """Create Track from API response."""
        # Parse release date
        release_date = None
        if data.get("release_date"):
            try:
                release_date = datetime.strptime(data["release_date"], "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
        
        # Extract artist info
        artist_id = None
        artist_name = None
        if data.get("artist"):
            artist_id = str(data["artist"].get("id", ""))
            artist_name = data["artist"].get("name", "")
        
        # Extract album info
        album_id = None
        album_title = None
        if data.get("album"):
            album_id = str(data["album"].get("id", ""))
            album_title = data["album"].get("title", "")
        
        return cls(
            id=str(data.get("id", "")),
            type="track",
            title=data.get("title", ""),
            title_short=data.get("title_short", data.get("title", "")),
            title_version=data.get("title_version"),
            isrc=data.get("isrc"),
            link=data.get("link"),
            duration=data.get("duration", 0),
            track_position=data.get("track_position"),
            disk_number=data.get("disk_number"),
            rank=data.get("rank"),
            release_date=release_date,
            explicit_lyrics=data.get("explicit_lyrics", False),
            explicit_content_lyrics=data.get("explicit_content_lyrics", 0),
            explicit_content_cover=data.get("explicit_content_cover", 0),
            preview=data.get("preview"),
            bpm=data.get("bpm"),
            gain=data.get("gain"),
            artist_id=artist_id,
            artist_name=artist_name,
            album_id=album_id,
            album_title=album_title,
            contributors=data.get("contributors", []),
            md5_image=data.get("md5_image"),
            available_countries=data.get("available_countries", []),
            readable=data.get("readable", True),
            media_version=data.get("media_version"),
            raw_data=data,
        )
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration:
            return "0:00"
        
        td = timedelta(seconds=self.duration)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    @property
    def full_title(self) -> str:
        """Get full title including version."""
        if self.title_version:
            return f"{self.title} ({self.title_version})"
        return self.title
    
    @property
    def cover_small(self) -> Optional[str]:
        """Get small cover URL."""
        if self.md5_image:
            return f"https://e-cdns-images.dzcdn.net/images/cover/{self.md5_image}/56x56-000000-80-0-0.jpg"
        elif self.album_id:
            return f"https://api.deezer.com/album/{self.album_id}/image?size=small"
        return None
    
    @property
    def cover_medium(self) -> Optional[str]:
        """Get medium cover URL."""
        if self.md5_image:
            return f"https://e-cdns-images.dzcdn.net/images/cover/{self.md5_image}/250x250-000000-80-0-0.jpg"
        elif self.album_id:
            return f"https://api.deezer.com/album/{self.album_id}/image?size=medium"
        return None
    
    @property
    def cover_large(self) -> Optional[str]:
        """Get large cover URL."""
        if self.md5_image:
            return f"https://e-cdns-images.dzcdn.net/images/cover/{self.md5_image}/500x500-000000-80-0-0.jpg"
        elif self.album_id:
            return f"https://api.deezer.com/album/{self.album_id}/image?size=big"
        return None
    
    @property
    def cover_xl(self) -> Optional[str]:
        """Get extra large cover URL."""
        if self.md5_image:
            return f"https://e-cdns-images.dzcdn.net/images/cover/{self.md5_image}/1000x1000-000000-80-0-0.jpg"
        elif self.album_id:
            return f"https://api.deezer.com/album/{self.album_id}/image?size=xl"
        return None
    
    def is_available_in(self, country_code: str) -> bool:
        """Check if track is available in a country."""
        if not self.available_countries:
            return True  # Assume available if no restrictions
        return country_code.upper() in self.available_countries
    
    @property
    def api_url(self) -> str:
        """Get API URL for this track."""
        return f"https://api.deezer.com/track/{self.id}"
    
    @property
    def web_url(self) -> str:
        """Get web URL for this track."""
        return f"https://www.deezer.com/track/{self.id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "artist_name": self.artist_name,
            "album_title": self.album_title,
            "duration": self.duration,
            "isrc": self.isrc,
        }