"""
Search-related models for Beatport API.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .core import Track, Release, Artist, Label
from .enums import SearchType, SortField, SortDirection


@dataclass
class SearchQuery:
    """Search query parameters."""
    query: str
    search_type: SearchType = SearchType.TRACKS
    
    # Filters
    genre_id: Optional[int] = None
    sub_genre_id: Optional[int] = None
    artist_id: Optional[int] = None
    label_id: Optional[int] = None
    
    # Date filters
    release_date_start: Optional[str] = None  # YYYY-MM-DD
    release_date_end: Optional[str] = None
    
    # BPM range
    bpm_low: Optional[int] = None
    bpm_high: Optional[int] = None
    
    # Key filter
    key_id: Optional[int] = None
    
    # Sorting
    sort_by: Optional[SortField] = None
    sort_direction: SortDirection = SortDirection.DESC
    
    # Pagination
    page: int = 1
    per_page: int = 25
    
    def to_params(self) -> Dict[str, Any]:
        """Convert to API parameters."""
        params = {
            'q': self.query,
            'page': self.page,
            'per_page': self.per_page
        }
        
        if self.genre_id:
            params['genre_id'] = self.genre_id
        if self.sub_genre_id:
            params['sub_genre_id'] = self.sub_genre_id
        if self.artist_id:
            params['artist_id'] = self.artist_id
        if self.label_id:
            params['label_id'] = self.label_id
            
        if self.release_date_start:
            params['release_date_start'] = self.release_date_start
        if self.release_date_end:
            params['release_date_end'] = self.release_date_end
            
        if self.bpm_low:
            params['bpm_low'] = self.bpm_low
        if self.bpm_high:
            params['bpm_high'] = self.bpm_high
            
        if self.key_id:
            params['key_id'] = self.key_id
            
        if self.sort_by:
            params['sort'] = f"{self.sort_by.value}:{self.sort_direction.value}"
            
        return params


@dataclass
class SearchResult:
    """Search result container."""
    query: SearchQuery
    total: int
    page: int
    per_page: int
    
    # Results based on search type
    tracks: List[Track] = field(default_factory=list)
    releases: List[Release] = field(default_factory=list)
    artists: List[Artist] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    
    @property
    def has_more(self) -> bool:
        """Check if there are more pages."""
        return self.page * self.per_page < self.total
    
    @property
    def total_pages(self) -> int:
        """Get total number of pages."""
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def items(self) -> List:
        """Get items based on search type."""
        if self.query.search_type == SearchType.TRACKS:
            return self.tracks
        elif self.query.search_type == SearchType.RELEASES:
            return self.releases
        elif self.query.search_type == SearchType.ARTISTS:
            return self.artists
        elif self.query.search_type == SearchType.LABELS:
            return self.labels
        return []


@dataclass
class AdvancedSearchFilters:
    """Advanced search filters."""
    # Price range
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    
    # Length range (in seconds)
    length_min: Optional[int] = None
    length_max: Optional[int] = None
    
    # Only exclusives
    exclusive_only: bool = False
    
    # Only available tracks
    available_only: bool = True
    
    # Has preview
    has_preview: bool = False
    
    # Has waveform
    has_waveform: bool = False