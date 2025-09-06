# Music Metadata Research & Management System Plan

## Overview

Design a comprehensive system for collecting, normalizing, and managing music metadata from multiple sources with the goal of creating a complete database that can sync with Rekordbox and provide intelligent track tagging similar to MP3Tag.

## Goals

1. **Comprehensive Metadata Collection**: Gather all available metadata from 13+ integrations
2. **Intelligent Track Resolution**: Find best download source or purchase options
3. **Quality Assessment**: Mark tracks as 'solved' when they meet quality requirements
4. **Rekordbox Sync**: Complete metadata transfer to Rekordbox database
5. **Smart Tagging**: MP3Tag-like intelligent track tagging with album art

## Rekordbox Database Schema Analysis

### Core Tables & Fields
Based on research of Rekordbox database structure:

```sql
-- Core track metadata (DjmdContent table)
- ID (Primary Key)
- Title
- Artist Name  
- Album
- Genre
- Label
- Remixer
- Composer
- Comments
- Grouping
- BPM (analyzed)
- Key (analyzed) 
- Length (duration)
- File Path
- File Size
- Bitrate
- Sample Rate
- Date Added
- Date Created
- Release Date
- Track Number
- Disc Number
- Rating (1-5 stars)
- Play Count
- Last Played
- Color (track color coding)
- Energy (analyzed energy level)
- Artwork ID (reference)

-- DJ-specific metadata
- Beat Grid Data
- Cue Points (Hot Cues)
- Loop Points
- Waveform Data
- Memory Cues
- Tempo Range
- Mix In/Out Points

-- My Tag System (custom categorization)
- Genre Tags
- Component Tags  
- Situation Tags
- Custom Tags

-- Analysis Data
- Dynamic Range
- Loudness
- Musical Key Confidence
- BPM Confidence
- Beat Grid Locked
```

### Related Tables
```sql
DjmdArtist - Artist information
DjmdAlbum - Album information  
DjmdGenre - Genre classification
DjmdLabel - Record label data
DjmdPlaylist - Playlist data
DjmdArtwork - Album artwork
```

## Unified Metadata Schema

### Proposed Universal Track Model

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class TrackQuality(Enum):
    UNKNOWN = "unknown"
    LOW = "low"          # <128kbps MP3
    MEDIUM = "medium"    # 128-256kbps MP3  
    HIGH = "high"        # 320kbps MP3, 256kbps AAC
    LOSSLESS = "lossless" # FLAC, WAV, ALAC

class TrackStatus(Enum):
    DISCOVERED = "discovered"     # Found but not analyzed
    RESEARCHING = "researching"   # Currently being analyzed
    SOLVED = "solved"            # Complete with download/purchase option
    DOWNLOADED = "downloaded"    # Available locally
    SYNCED = "synced"           # Synced to Rekordbox

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
    time_signature: Optional[str] = None
    
    # Audio quality
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None        # MP3, FLAC, WAV, AAC
    quality: TrackQuality = TrackQuality.UNKNOWN
    
    # Identifiers
    isrc: Optional[str] = None
    upc: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    discogs_master_id: Optional[int] = None
    discogs_release_id: Optional[int] = None
    spotify_id: Optional[str] = None
    soundcloud_id: Optional[str] = None
    beatport_id: Optional[int] = None
    
    # URLs and sources
    platform_urls: Dict[str, str] = field(default_factory=dict)  # Platform -> URL
    preview_urls: Dict[str, str] = field(default_factory=dict)   # Platform -> Preview URL
    download_urls: Dict[str, str] = field(default_factory=dict)  # Platform -> Download URL
    purchase_urls: Dict[str, str] = field(default_factory=dict)  # Platform -> Purchase URL
    
    # Artwork
    artwork_urls: Dict[str, str] = field(default_factory=dict)   # Size -> URL
    artwork_local_path: Optional[str] = None
    
    # User/DJ data
    rating: Optional[int] = None        # 1-5 stars
    energy: Optional[int] = None        # 1-10 energy level
    danceability: Optional[float] = None # 0.0-1.0 from Spotify
    valence: Optional[float] = None     # 0.0-1.0 musical positivity
    popularity: Optional[int] = None    # Platform popularity scores
    
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
    
    # Timestamps
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_researched_at: Optional[datetime] = None
    solved_at: Optional[datetime] = None
    
    # Platform-specific metadata
    platform_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # File information (when downloaded)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    
    # Rekordbox sync
    rekordbox_synced: bool = False
    rekordbox_sync_at: Optional[datetime] = None
    rekordbox_id: Optional[str] = None
