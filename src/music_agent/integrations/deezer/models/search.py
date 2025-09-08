"""
Search models for Deezer.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SearchResult(Generic[T]):
    """Search result container."""
    
    data: List[T]
    total: int
    next: Optional[str] = None
    prev: Optional[str] = None
    
    @property
    def has_next(self) -> bool:
        """Check if there are more results."""
        return self.next is not None
    
    @property
    def has_prev(self) -> bool:
        """Check if there are previous results."""
        return self.prev is not None
    
    @property
    def count(self) -> int:
        """Get number of results in this page."""
        return len(self.data)


@dataclass
class SearchFilters:
    """Search filters for advanced queries."""
    
    # Basic filters
    artist: Optional[str] = None
    album: Optional[str] = None
    label: Optional[str] = None
    dur_min: Optional[int] = None  # Minimum duration in seconds
    dur_max: Optional[int] = None  # Maximum duration in seconds
    bpm_min: Optional[int] = None
    bpm_max: Optional[int] = None
    
    # Date filters (format: YYYY-MM-DD)
    date_min: Optional[str] = None
    date_max: Optional[str] = None
    
    # Quality filters
    explicit: Optional[bool] = None
    
    # Sorting
    order: Optional[str] = None  # RANKING, TRACK_ASC, TRACK_DESC, ARTIST_ASC, ARTIST_DESC, ALBUM_ASC, ALBUM_DESC, RATING_ASC, RATING_DESC, DURATION_ASC, DURATION_DESC
    
    def to_query_string(self) -> str:
        """Convert filters to Deezer search query string."""
        parts = []
        
        if self.artist:
            parts.append(f'artist:"{self.artist}"')
        if self.album:
            parts.append(f'album:"{self.album}"')
        if self.label:
            parts.append(f'label:"{self.label}"')
        if self.dur_min is not None:
            parts.append(f"dur_min:{self.dur_min}")
        if self.dur_max is not None:
            parts.append(f"dur_max:{self.dur_max}")
        if self.bpm_min is not None:
            parts.append(f"bpm_min:{self.bpm_min}")
        if self.bpm_max is not None:
            parts.append(f"bpm_max:{self.bpm_max}")
        if self.date_min:
            parts.append(f"date_min:{self.date_min}")
        if self.date_max:
            parts.append(f"date_max:{self.date_max}")
        
        return " ".join(parts)