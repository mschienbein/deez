"""
Universal Track Metadata Model

Comprehensive metadata schema covering all integration sources.
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class TrackQuality(Enum):
    """Audio quality classification."""
    UNKNOWN = "unknown"
    LOW = "low"              # <128kbps MP3
    MEDIUM = "medium"        # 128-256kbps MP3  
    HIGH = "high"            # 320kbps MP3, 256kbps AAC
    LOSSLESS = "lossless"    # FLAC, WAV, ALAC
    MASTER = "master"        # High-res audio (24bit/96kHz+)


class TrackStatus(Enum):
    """Research and processing status."""
    DISCOVERED = "discovered"        # Found but not analyzed
    RESEARCHING = "researching"      # Currently being analyzed
    SOLVED = "solved"               # Complete with download/purchase option
    DOWNLOADED = "downloaded"       # Available locally
    SYNCED = "synced"              # Synced to Rekordbox
    FAILED = "failed"              # Research failed
    DUPLICATE = "duplicate"        # Duplicate of existing track


@dataclass
class ArtworkInfo:
    """Artwork metadata."""
    source: str                    # Platform/source
    url: str                       # URL to artwork
    size: str                      # Resolution (e.g., "500x500")
    format: str = "jpg"           # Image format
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    local_path: Optional[str] = None
    priority: int = 100           # Lower is better


@dataclass
class PlatformMetadata:
    """Platform-specific metadata container."""
    platform: str
    track_id: str
    url: Optional[str] = None
    preview_url: Optional[str] = None
    download_url: Optional[str] = None
    purchase_url: Optional[str] = None
    confidence_score: float = 0.0
    extra_data: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UniversalTrackMetadata:
    """Universal track metadata schema covering all integration sources."""
    
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    artist: str = ""
    album: Optional[str] = None
    
    # Additional artists/contributors
    featured_artists: List[str] = field(default_factory=list)
    remixers: List[str] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)
    composers: List[str] = field(default_factory=list)
    writers: List[str] = field(default_factory=list)
    
    # Release information
    label: Optional[str] = None
    catalog_number: Optional[str] = None
    release_date: Optional[datetime] = None
    original_release_date: Optional[datetime] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    total_tracks: Optional[int] = None
    total_discs: Optional[int] = None
    
    # Classification
    genre: Optional[str] = None
    sub_genres: List[str] = field(default_factory=list)
    style: Optional[str] = None
    mood: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Technical data
    duration_ms: Optional[int] = None
    bpm: Optional[float] = None
    key: Optional[str] = None           # Musical key (A, Bb, C#m, etc.)
    key_camelot: Optional[str] = None   # Camelot wheel notation (8A, 5B, etc.)
    key_open_key: Optional[str] = None  # Open Key notation (1m, 10d, etc.)
    time_signature: Optional[str] = None
    
    # Audio quality
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None        # MP3, FLAC, WAV, AAC
    quality: TrackQuality = TrackQuality.UNKNOWN
    codec: Optional[str] = None
    bit_depth: Optional[int] = None
    
    # Identifiers
    isrc: Optional[str] = None
    upc: Optional[str] = None
    ean: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    musicbrainz_recording_id: Optional[str] = None
    discogs_master_id: Optional[int] = None
    discogs_release_id: Optional[int] = None
    spotify_id: Optional[str] = None
    spotify_uri: Optional[str] = None
    soundcloud_id: Optional[str] = None
    beatport_id: Optional[int] = None
    deezer_id: Optional[str] = None
    youtube_id: Optional[str] = None
    
    # Platform data
    platform_data: List[PlatformMetadata] = field(default_factory=list)
    
    # Artwork
    artwork: List[ArtworkInfo] = field(default_factory=list)
    primary_artwork_url: Optional[str] = None
    primary_artwork_path: Optional[str] = None
    
    # Audio features (Spotify-style)
    energy: Optional[float] = None        # 0.0-1.0 energy level
    danceability: Optional[float] = None  # 0.0-1.0
    valence: Optional[float] = None       # 0.0-1.0 musical positivity
    acousticness: Optional[float] = None  # 0.0-1.0
    instrumentalness: Optional[float] = None  # 0.0-1.0
    liveness: Optional[float] = None      # 0.0-1.0
    speechiness: Optional[float] = None   # 0.0-1.0
    loudness: Optional[float] = None      # dB
    
    # User/DJ data
    rating: Optional[int] = None          # 1-5 stars
    color: Optional[int] = None           # Rekordbox color tag
    play_count: Optional[int] = None
    last_played: Optional[datetime] = None
    comments: Optional[str] = None
    grouping: Optional[str] = None
    
    # Lyrics
    lyrics: Optional[str] = None
    lyrics_language: Optional[str] = None
    has_explicit_lyrics: Optional[bool] = None
    
    # Research status
    status: TrackStatus = TrackStatus.DISCOVERED
    research_sources: List[str] = field(default_factory=list)  # Which platforms searched
    best_download_source: Optional[str] = None
    best_quality_available: TrackQuality = TrackQuality.UNKNOWN
    cheapest_purchase_option: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0       # Overall metadata confidence
    
    # Timestamps
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_researched_at: Optional[datetime] = None
    solved_at: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None
    
    # File information (when downloaded)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    file_modified: Optional[datetime] = None
    
    # Rekordbox sync
    rekordbox_synced: bool = False
    rekordbox_sync_at: Optional[datetime] = None
    rekordbox_id: Optional[str] = None
    rekordbox_content_id: Optional[int] = None
    
    # DJ-specific data (from Rekordbox)
    beat_grid_locked: Optional[bool] = None
    hot_cues: List[Dict[str, Any]] = field(default_factory=list)
    memory_cues: List[Dict[str, Any]] = field(default_factory=list)
    loops: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_platform_data(self, platform: str, track_id: str, **kwargs) -> None:
        """Add or update platform-specific data."""
        # Check if platform data already exists
        for pd in self.platform_data:
            if pd.platform == platform:
                pd.track_id = track_id
                pd.last_updated = datetime.utcnow()
                for key, value in kwargs.items():
                    if hasattr(pd, key):
                        setattr(pd, key, value)
                    else:
                        pd.extra_data[key] = value
                return
        
        # Add new platform data
        self.platform_data.append(PlatformMetadata(
            platform=platform,
            track_id=track_id,
            **kwargs
        ))
    
    def get_platform_data(self, platform: str) -> Optional[PlatformMetadata]:
        """Get platform-specific data."""
        for pd in self.platform_data:
            if pd.platform == platform:
                return pd
        return None
    
    def add_artwork(self, source: str, url: str, size: str, **kwargs) -> None:
        """Add artwork information."""
        self.artwork.append(ArtworkInfo(
            source=source,
            url=url,
            size=size,
            **kwargs
        ))
        
        # Sort by priority and size
        self.artwork.sort(key=lambda a: (a.priority, -(a.width or 0)))
        
        # Update primary artwork
        if self.artwork and not self.primary_artwork_url:
            self.primary_artwork_url = self.artwork[0].url
    
    def get_best_artwork(self, min_size: int = 500) -> Optional[ArtworkInfo]:
        """Get best available artwork above minimum size."""
        for art in self.artwork:
            if art.width and art.width >= min_size:
                return art
        return self.artwork[0] if self.artwork else None
    
    def calculate_confidence_score(self) -> float:
        """Calculate overall metadata confidence score (0.0-1.0)."""
        score = 0.0
        weights = {}
        
        # Core fields (40%)
        core_fields = ['title', 'artist', 'duration_ms', 'album']
        core_complete = sum(1 for f in core_fields if getattr(self, f))
        weights['core'] = (core_complete / len(core_fields), 0.4)
        
        # Technical data (20%)
        tech_fields = ['bpm', 'key', 'genre', 'bitrate']
        tech_complete = sum(1 for f in tech_fields if getattr(self, f))
        weights['technical'] = (tech_complete / len(tech_fields), 0.2)
        
        # Identifiers (15%)
        id_fields = ['isrc', 'musicbrainz_id', 'spotify_id', 'beatport_id']
        id_complete = sum(1 for f in id_fields if getattr(self, f))
        weights['identifiers'] = (min(id_complete / 2, 1.0), 0.15)
        
        # Platform coverage (15%)
        platform_count = len(self.platform_data)
        weights['platforms'] = (min(platform_count / 3, 1.0), 0.15)
        
        # Artwork (10%)
        has_artwork = 1.0 if self.artwork else 0.0
        weights['artwork'] = (has_artwork, 0.1)
        
        # Calculate weighted score
        for category, (completion, weight) in weights.items():
            score += completion * weight
        
        self.confidence_score = round(score, 2)
        return self.confidence_score
    
    def is_complete(self, threshold: float = 0.7) -> bool:
        """Check if metadata meets completeness threshold."""
        return self.calculate_confidence_score() >= threshold
    
    def merge(self, other: 'UniversalTrackMetadata', prefer_other: bool = False) -> None:
        """Merge another metadata object into this one."""
        # Simple fields - prefer non-None values
        simple_fields = [
            'title', 'artist', 'album', 'label', 'catalog_number',
            'genre', 'style', 'mood', 'duration_ms', 'bpm', 'key',
            'bitrate', 'sample_rate', 'format', 'isrc', 'upc'
        ]
        
        for field in simple_fields:
            other_val = getattr(other, field)
            self_val = getattr(self, field)
            
            if other_val is not None:
                if self_val is None or prefer_other:
                    setattr(self, field, other_val)
        
        # List fields - combine unique values
        list_fields = [
            'featured_artists', 'remixers', 'producers', 'composers',
            'writers', 'sub_genres', 'tags', 'research_sources'
        ]
        
        for field in list_fields:
            self_list = getattr(self, field)
            other_list = getattr(other, field)
            combined = list(set(self_list + other_list))
            setattr(self, field, combined)
        
        # Platform data - merge
        for pd in other.platform_data:
            self.add_platform_data(
                pd.platform,
                pd.track_id,
                url=pd.url,
                preview_url=pd.preview_url,
                download_url=pd.download_url,
                purchase_url=pd.purchase_url,
                confidence_score=pd.confidence_score,
                extra_data=pd.extra_data
            )
        
        # Artwork - merge
        for art in other.artwork:
            # Check if artwork already exists
            exists = any(
                a.url == art.url for a in self.artwork
            )
            if not exists:
                self.artwork.append(art)
        
        # Sort artwork by priority
        self.artwork.sort(key=lambda a: (a.priority, -(a.width or 0)))
        
        # Update confidence score
        self.calculate_confidence_score()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {}
        
        for field_name, field_value in self.__dict__.items():
            if field_value is None:
                continue
            
            if isinstance(field_value, (datetime,)):
                data[field_name] = field_value.isoformat()
            elif isinstance(field_value, Enum):
                data[field_name] = field_value.value
            elif isinstance(field_value, list):
                if field_value:  # Only include non-empty lists
                    if all(isinstance(item, (str, int, float, bool)) for item in field_value):
                        data[field_name] = field_value
                    else:
                        # Handle complex objects in lists
                        data[field_name] = [
                            item.to_dict() if hasattr(item, 'to_dict') else item.__dict__
                            for item in field_value
                        ]
            else:
                data[field_name] = field_value
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniversalTrackMetadata':
        """Create from dictionary."""
        # Convert string dates back to datetime
        date_fields = [
            'release_date', 'original_release_date', 'discovered_at',
            'last_researched_at', 'solved_at', 'downloaded_at', 'synced_at',
            'rekordbox_sync_at', 'file_modified', 'last_played'
        ]
        
        for field in date_fields:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert quality and status enums
        if 'quality' in data:
            data['quality'] = TrackQuality(data['quality'])
        if 'status' in data:
            data['status'] = TrackStatus(data['status'])
        
        # Convert platform data
        if 'platform_data' in data:
            data['platform_data'] = [
                PlatformMetadata(**pd) if isinstance(pd, dict) else pd
                for pd in data['platform_data']
            ]
        
        # Convert artwork
        if 'artwork' in data:
            data['artwork'] = [
                ArtworkInfo(**art) if isinstance(art, dict) else art
                for art in data['artwork']
            ]
        
        return cls(**data)