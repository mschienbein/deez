"""
Release and ReleaseGroup models for MusicBrainz.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import date

from .core import Medium, Artist
from .enums import ReleaseType, ReleaseStatus


@dataclass
class Release:
    """Release information."""
    id: str  # MBID
    title: str
    status: Optional[ReleaseStatus] = None
    quality: Optional[str] = None
    disambiguation: Optional[str] = None
    packaging: Optional[str] = None
    barcode: Optional[str] = None
    release_date: Optional[date] = None
    country: Optional[str] = None
    artist_credit: List[Dict[str, Any]] = field(default_factory=list)
    label_info: List[Dict[str, Any]] = field(default_factory=list)
    media: List[Medium] = field(default_factory=list)
    release_group: Optional[Dict[str, Any]] = None
    tags: List[Dict[str, Any]] = field(default_factory=list)
    rating: Optional[float] = None
    cover_art_archive: Optional[Dict[str, bool]] = None
    text_representation: Optional[Dict[str, str]] = None
    
    @property
    def artist(self) -> str:
        """Get primary artist name."""
        if self.artist_credit:
            return self.artist_credit[0].get('name', 'Unknown Artist')
        return "Unknown Artist"
    
    @property
    def label(self) -> Optional[str]:
        """Get primary label name."""
        if self.label_info:
            label = self.label_info[0].get('label', {})
            return label.get('name') if isinstance(label, dict) else None
        return None
    
    @property
    def catalog_number(self) -> Optional[str]:
        """Get catalog number."""
        if self.label_info:
            return self.label_info[0].get('catalog_number')
        return None
    
    @property
    def track_count(self) -> int:
        """Get total track count."""
        return sum(medium.track_count for medium in self.media)
    
    @property
    def has_cover_art(self) -> bool:
        """Check if cover art is available."""
        if self.cover_art_archive:
            return self.cover_art_archive.get('artwork', False)
        return False


@dataclass
class ReleaseGroup:
    """Release group (master release) information."""
    id: str  # MBID
    title: str
    type: Optional[ReleaseType] = None
    primary_type: Optional[str] = None
    secondary_types: List[str] = field(default_factory=list)
    disambiguation: Optional[str] = None
    artist_credit: List[Dict[str, Any]] = field(default_factory=list)
    releases: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    rating: Optional[float] = None
    first_release_date: Optional[date] = None
    
    @property
    def artist(self) -> str:
        """Get primary artist name."""
        if self.artist_credit:
            return self.artist_credit[0].get('name', 'Unknown Artist')
        return "Unknown Artist"
    
    @property
    def release_count(self) -> int:
        """Get number of releases in this group."""
        return len(self.releases)