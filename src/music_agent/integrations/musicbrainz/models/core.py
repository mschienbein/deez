"""
Core MusicBrainz data models.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Artist:
    """Artist information."""
    id: str  # MBID (MusicBrainz ID)
    name: str
    sort_name: Optional[str] = None
    disambiguation: Optional[str] = None
    type: Optional[str] = None  # Person, Group, Orchestra, etc.
    gender: Optional[str] = None
    country: Optional[str] = None
    area: Optional[Dict[str, Any]] = None
    begin_date: Optional[date] = None
    end_date: Optional[date] = None
    life_span: Optional[Dict[str, Any]] = None
    aliases: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    rating: Optional[float] = None
    isnis: List[str] = field(default_factory=list)
    ipis: List[str] = field(default_factory=list)
    
    @property
    def is_active(self) -> bool:
        """Check if artist is still active."""
        return self.end_date is None


@dataclass
class Recording:
    """Recording (track) information."""
    id: str  # MBID
    title: str
    length: Optional[int] = None  # Duration in milliseconds
    disambiguation: Optional[str] = None
    artist_credit: List[Dict[str, Any]] = field(default_factory=list)
    releases: List[Dict[str, Any]] = field(default_factory=list)
    isrcs: List[str] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    rating: Optional[float] = None
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get duration in seconds."""
        if self.length is None:
            return None
        # Handle both int and string types
        length_ms = int(self.length) if isinstance(self.length, (int, str)) else 0
        return length_ms // 1000 if length_ms else None
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration (MM:SS)."""
        if not self.length:
            return ""
        # Handle both int and string types
        try:
            length_ms = int(self.length)
            seconds = length_ms // 1000
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        except (ValueError, TypeError):
            return ""


@dataclass
class Track:
    """Track on a release."""
    id: Optional[str] = None  # Track MBID (if available)
    position: Optional[int] = None
    number: Optional[str] = None
    title: str = ""
    length: Optional[int] = None
    recording_id: Optional[str] = None  # Recording MBID
    artist_credit: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Medium:
    """Physical medium (CD, vinyl, etc.) in a release."""
    position: int
    format: Optional[str] = None
    title: Optional[str] = None
    track_count: int = 0
    tracks: List[Track] = field(default_factory=list)


@dataclass
class Label:
    """Label information."""
    id: str  # MBID
    name: str
    sort_name: Optional[str] = None
    disambiguation: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None
    area: Optional[Dict[str, Any]] = None
    life_span: Optional[Dict[str, Any]] = None
    aliases: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    label_code: Optional[int] = None
    ipis: List[str] = field(default_factory=list)
    isnis: List[str] = field(default_factory=list)