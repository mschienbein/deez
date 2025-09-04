"""
Search filters and sorting options for SoundCloud.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class SortOptions(Enum):
    """Available sort options for search results."""
    POPULARITY = "popularity"
    DATE = "date"
    LIKES = "likes"
    DURATION = "duration"
    FOLLOWERS = "followers"
    TRACKS = "tracks"
    RELEVANCE = "relevance"


class FilterBuilder:
    """Builder for constructing search filters."""
    
    def __init__(self):
        """Initialize filter builder."""
        self.filters: Dict[str, Any] = {}
    
    def genre(self, genre: str) -> "FilterBuilder":
        """Filter by genre."""
        self.filters["genre"] = genre
        return self
    
    def tags(self, tags: List[str]) -> "FilterBuilder":
        """Filter by tags."""
        self.filters["tags"] = tags
        return self
    
    def bpm_range(
        self,
        min_bpm: Optional[float] = None,
        max_bpm: Optional[float] = None
    ) -> "FilterBuilder":
        """Filter by BPM range."""
        if min_bpm is not None:
            self.filters["bpm_from"] = min_bpm
        if max_bpm is not None:
            self.filters["bpm_to"] = max_bpm
        return self
    
    def duration_range(
        self,
        min_ms: Optional[int] = None,
        max_ms: Optional[int] = None
    ) -> "FilterBuilder":
        """Filter by duration range (in milliseconds)."""
        if min_ms is not None:
            self.filters["duration_from"] = min_ms
        if max_ms is not None:
            self.filters["duration_to"] = max_ms
        return self
    
    def duration_minutes(
        self,
        min_minutes: Optional[float] = None,
        max_minutes: Optional[float] = None
    ) -> "FilterBuilder":
        """Filter by duration range (in minutes)."""
        if min_minutes is not None:
            self.filters["duration_from"] = int(min_minutes * 60 * 1000)
        if max_minutes is not None:
            self.filters["duration_to"] = int(max_minutes * 60 * 1000)
        return self
    
    def created_range(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> "FilterBuilder":
        """Filter by creation date range."""
        if from_date:
            self.filters["created_at_from"] = from_date.isoformat()
        if to_date:
            self.filters["created_at_to"] = to_date.isoformat()
        return self
    
    def created_after(self, date: datetime) -> "FilterBuilder":
        """Filter for content created after date."""
        self.filters["created_at_from"] = date.isoformat()
        return self
    
    def created_before(self, date: datetime) -> "FilterBuilder":
        """Filter for content created before date."""
        self.filters["created_at_to"] = date.isoformat()
        return self
    
    def license(self, license_type: str) -> "FilterBuilder":
        """Filter by license type."""
        self.filters["license"] = license_type
        return self
    
    def streamable(self, value: bool = True) -> "FilterBuilder":
        """Filter by streamable status."""
        self.filters["streamable"] = value
        return self
    
    def downloadable(self, value: bool = True) -> "FilterBuilder":
        """Filter by downloadable status."""
        self.filters["downloadable"] = value
        return self
    
    def private(self, value: bool = False) -> "FilterBuilder":
        """Filter by private status."""
        self.filters["private"] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the filter dictionary."""
        return self.filters
    
    def clear(self) -> "FilterBuilder":
        """Clear all filters."""
        self.filters = {}
        return self


class LicenseFilter(Enum):
    """Common Creative Commons licenses."""
    ALL_RIGHTS_RESERVED = "all-rights-reserved"
    CC_BY = "cc-by"
    CC_BY_SA = "cc-by-sa"
    CC_BY_NC = "cc-by-nc"
    CC_BY_NC_SA = "cc-by-nc-sa"
    CC_BY_NC_ND = "cc-by-nc-nd"
    CC_BY_ND = "cc-by-nd"
    CC0 = "cc0"
    NO_RIGHTS_RESERVED = "no-rights-reserved"


