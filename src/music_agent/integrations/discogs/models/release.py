"""
Release and Master models for Discogs.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .core import Artist, Label, Track, Image


@dataclass
class Release:
    """Release information."""
    id: int
    title: str
    resource_url: str
    uri: Optional[str] = None
    status: Optional[str] = None
    year: Optional[int] = None
    format: Optional[str] = None
    format_quantity: Optional[int] = None
    formats: List[Dict[str, Any]] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    artists: List[Artist] = field(default_factory=list)
    artists_sort: Optional[str] = None
    extraartists: List[Artist] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    country: Optional[str] = None
    released: Optional[str] = None
    released_formatted: Optional[str] = None
    notes: Optional[str] = None
    data_quality: Optional[str] = None
    master_id: Optional[int] = None
    master_url: Optional[str] = None
    tracklist: List[Track] = field(default_factory=list)
    identifiers: List[Dict[str, Any]] = field(default_factory=list)
    videos: List[Dict[str, Any]] = field(default_factory=list)
    companies: List[Dict[str, Any]] = field(default_factory=list)
    series: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    thumb: Optional[str] = None
    estimated_weight: Optional[int] = None
    community: Optional[Dict[str, Any]] = None
    marketplace_stats: Optional[Dict[str, Any]] = None
    
    @property
    def main_artists(self) -> str:
        """Get main artists as string."""
        if self.artists:
            return ", ".join([a.name for a in self.artists])
        return "Unknown Artist"
    
    @property
    def artist(self) -> str:
        """Alias for main_artists for compatibility."""
        return self.main_artists
    
    @property
    def catalog_number(self) -> Optional[str]:
        """Get primary catalog number."""
        if self.labels:
            return self.labels[0].catno
        return None


@dataclass
class Master:
    """Master release information."""
    id: int
    title: str
    resource_url: str
    uri: Optional[str] = None
    versions_url: Optional[str] = None
    main_release: Optional[int] = None
    main_release_url: Optional[str] = None
    year: Optional[int] = None
    artists: List[Artist] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    tracklist: List[Track] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    videos: List[Dict[str, Any]] = field(default_factory=list)
    data_quality: Optional[str] = None
    num_for_sale: Optional[int] = None
    lowest_price: Optional[float] = None