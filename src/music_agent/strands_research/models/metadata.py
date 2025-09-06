"""
Data models for track metadata and research results.

Using Pydantic for validation since Strands uses it internally.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TrackQuality(str, Enum):
    """Audio quality levels."""
    LOSSLESS = "lossless"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class PlatformResult(BaseModel):
    """Result from a single platform search."""
    platform: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    search_query: Optional[str] = None


class TrackMetadata(BaseModel):
    """Unified track metadata model."""
    # Core identification
    title: str = ""
    artist: str = ""
    album: Optional[str] = None
    mix_name: Optional[str] = None
    
    # Technical metadata
    duration_ms: Optional[int] = None
    bpm: Optional[float] = None
    key: Optional[str] = None
    genre: Optional[str] = None
    sub_genres: List[str] = Field(default_factory=list)
    
    # Release information
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    release_date: Optional[str] = None
    year: Optional[int] = None
    
    # Identifiers
    isrc: Optional[str] = None
    spotify_id: Optional[str] = None
    beatport_id: Optional[str] = None
    discogs_id: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    
    # Credits
    remixers: List[str] = Field(default_factory=list)
    producers: List[str] = Field(default_factory=list)
    composers: List[str] = Field(default_factory=list)
    featured_artists: List[str] = Field(default_factory=list)
    
    # Audio features (0.0-1.0)
    energy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    danceability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    valence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    acousticness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    instrumentalness: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Metadata about the metadata
    sources: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    
    def calculate_completeness(self) -> float:
        """Calculate metadata completeness score."""
        required_fields = [
            'title', 'artist', 'duration_ms', 'bpm', 
            'key', 'genre', 'label', 'release_date'
        ]
        
        present = sum(
            1 for field in required_fields
            if getattr(self, field) is not None and getattr(self, field) != ""
        )
        
        self.completeness = present / len(required_fields)
        return self.completeness


class ConflictReport(BaseModel):
    """Report of a metadata conflict between sources."""
    field: str
    values: List[tuple[str, Any]]  # [(source, value), ...]
    resolution: Optional[Any] = None
    resolution_reason: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class QualityReport(BaseModel):
    """Quality assessment report for metadata."""
    audio_quality: TrackQuality
    metadata_completeness: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    quality_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    meets_requirements: bool = False
    conflicts: List[ConflictReport] = Field(default_factory=list)


class AcquisitionOption(BaseModel):
    """Option for acquiring a track."""
    source: str
    type: str  # 'purchase', 'stream', 'download', 'vinyl'
    quality: TrackQuality
    price: Optional[float] = None
    currency: Optional[str] = None
    url: Optional[str] = None
    requires_subscription: bool = False
    region_restricted: bool = False
    availability: str = "available"
    formats: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ResearchResult(BaseModel):
    """Complete research result for a track."""
    query: str
    success: bool
    solved: bool = False
    metadata: Optional[TrackMetadata] = None
    quality_report: Optional[QualityReport] = None
    acquisition_options: List[AcquisitionOption] = Field(default_factory=list)
    platform_results: Dict[str, PlatformResult] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    solve_reason: Optional[str] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    
    def is_solved(self) -> bool:
        """Determine if track is solved based on criteria."""
        if not self.metadata or not self.quality_report:
            return False
        
        self.solved = (
            self.quality_report.metadata_completeness >= 0.8 and
            self.quality_report.confidence_score >= 0.7 and
            len(self.metadata.sources) >= 2 and
            len(self.acquisition_options) > 0 and
            any(opt.quality in [TrackQuality.LOSSLESS, TrackQuality.HIGH] 
                for opt in self.acquisition_options)
        )
        
        if self.solved:
            self.solve_reason = (
                f"Track resolved with {self.quality_report.confidence_score:.0%} confidence. "
                f"Found on {len(self.metadata.sources)} platforms with "
                f"{len(self.acquisition_options)} acquisition options."
            )
        else:
            issues = []
            if self.quality_report.metadata_completeness < 0.8:
                issues.append(f"completeness only {self.quality_report.metadata_completeness:.0%}")
            if self.quality_report.confidence_score < 0.7:
                issues.append(f"confidence only {self.quality_report.confidence_score:.0%}")
            if len(self.metadata.sources) < 2:
                issues.append("insufficient sources")
            if not self.acquisition_options:
                issues.append("no acquisition options")
            
            self.solve_reason = f"Not solved: {', '.join(issues)}"
        
        return self.solved