```

## Integration Source Coverage

### Metadata Available by Integration

```python
INTEGRATION_METADATA_COVERAGE = {
    "soundcloud": {
        "core": ["title", "artist", "duration_ms", "genre", "tags"],
        "technical": ["bitrate", "format"],
        "urls": ["platform_urls", "preview_urls", "download_urls"],
        "user": ["popularity", "rating"],
        "unique": ["waveform_url", "repost_count", "comment_count"]
    },
    
    "spotify": {
        "core": ["title", "artist", "album", "duration_ms", "popularity"],
        "release": ["release_date", "track_number", "total_tracks"],
        "analysis": ["bpm", "key", "energy", "danceability", "valence"],
        "ids": ["spotify_id", "isrc"],
        "unique": ["acousticness", "instrumentalness", "liveness", "speechiness"]
    },
    
    "beatport": {
        "core": ["title", "artist", "label", "genre", "sub_genres"],
        "technical": ["bpm", "key", "duration_ms"],
        "release": ["release_date", "catalog_number", "remixers"],
        "urls": ["preview_urls", "purchase_urls"],
        "unique": ["energy_rating", "chart_position", "release_type"]
    },
    
    "discogs": {
        "core": ["title", "artist", "album", "label", "genre", "style"],
        "release": ["release_date", "catalog_number", "track_number", "total_tracks"],
        "contributors": ["producers", "composers", "writers", "featured_artists"],
        "ids": ["discogs_master_id", "discogs_release_id", "upc"],
        "unique": ["pressing_info", "matrix_number", "credits", "notes"]
    },
    
    "musicbrainz": {
        "core": ["title", "artist", "album", "duration_ms"],
        "release": ["release_date", "track_number", "label"],
        "ids": ["musicbrainz_id", "isrc"],
        "contributors": ["composers", "writers", "producers"],
        "unique": ["recording_relationships", "work_relationships"]
    },
    
    "genius": {
        "core": ["title", "artist", "album"],
        "lyrics": ["lyrics", "lyrics_language", "has_explicit_lyrics"],
        "contributors": ["writers", "producers", "featured_artists"],
        "unique": ["annotations", "song_relationships", "verified_lyrics"]
    },
    
    "last.fm": {
        "core": ["title", "artist", "album", "duration_ms"],
        "classification": ["tags", "genre"],
        "user": ["popularity", "play_count"],
        "unique": ["similar_tracks", "top_listeners", "scrobble_count"]
    }
}
```

## Album Artwork Collection Strategy

### Primary Sources (Based on MP3Tag Analysis)
1. **MusicBrainz Cover Art Archive** - Free, open source
2. **Discogs** - Comprehensive release artwork
3. **Spotify** - High quality modern releases  
4. **Beatport** - Electronic music artwork
5. **Last.fm** - Community-sourced artwork
6. **iTunes/Apple Music** - High resolution when available

### Artwork Quality Hierarchy
```python
ARTWORK_SOURCES = [
    {"source": "musicbrainz", "priority": 1, "max_size": "1200x1200", "format": "jpg"},
    {"source": "discogs", "priority": 2, "max_size": "1200x1200", "format": "jpg"},
    {"source": "spotify", "priority": 3, "max_size": "640x640", "format": "jpg"},
    {"source": "beatport", "priority": 4, "max_size": "500x500", "format": "jpg"},
    {"source": "soundcloud", "priority": 5, "max_size": "500x500", "format": "jpg"},
    {"source": "lastfm", "priority": 6, "max_size": "300x300", "format": "jpg"},
]

# Preferred sizes for different use cases
ARTWORK_SIZES = {
    "thumbnail": "150x150",
    "medium": "500x500", 
    "large": "1000x1000",
    "original": "max_available"
}
```

## Music Deep Research Agent Architecture

### Research Pipeline
```python
class MusicResearchAgent:
    """Deep research agent for comprehensive track metadata collection."""
    
    async def research_track(self, query: str) -> UniversalTrackMetadata:
        """
        Complete research pipeline for a track.
        
        Steps:
        1. Multi-platform search
        2. Metadata collection & normalization
        3. Quality assessment
        4. Download/purchase option analysis
        5. Artwork collection
        6. Status determination
        """
        
    async def search_phase(self, query: str) -> Dict[str, List[Any]]:
        """Search across all available platforms."""
        
    async def metadata_collection_phase(self, candidates: Dict) -> UniversalTrackMetadata:
        """Collect and merge metadata from all sources."""
        
    async def quality_assessment_phase(self, metadata: UniversalTrackMetadata) -> None:
        """Assess available quality options."""
        
    async def artwork_collection_phase(self, metadata: UniversalTrackMetadata) -> None:
        """Collect artwork from multiple sources."""
        
    async def resolution_phase(self, metadata: UniversalTrackMetadata) -> None:
        """Determine best download/purchase options."""
