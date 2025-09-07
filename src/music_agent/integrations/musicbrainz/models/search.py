"""
Search result models for MusicBrainz.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .enums import EntityType


@dataclass
class SearchResult:
    """Generic search result container."""
    type: EntityType
    id: str  # MBID
    score: int  # Match score (0-100)
    title: Optional[str] = None
    name: Optional[str] = None
    artist: Optional[str] = None
    disambiguation: Optional[str] = None
    country: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    barcode: Optional[str] = None
    catalog_number: Optional[str] = None
    label: Optional[str] = None
    track_count: Optional[int] = None
    format: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def display_title(self) -> str:
        """Get display title based on entity type."""
        if self.type in [EntityType.ARTIST, EntityType.LABEL]:
            return self.name or "Unknown"
        else:
            return self.title or "Unknown"
    
    @property
    def display_subtitle(self) -> str:
        """Get subtitle for display."""
        parts = []
        if self.artist and self.type != EntityType.ARTIST:
            parts.append(self.artist)
        if self.date:
            parts.append(f"({self.date[:4]})" if len(self.date) >= 4 else self.date)
        if self.disambiguation:
            parts.append(f"[{self.disambiguation}]")
        return " ".join(parts)


@dataclass
class SearchResults:
    """Container for paginated search results."""
    results: List[SearchResult]
    total_count: int
    offset: int
    limit: int
    
    @property
    def has_more(self) -> bool:
        """Check if more results are available."""
        return (self.offset + len(self.results)) < self.total_count
    
    @property
    def next_offset(self) -> int:
        """Get offset for next page."""
        return self.offset + self.limit