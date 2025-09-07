"""
Core Beatport data models.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Artist:
    """Artist information."""
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None
    image: Optional[Dict[str, str]] = None  # Contains uri, width, height
    biography: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    soundcloud: Optional[str] = None
    instagram: Optional[str] = None
    
    @property
    def image_url(self) -> Optional[str]:
        """Get image URL if available."""
        return self.image.get('uri') if self.image else None


@dataclass
class Label:
    """Label information."""
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None
    image: Optional[Dict[str, str]] = None
    biography: Optional[str] = None
    
    @property
    def image_url(self) -> Optional[str]:
        """Get image URL if available."""
        return self.image.get('uri') if self.image else None


@dataclass
class Genre:
    """Genre information."""
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Key:
    """Musical key information."""
    id: int
    name: str  # e.g., "C minor", "A major"
    short_name: Optional[str] = None  # e.g., "Cm", "A"
    camelot: Optional[str] = None  # Camelot wheel notation


@dataclass
class Remixer:
    """Remixer information."""
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Waveform:
    """Track waveform data."""
    url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class Stream:
    """Audio stream information."""
    url: str
    format: str  # mp3, mp4, etc.
    quality: str  # 128, 320, etc.
    
    
@dataclass
class Price:
    """Price information."""
    currency: str  # USD, EUR, GBP
    value: float
    formatted: Optional[str] = None  # e.g., "$1.99"


@dataclass
class Track:
    """Track information."""
    id: int
    name: str
    mix: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    
    # Artists and credits
    artists: List[Artist] = field(default_factory=list)
    remixers: List[Remixer] = field(default_factory=list)
    
    # Release info
    label: Optional[Label] = None
    release: Optional['Release'] = None
    release_date: Optional[datetime] = None
    publish_date: Optional[datetime] = None
    
    # Music metadata
    genre: Optional[Genre] = None
    sub_genre: Optional[Genre] = None
    key: Optional[Key] = None
    bpm: Optional[int] = None
    length_ms: Optional[int] = None
    
    # Media
    image: Optional[Dict[str, str]] = None
    waveform: Optional[Waveform] = None
    preview: Optional[Stream] = None
    
    # Purchase info
    price: Optional[Price] = None
    exclusive: bool = False
    available: bool = True
    
    # Additional metadata
    isrc: Optional[str] = None
    catalog_number: Optional[str] = None
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (MM:SS)."""
        if not self.length_ms:
            return ""
        seconds = self.length_ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    
    @property
    def artist_names(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(a.name for a in self.artists)
    
    @property
    def image_url(self) -> Optional[str]:
        """Get image URL if available."""
        return self.image.get('uri') if self.image else None


@dataclass
class Release:
    """Release/album information."""
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None
    
    # Artists and label
    artists: List[Artist] = field(default_factory=list)
    label: Optional[Label] = None
    
    # Release info
    release_date: Optional[datetime] = None
    publish_date: Optional[datetime] = None
    catalog_number: Optional[str] = None
    upc: Optional[str] = None
    
    # Media
    image: Optional[Dict[str, str]] = None
    
    # Tracks
    tracks: List[Track] = field(default_factory=list)
    track_count: Optional[int] = None
    
    # Purchase info
    price: Optional[Price] = None
    exclusive: bool = False
    
    @property
    def artist_names(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(a.name for a in self.artists)
    
    @property
    def image_url(self) -> Optional[str]:
        """Get image URL if available."""
        return self.image.get('uri') if self.image else None


@dataclass
class ChartTrack:
    """Track in a chart with position."""
    position: int
    track: Track
    change: Optional[int] = None  # Position change from last week
    peak_position: Optional[int] = None
    weeks_on_chart: Optional[int] = None


@dataclass
class Chart:
    """Chart information."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    
    # Chart metadata
    genre: Optional[Genre] = None
    published_date: Optional[datetime] = None
    
    # Tracks
    tracks: List[ChartTrack] = field(default_factory=list)
    
    @property
    def track_count(self) -> int:
        """Get number of tracks in chart."""
        return len(self.tracks)