```

### Research Strategy
1. **Parallel Search**: Search all platforms simultaneously
2. **Metadata Merging**: Intelligent merging of conflicting data
3. **Confidence Scoring**: Rate reliability of each data source
4. **Quality Prioritization**: Prefer lossless > high bitrate > lower quality
5. **Cost Analysis**: Find cheapest purchase options when downloads unavailable

## Database Schema

### Primary Tables
```sql
-- Core track metadata
CREATE TABLE tracks (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    artist VARCHAR(500) NOT NULL,
    album VARCHAR(500),
    duration_ms INTEGER,
    bpm DECIMAL(6,2),
    key VARCHAR(10),
    genre VARCHAR(100),
    status VARCHAR(20) DEFAULT 'discovered',
    quality VARCHAR(20) DEFAULT 'unknown',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    solved_at TIMESTAMP,
    -- ... all UniversalTrackMetadata fields
);

-- Platform-specific data
CREATE TABLE platform_data (
    track_id VARCHAR(36),
    platform VARCHAR(50),
    platform_track_id VARCHAR(100),
    url VARCHAR(1000),
    preview_url VARCHAR(1000),
    download_url VARCHAR(1000),
    purchase_url VARCHAR(1000),
    metadata_json TEXT, -- Platform-specific extra data
    confidence_score DECIMAL(3,2),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- Artwork storage
CREATE TABLE artwork (
    id VARCHAR(36) PRIMARY KEY,
    track_id VARCHAR(36),
    source VARCHAR(50),
    size VARCHAR(20),
    format VARCHAR(10),
    url VARCHAR(1000),
    local_path VARCHAR(1000),
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- Research history
CREATE TABLE research_sessions (
    id VARCHAR(36) PRIMARY KEY,
    track_id VARCHAR(36),
    query VARCHAR(500),
    sources_searched TEXT, -- JSON array
    results_found INTEGER,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);

-- Rekordbox sync tracking
CREATE TABLE rekordbox_sync (
    track_id VARCHAR(36) PRIMARY KEY,
    rekordbox_id VARCHAR(100),
    synced_at TIMESTAMP,
    sync_status VARCHAR(20),
    last_error TEXT,
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);
```

## Implementation Architecture

### Tools Structure (Post-Refactor)
```
tools/
├── operations/
│   ├── search.py           # Generic search templates
│   ├── metadata.py         # Metadata collection templates
│   └── artwork.py          # Artwork collection templates
├── integrations/
│   ├── [platform].py       # Platform-specific implementations
├── core/
│   ├── research.py         # Music research orchestration
│   ├── metadata_merger.py  # Intelligent metadata merging
│   ├── quality_analyzer.py # Audio quality assessment
│   └── artwork_manager.py  # Artwork collection & management
├── database/
│   ├── models.py           # Database models
│   ├── metadata_store.py   # Metadata storage operations
│   └── rekordbox_sync.py   # Rekordbox synchronization
└── specialized/
    ├── mp3tag_integration.py # MP3Tag-like functionality
    ├── auto_tagger.py        # Intelligent auto-tagging
    └── quality_enhancer.py   # Audio quality enhancement
```

### Research Agent Workflow
```python
# Example usage
research_agent = MusicResearchAgent()

# Research a track
metadata = await research_agent.research_track("Deadmau5 - Strobe")

# Results include:
# - All available platforms and their data
# - Best quality download option
# - Purchase alternatives if no downloads
# - Complete metadata from all sources
# - High-quality artwork
# - Confidence scores for data accuracy

if metadata.status == TrackStatus.SOLVED:
    # Track meets quality requirements
    await download_manager.download_track(metadata.best_download_source)
    await rekordbox_sync.sync_track(metadata)
```

## Quality Requirements & "Solved" Criteria

### Track Resolution Criteria
A track is marked as "SOLVED" when:
1. **Metadata Completeness**: Core fields (title, artist, duration, genre) present
2. **Quality Threshold**: Minimum 320kbps MP3 or lossless available
3. **Artwork Available**: At least 500x500px artwork found
4. **Source Reliability**: Data from 2+ reliable sources
5. **Download/Purchase Option**: Clear path to obtain the track

### Quality Scoring System
```python
def calculate_track_quality_score(metadata: UniversalTrackMetadata) -> float:
    """Calculate overall quality score (0.0 - 1.0)."""
    score = 0.0
    
    # Metadata completeness (40%)
    core_fields = ['title', 'artist', 'duration_ms', 'bpm', 'key']
    completeness = sum(1 for field in core_fields if getattr(metadata, field)) / len(core_fields)
    score += completeness * 0.4
    
    # Audio quality (30%)
    quality_scores = {
        TrackQuality.LOSSLESS: 1.0,
        TrackQuality.HIGH: 0.8,
        TrackQuality.MEDIUM: 0.5,
        TrackQuality.LOW: 0.2,
        TrackQuality.UNKNOWN: 0.0
    }
    score += quality_scores[metadata.quality] * 0.3
    
    # Source reliability (20%)
    reliable_sources = ['beatport', 'spotify', 'discogs', 'musicbrainz']
    reliable_count = sum(1 for source in metadata.research_sources if source in reliable_sources)
    score += min(reliable_count / len(reliable_sources), 1.0) * 0.2
    
    # Artwork quality (10%)
    if metadata.artwork_local_path:
        score += 0.1
    
    return score
```

## Integration with Existing Systems

### MP3Tag-like Functionality
```python
class IntelligentTagger:
    """MP3Tag-inspired intelligent tagging system."""
    
    async def auto_tag_file(self, file_path: str) -> Dict[str, Any]:
        """Automatically tag an audio file using research data."""
        
    async def batch_tag_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Tag all files in a directory."""
        
    async def verify_tags(self, file_path: str) -> Dict[str, Any]:
        """Verify existing tags against research database."""
```

### Rekordbox Integration via PyRekordbox
Using the `pyrekordbox` package for comprehensive Rekordbox database access:

```python
import pyrekordbox

class RekordboxIntegration:
    """Full Rekordbox database integration using pyrekordbox."""
    
    def __init__(self, rekordbox_path: Optional[str] = None):
        """Initialize with Rekordbox database path."""
        self.db = pyrekordbox.Rekordbox6Database(rekordbox_path)
        
    async def import_rekordbox_tracks(self) -> List[UniversalTrackMetadata]:
        """Import all tracks from Rekordbox database."""
        tracks = []
        
        # Get all content (tracks)
        for content in self.db.get_content():
            metadata = self._convert_rekordbox_to_universal(content)
            tracks.append(metadata)
            
        return tracks
    
    async def sync_track_to_rekordbox(self, metadata: UniversalTrackMetadata) -> bool:
        """Sync enhanced metadata back to Rekordbox."""
        try:
            # Update existing track or add new one
            content_data = self._convert_universal_to_rekordbox(metadata)
            
            # Use pyrekordbox to update the database
            # Note: This requires write capability which may be limited
            success = self.db.update_content(content_data)
            
            if success:
                metadata.rekordbox_synced = True
                metadata.rekordbox_sync_at = datetime.utcnow()
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to sync track {metadata.title}: {e}")
            return False
    
    def _convert_rekordbox_to_universal(self, rb_content) -> UniversalTrackMetadata:
        """Convert pyrekordbox content to UniversalTrackMetadata."""
        return UniversalTrackMetadata(
            title=rb_content.Title or "",
            artist=rb_content.Artist.Name if rb_content.Artist else "",
            album=rb_content.Album.Name if rb_content.Album else None,
            genre=rb_content.Genre.Name if rb_content.Genre else None,
            label=rb_content.Label.Name if rb_content.Label else None,
            bpm=rb_content.Tempo,
            key=rb_content.Tonality,
            duration_ms=rb_content.Length,
            bitrate=rb_content.BitRate,
            sample_rate=rb_content.SampleRate,
            file_path=rb_content.FolderPath,
            rating=rb_content.Rating,
            play_count=rb_content.PlayCount,
            # Map other Rekordbox fields...
            rekordbox_id=str(rb_content.ID),
            platform_metadata={"rekordbox": rb_content.__dict__}
        )
    
    def get_rekordbox_playlists(self) -> List[Dict[str, Any]]:
        """Get all playlists from Rekordbox."""
        playlists = []
        
        for playlist in self.db.get_playlist():
            playlist_data = {
                "id": playlist.ID,
                "name": playlist.Name,
                "parent_id": playlist.Parent.ID if playlist.Parent else None,
                "tracks": [track.ID for track in playlist.Songs] if playlist.Songs else []
            }
            playlists.append(playlist_data)
            
        return playlists
    
    def get_hot_cues(self, track_id: str) -> List[Dict[str, Any]]:
        """Get hot cues for a specific track."""
        # Access hot cue data through pyrekordbox
        # Implementation depends on pyrekordbox capabilities
        pass
    
    def get_beat_grid(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get beat grid data for a track."""
        # Access beat grid through pyrekordbox
        pass
```

### Enhanced Rekordbox Schema Coverage
With pyrekordbox, we can access much more detailed Rekordbox data:

```python
REKORDBOX_FIELD_MAPPING = {
    # Basic metadata
    "Title": "title",
    "Artist.Name": "artist", 
    "Album.Name": "album",
    "Genre.Name": "genre",
    "Label.Name": "label",
    "Remixer": "remixers",
    
    # Technical data
    "Tempo": "bpm",
    "Tonality": "key", 
    "Length": "duration_ms",
    "BitRate": "bitrate",
    "SampleRate": "sample_rate",
    "ColorID": "color_id",
    
    # DJ data
    "Rating": "rating",
    "PlayCount": "play_count",
    "LastPlayDate": "last_played",
    
    # File info
    "FolderPath": "file_path",
    "FileName": "filename",
    "FileSize": "file_size",
    "DateCreated": "date_created",
    "DateAdded": "date_added",
    
    # Analysis data (if available via pyrekordbox)
    "HotCues": "hot_cues",
    "BeatGrid": "beat_grid",
    "Waveform": "waveform_data"
}
```

## Implementation Timeline

### Phase 1: Foundation (2-3 weeks)
1. Database schema implementation
2. Universal metadata model
3. **PyRekordbox integration setup** - Replace current rekordbox_sync.py
4. Basic research agent framework
5. Core metadata merger

### Phase 2: Integration (3-4 weeks)
1. Platform-specific metadata collectors
2. **Rekordbox data import/export** via pyrekordbox
3. Artwork collection system
4. Quality assessment algorithms
5. Research pipeline implementation

### Phase 3: Intelligence (2-3 weeks)
1. Advanced metadata merging
2. **Rekordbox-aware research** - Use existing library as research baseline
3. Confidence scoring
4. Auto-tagging functionality
5. Quality enhancement

### Phase 4: Sync & Polish (1-2 weeks)
1. **Full Rekordbox bidirectional sync** - Import existing, export enhanced
2. MP3Tag-like features
3. **Playlist and hot cue management**
4. Performance optimization
5. Testing & documentation

### PyRekordbox Migration Plan
**Replace**: `src/music_agent/integrations/rekordbox_sync.py`
**With**: Full pyrekordbox integration including:

```python
# New rekordbox integration structure
src/music_agent/integrations/rekordbox/
├── __init__.py
├── client.py              # PyRekordbox wrapper
├── models.py              # Rekordbox-specific models
├── sync.py                # Bidirectional sync manager
├── playlist_manager.py    # Playlist operations
└── analysis_data.py       # Hot cues, beat grids, waveforms
```

**Key Capabilities Added**:
- **Read Existing Library**: Import all current Rekordbox tracks as research baseline
- **Enhanced Sync**: Write back enriched metadata, artwork, and analysis
- **Playlist Management**: Sync playlists between research DB and Rekordbox
- **Analysis Data**: Access/modify hot cues, beat grids, loops
- **Advanced Queries**: Search Rekordbox library with complex filters

## Success Metrics

### Research Effectiveness
- **Coverage**: Percentage of tracks that can be "solved"
- **Accuracy**: Metadata accuracy compared to ground truth
- **Completeness**: Average metadata completeness score
- **Quality**: Percentage of tracks found in high/lossless quality

### System Performance
- **Speed**: Average time to research a track
- **Efficiency**: Successful downloads vs searches
- **Reliability**: Successful Rekordbox syncs
- **Storage**: Metadata database size vs track count

This comprehensive system will transform music discovery from manual searches into an intelligent, automated research and curation platform that rivals commercial music tagging solutions while maintaining full control over the data and process.