class GenreFilter(Enum):
    """Common SoundCloud genres."""
    ALTERNATIVE_ROCK = "Alternative Rock"
    AMBIENT = "Ambient"
    CLASSICAL = "Classical"
    COUNTRY = "Country"
    DANCE_EDM = "Dance & EDM"
    DANCEHALL = "Dancehall"
    DEEP_HOUSE = "Deep House"
    DISCO = "Disco"
    DRUM_BASS = "Drum & Bass"
    DUBSTEP = "Dubstep"
    ELECTRONIC = "Electronic"
    FOLK_SINGER = "Folk & Singer-Songwriter"
    HIP_HOP_RAP = "Hip-hop & Rap"
    HOUSE = "House"
    INDIE = "Indie"
    JAZZ_BLUES = "Jazz & Blues"
    LATIN = "Latin"
    METAL = "Metal"
    PIANO = "Piano"
    POP = "Pop"
    RB_SOUL = "R&B & Soul"
    REGGAE = "Reggae"
    REGGAETON = "Reggaeton"
    ROCK = "Rock"
    SOUNDTRACK = "Soundtrack"
    TECHNO = "Techno"
    TRANCE = "Trance"
    TRAP = "Trap"
    TRIPHOP = "Triphop"
    WORLD = "World"
    
    # Additional sub-genres
    AUDIOBOOKS = "Audiobooks"
    BUSINESS = "Business"
    COMEDY = "Comedy"
    ENTERTAINMENT = "Entertainment"
    LEARNING = "Learning"
    NEWS_POLITICS = "News & Politics"
    RELIGION_SPIRITUALITY = "Religion & Spirituality"
    SCIENCE = "Science"
    SPORTS = "Sports"
    STORYTELLING = "Storytelling"
    TECHNOLOGY = "Technology"


class DurationFilter:
    """Pre-defined duration filters."""
    
    VERY_SHORT = {"duration_to": 60000}  # < 1 minute
    SHORT = {"duration_from": 60000, "duration_to": 180000}  # 1-3 minutes
    MEDIUM = {"duration_from": 180000, "duration_to": 600000}  # 3-10 minutes
    LONG = {"duration_from": 600000, "duration_to": 3600000}  # 10-60 minutes
    VERY_LONG = {"duration_from": 3600000}  # > 60 minutes
    
    @staticmethod
    def custom(min_seconds: int = 0, max_seconds: Optional[int] = None) -> Dict:
        """Create custom duration filter."""
        filters = {"duration_from": min_seconds * 1000}
        if max_seconds:
            filters["duration_to"] = max_seconds * 1000
        return filters


class BPMFilter:
    """Pre-defined BPM filters for different music styles."""
    
    SLOW = {"bpm_from": 60, "bpm_to": 90}  # Slow tempo
    MODERATE = {"bpm_from": 90, "bpm_to": 120}  # Moderate tempo
    FAST = {"bpm_from": 120, "bpm_to": 150}  # Fast tempo
    VERY_FAST = {"bpm_from": 150, "bpm_to": 200}  # Very fast tempo
    
    # Genre-specific BPM ranges
    HIP_HOP = {"bpm_from": 70, "bpm_to": 100}
    HOUSE = {"bpm_from": 118, "bpm_to": 135}
    TECHNO = {"bpm_from": 120, "bpm_to": 150}
    DRUM_BASS = {"bpm_from": 160, "bpm_to": 180}
    DUBSTEP = {"bpm_from": 138, "bpm_to": 142}
    TRAP = {"bpm_from": 135, "bpm_to": 170}
    
    @staticmethod
    def custom(min_bpm: float, max_bpm: float) -> Dict:
        """Create custom BPM filter."""
        return {"bpm_from": min_bpm, "bpm_to": max_bpm}


__all__ = [
    "FilterBuilder",
    "SortOptions",
    "LicenseFilter",
    "GenreFilter",
    "DurationFilter",
    "BPMFilter",
]