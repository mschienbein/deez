# Unified Music Ontology - Comparison and Complete Model

## Executive Summary

This document compares the ontologies across all integration plans and identifies gaps, particularly for Rekordbox-specific data. The Rekordbox integration plan focuses on the hybrid database architecture but lacks comprehensive Graphiti ontologies for DJ-specific concepts like cue points, beat grids, and waveform analysis.

## Ontology Comparison Matrix

| Entity Type | Base Architecture | Extended Models | Rekordbox Plan | Soulseek Plan | Gap Analysis |
|------------|------------------|-----------------|----------------|---------------|--------------|
| **Track** | ✅ Complete | ✅ Enhanced | ⚠️ SQL only | ✅ P2P specific | Missing DJ metadata in Graphiti |
| **Artist** | ✅ Complete | ✅ Enhanced | ⚠️ SQL only | ❌ Not defined | Consistent across plans |
| **Album** | ✅ Complete | ✅ Enhanced | ⚠️ SQL only | ❌ Not defined | Consistent across plans |
| **Genre** | ✅ Complete | ✅ Enhanced | ⚠️ SQL only | ❌ Not defined | Need subgenre hierarchy |
| **Playlist** | ✅ Basic | ✅ Enhanced | ⚠️ SQL only | ❌ Not defined | Missing smart playlist logic |
| **CuePoint** | ❌ Missing | ❌ Missing | ✅ SQL only | ❌ Not needed | **Critical gap for DJs** |
| **BeatGrid** | ❌ Missing | ❌ Missing | ✅ SQL only | ❌ Not needed | **Critical gap for DJs** |
| **Loop** | ❌ Missing | ❌ Missing | ⚠️ Partial | ❌ Not needed | **Critical gap for DJs** |
| **Waveform** | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Not needed | **Critical gap for DJs** |
| **DJSet** | ❌ Missing | ✅ Complete | ❌ Missing | ❌ Not needed | Good in extended |
| **P2PSource** | ❌ Missing | ❌ Missing | ❌ Missing | ⚠️ Referenced | **Needed for Soulseek** |
| **BeatportTrack** | ❌ Missing | ✅ Complete | ❌ Missing | ❌ Not needed | Good in extended |
| **VinylRecord** | ❌ Missing | ✅ Complete | ❌ Missing | ❌ Not needed | Good in extended |

## Complete Unified Ontology for Graphiti

### 1. Core Music Entities (Enhanced)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ============= CORE ENTITIES =============

class Track(BaseModel):
    """Universal track entity with DJ-specific metadata"""
    # Basic metadata
    title: str = Field(description="Track title")
    artist: str = Field(description="Primary artist")
    album: Optional[str] = Field(None, description="Album name")
    
    # Technical metadata
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="mp3, flac, wav, etc")
    bitrate: Optional[int] = Field(None, description="Bitrate in kbps")
    sample_rate: Optional[int] = Field(None, description="Sample rate in Hz")
    
    # Musical metadata
    bpm: Optional[float] = Field(None, description="Beats per minute")
    key: Optional[str] = Field(None, description="Musical key (Camelot or standard)")
    energy: Optional[float] = Field(None, description="Energy level 0-1")
    danceability: Optional[float] = Field(None, description="Danceability 0-1")
    
    # DJ-specific metadata (NEW - was missing!)
    analyzed: bool = Field(default=False, description="Has been analyzed by Rekordbox")
    rating: Optional[int] = Field(None, description="1-5 star rating")
    color: Optional[str] = Field(None, description="Track color coding")
    comment: Optional[str] = Field(None, description="DJ notes")
    
    # Platform identifiers
    rekordbox_id: Optional[str] = Field(None)
    spotify_id: Optional[str] = Field(None)
    deezer_id: Optional[str] = Field(None)
    beatport_id: Optional[str] = Field(None)
    discogs_id: Optional[str] = Field(None)
    youtube_id: Optional[str] = Field(None)
    track_1001_id: Optional[str] = Field(None)
    
    # Universal identifiers
    isrc: Optional[str] = Field(None, description="International Standard Recording Code")
    audio_fingerprint: Optional[str] = Field(None, description="AcoustID or similar")
    
    # File location
    file_path: Optional[str] = Field(None, description="Local file path if owned")
    
    # Dates
    release_date: Optional[datetime] = Field(None)
    added_date: Optional[datetime] = Field(None)
    last_played: Optional[datetime] = Field(None)
    play_count: int = Field(default=0)

# ============= DJ-SPECIFIC ENTITIES (NEW) =============

class CuePoint(BaseModel):
    """DJ cue point for track navigation"""
    track_id: str = Field(description="Associated track ID")
    position_ms: int = Field(description="Position in milliseconds")
    type: str = Field(description="hot_cue, memory, loop_in, loop_out")
    index: Optional[int] = Field(None, description="Hot cue number (1-8)")
    name: Optional[str] = Field(None, description="Cue point name")
    color: Optional[str] = Field(None, description="Visual color")
    comment: Optional[str] = Field(None, description="Notes about this point")

class BeatGrid(BaseModel):
    """Beat grid for precise mixing"""
    track_id: str = Field(description="Associated track ID")
    first_beat_ms: int = Field(description="First downbeat position")
    bpm: float = Field(description="Precise BPM")
    beat_positions: Optional[List[int]] = Field(None, description="Beat positions in ms")
    confidence: Optional[float] = Field(None, description="Grid accuracy 0-1")
    manually_adjusted: bool = Field(default=False)

class Loop(BaseModel):
    """Saved loop region"""
    track_id: str = Field(description="Associated track ID")
    start_ms: int = Field(description="Loop start in milliseconds")
    end_ms: int = Field(description="Loop end in milliseconds")
    length_beats: int = Field(description="Loop length in beats")
    name: Optional[str] = Field(None, description="Loop name")
    active: bool = Field(default=False, description="Currently active loop")

class WaveformData(BaseModel):
    """Waveform visualization data"""
    track_id: str = Field(description="Associated track ID")
    overview_data: Optional[str] = Field(None, description="Base64 encoded overview")
    detail_data: Optional[str] = Field(None, description="Base64 encoded detail")
    color_data: Optional[str] = Field(None, description="Frequency color information")
    peak_data: Optional[List[float]] = Field(None, description="Peak levels")

class HarmonicKey(BaseModel):
    """Advanced key detection for harmonic mixing"""
    track_id: str = Field(description="Associated track ID")
    camelot_key: str = Field(description="Camelot wheel notation (1A-12B)")
    standard_key: str = Field(description="Standard notation (C, Dm, etc)")
    energy_level: int = Field(description="Energy level 1-10")
    compatible_keys: List[str] = Field(default_factory=list, description="Harmonically compatible keys")

# ============= P2P & NETWORK ENTITIES (NEW) =============

class P2PSource(BaseModel):
    """Peer-to-peer source information"""
    username: str = Field(description="P2P username")
    network: str = Field(description="soulseek, napster, etc")
    reputation: Optional[float] = Field(None, description="User reputation 0-1")
    shared_files: Optional[int] = Field(None, description="Number of shared files")
    connection_quality: Optional[str] = Field(None, description="Connection speed/quality")
    last_seen: Optional[datetime] = Field(None)

class DownloadSource(BaseModel):
    """Track download source information"""
    track_id: str = Field(description="Downloaded track ID")
    source_type: str = Field(description="deezer, spotify, soulseek, youtube, etc")
    source_user: Optional[str] = Field(None, description="P2P username if applicable")
    quality: str = Field(description="FLAC, MP3_320, etc")
    download_date: datetime
    file_size: int
    success: bool = Field(default=True)

# ============= COLLECTION ENTITIES =============

class DJFolder(BaseModel):
    """Rekordbox folder/crate organization"""
    name: str = Field(description="Folder/crate name")
    parent_folder: Optional[str] = Field(None, description="Parent folder if nested")
    color: Optional[str] = Field(None, description="Visual color")
    smart_folder: bool = Field(default=False, description="Dynamic smart folder")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Smart folder criteria")
    track_count: int = Field(default=0)
    created_date: datetime
    modified_date: datetime

class PreparedSet(BaseModel):
    """Pre-planned DJ set"""
    name: str = Field(description="Set name")
    event: Optional[str] = Field(None, description="Event/venue")
    date: Optional[datetime] = Field(None, description="Performance date")
    duration_minutes: int = Field(description="Planned duration")
    tracks: List[str] = Field(default_factory=list, description="Ordered track IDs")
    transitions: Optional[List[Dict]] = Field(None, description="Planned transitions")
    notes: Optional[str] = Field(None, description="Performance notes")

# ============= ANALYSIS ENTITIES =============

class TrackAnalysis(BaseModel):
    """Comprehensive track analysis results"""
    track_id: str = Field(description="Analyzed track ID")
    analyzer: str = Field(description="rekordbox, mixed_in_key, traktor, etc")
    analysis_date: datetime
    
    # Rhythm analysis
    bpm: float
    bpm_confidence: float
    time_signature: str = Field(description="4/4, 3/4, etc")
    
    # Harmonic analysis
    key: str
    key_confidence: float
    scale: str = Field(description="major, minor, etc")
    
    # Structure analysis
    intro_ms: Optional[int] = Field(None)
    outro_ms: Optional[int] = Field(None)
    breakdown_positions: Optional[List[int]] = Field(None)
    drop_positions: Optional[List[int]] = Field(None)
    phrase_length: Optional[int] = Field(None, description="Bars per phrase")
    
    # Energy analysis
    energy_profile: Optional[List[float]] = Field(None, description="Energy over time")
    peak_energy: Optional[float] = Field(None)
    average_energy: Optional[float] = Field(None)

class MixTransition(BaseModel):
    """Transition between two tracks in a mix"""
    from_track_id: str
    to_track_id: str
    transition_type: str = Field(description="blend, cut, fade, scratch, etc")
    start_position_ms: int = Field(description="Start position in from_track")
    end_position_ms: int = Field(description="End position in from_track")
    cue_position_ms: int = Field(description="Cue position in to_track")
    key_change: Optional[str] = Field(None, description="Key transition description")
    bpm_change: Optional[float] = Field(None, description="BPM difference")
    quality_score: Optional[float] = Field(None, description="Transition quality 0-1")
    notes: Optional[str] = Field(None)

# ============= RELATIONSHIPS (ENHANCED) =============

class AnalyzedBy(BaseModel):
    """Track analyzed by software"""
    software: str = Field(description="Analysis software")
    version: str = Field(description="Software version")
    date: datetime
    settings: Optional[Dict[str, Any]] = Field(None)

class MixedWith(BaseModel):
    """Tracks that mix well together"""
    compatibility_score: float = Field(description="How well they mix 0-1")
    key_compatible: bool
    bpm_compatible: bool
    energy_compatible: bool
    tested: bool = Field(default=False, description="Actually mixed together")
    notes: Optional[str] = Field(None)

class InFolder(BaseModel):
    """Track in DJ folder/crate"""
    folder_name: str
    position: Optional[int] = Field(None)
    added_date: datetime
    tags: Optional[List[str]] = Field(None)

class PlayedInSet(BaseModel):
    """Track played in DJ set"""
    set_id: str
    position: int
    actual_bpm: Optional[float] = Field(None, description="BPM as played (pitched)")
    actual_key: Optional[str] = Field(None, description="Key as played (pitched)")
    crowd_response: Optional[str] = Field(None, description="Crowd reaction")

class DownloadedFrom(BaseModel):
    """Track downloaded from source"""
    source: str
    quality: str
    date: datetime
    successful: bool
    retry_count: int = Field(default=0)

# ============= ENTITY TYPE REGISTRY =============

COMPLETE_MUSIC_ENTITY_TYPES = {
    # Core music entities
    'Track': Track,
    'Artist': Artist,  # From base architecture
    'Album': Album,  # From base architecture
    'Genre': Genre,  # From base architecture
    'Playlist': Playlist,  # From base architecture
    'MusicLabel': MusicLabel,  # From base architecture
    'MusicVenue': MusicVenue,  # From base architecture
    
    # DJ-specific entities
    'CuePoint': CuePoint,
    'BeatGrid': BeatGrid,
    'Loop': Loop,
    'WaveformData': WaveformData,
    'HarmonicKey': HarmonicKey,
    'DJFolder': DJFolder,
    'PreparedSet': PreparedSet,
    'TrackAnalysis': TrackAnalysis,
    'MixTransition': MixTransition,
    
    # DJ performance entities (from extended)
    'DJSet': DJSet,  # From extended models
    'TracklistEntry': TracklistEntry,  # From extended models
    'RadioShow': RadioShow,  # From extended models
    'Festival': Festival,  # From extended models
    
    # P2P & Network entities
    'P2PSource': P2PSource,
    'DownloadSource': DownloadSource,
    
    # Platform-specific (from extended)
    'BeatportTrack': BeatportTrack,  # From extended models
    'DiscogsRelease': DiscogsRelease,  # From extended models
    'VinylRecord': VinylRecord,  # From extended models
    
    # User preference entities
    'ListeningSession': ListeningSession,  # From base architecture
    'MusicPreference': MusicPreference,  # From base architecture
}

COMPLETE_EDGE_TYPES = {
    # Basic relationships (from base)
    'PERFORMED_BY': PerformedBy,
    'BELONGS_TO_ALBUM': BelongsToAlbum,
    'SIGNED_TO': SignedTo,
    'COLLABORATED': Collaborated,
    'INFLUENCED_BY': InfluencedBy,
    'REMIX_OF': RemixOf,
    'SIMILAR_TO': SimilarTo,
    'CONTAINS_TRACK': ContainsTrack,
    'PREFERRED_BY': PreferredBy,
    'DISCOVERED_THROUGH': DiscoveredThrough,
    
    # DJ-specific relationships
    'ANALYZED_BY': AnalyzedBy,
    'MIXED_WITH': MixedWith,
    'IN_FOLDER': InFolder,
    'PLAYED_IN_SET': PlayedInSet,
    'DOWNLOADED_FROM': DownloadedFrom,
    
    # Performance relationships (from extended)
    'PLAYED_IN': PlayedIn,
    'PERFORMED_AT': PerformedAt,
    'SUPPORTED_BY': SupportedBy,
}
```

## 2. Integration with Rekordbox Sync

### Enhanced Rekordbox Sync with Full Ontology

```python
class EnhancedRekordboxSync:
    """Rekordbox sync with complete Graphiti ontology support"""
    
    async def sync_with_full_ontology(self, rekordbox_data: dict):
        """Sync Rekordbox data using complete ontology"""
        
        # 1. Sync tracks with DJ metadata
        for track in rekordbox_data['tracks']:
            episode_body = f"""
            Synced DJ track from Rekordbox:
            Title: {track['Title']} by {track['Artist']}
            
            DJ Metadata:
            - BPM: {track['BPM']} (Analyzed: {track['AnalyzedDate']})
            - Key: {track['TrackKey']}
            - Rating: {track['Rating']}/5
            - Energy: {track['Energy']}/10
            - Color: {track['ColorID']}
            - Comments: {track['Comment']}
            
            Technical:
            - File: {track['FilePath']}
            - Bitrate: {track['BitRate']}kbps
            - Added: {track['AddedDate']}
            - Last Played: {track['LastPlayed']}
            - Play Count: {track['PlayCount']}
            """
            
            await self.graphiti.add_episode(
                name=f"rekordbox_track_{track['ID']}",
                episode_body=episode_body,
                entity_types={
                    'Track': Track,
                    'TrackAnalysis': TrackAnalysis
                },
                source="rekordbox_sync"
            )
        
        # 2. Sync cue points (NEW)
        for cue in rekordbox_data['cues']:
            episode_body = f"""
            Cue point for track {cue['ContentID']}:
            - Position: {cue['InMsec']}ms
            - Type: {cue['Kind']}
            - Color: {cue['Color']}
            - Comment: {cue['Comment']}
            """
            
            await self.graphiti.add_episode(
                name=f"cue_point_{cue['ID']}",
                episode_body=episode_body,
                entity_types={'CuePoint': CuePoint},
                source="rekordbox_cue_sync"
            )
        
        # 3. Sync beat grids (NEW)
        for grid in rekordbox_data['beatgrids']:
            episode_body = f"""
            Beat grid for track {grid['ContentID']}:
            - BPM: {grid['BPM']}
            - First beat: {grid['BeatPosition']}ms
            - Meter: {grid['MeterKind']}
            """
            
            await self.graphiti.add_episode(
                name=f"beatgrid_{grid['ID']}",
                episode_body=episode_body,
                entity_types={'BeatGrid': BeatGrid},
                source="rekordbox_grid_sync"
            )
        
        # 4. Sync playlists/folders (NEW)
        for playlist in rekordbox_data['playlists']:
            episode_body = f"""
            DJ Folder/Playlist: {playlist['Name']}
            - Type: {'Smart' if playlist['SmartList'] else 'Manual'}
            - Track Count: {playlist['TrackCount']}
            - Parent: {playlist['ParentID']}
            """
            
            await self.graphiti.add_episode(
                name=f"dj_folder_{playlist['ID']}",
                episode_body=episode_body,
                entity_types={'DJFolder': DJFolder},
                source="rekordbox_folder_sync"
            )
        
        # 5. Create relationships for mixing compatibility (NEW)
        await self.analyze_mix_compatibility(rekordbox_data['tracks'])
```

## 3. Gap Analysis Summary

### Critical Gaps Identified:

1. **DJ-Specific Metadata in Graphiti**
   - ✅ NOW FIXED: Added CuePoint, BeatGrid, Loop, WaveformData entities
   - ✅ NOW FIXED: Added HarmonicKey for advanced key detection
   - ✅ NOW FIXED: Added TrackAnalysis for comprehensive analysis data

2. **P2P Source Tracking**
   - ✅ NOW FIXED: Added P2PSource entity for Soulseek users
   - ✅ NOW FIXED: Added DownloadSource for tracking origins

3. **Mix Relationships**
   - ✅ NOW FIXED: Added MixedWith relationship
   - ✅ NOW FIXED: Added MixTransition for detailed transition data
   - ✅ NOW FIXED: Added PlayedInSet for performance tracking

4. **Folder/Crate Organization**
   - ✅ NOW FIXED: Added DJFolder entity
   - ✅ NOW FIXED: Added PreparedSet for pre-planned sets
   - ✅ NOW FIXED: Added InFolder relationship

## 4. Implementation Priority

### Phase 1: Core DJ Entities (Critical)
```python
PHASE_1_ENTITIES = {
    'Track': Track,  # Enhanced with DJ metadata
    'CuePoint': CuePoint,
    'BeatGrid': BeatGrid,
    'Loop': Loop,
    'TrackAnalysis': TrackAnalysis,
}
```

### Phase 2: Organization & Performance
```python
PHASE_2_ENTITIES = {
    'DJFolder': DJFolder,
    'PreparedSet': PreparedSet,
    'DJSet': DJSet,
    'MixTransition': MixTransition,
}
```

### Phase 3: Network & Sources
```python
PHASE_3_ENTITIES = {
    'P2PSource': P2PSource,
    'DownloadSource': DownloadSource,
    'WaveformData': WaveformData,
    'HarmonicKey': HarmonicKey,
}
```

## 5. Database Strategy Validation

The hybrid approach (PostgreSQL + Neo4j/Graphiti) remains valid:

### PostgreSQL (Factual/Transactional)
- File paths and technical metadata
- Download queue and status
- Cue points and beat grids (fast lookup)
- Sync state and checksums

### Neo4j/Graphiti (Relationships/Intelligence)
- Track mixing compatibility
- DJ performance history
- Discovery patterns
- Musical relationships
- Temporal evolution of preferences

## 6. Example Usage with Complete Ontology

```python
# Complete track ingestion with all metadata
async def ingest_complete_track(track_data: dict, analysis_data: dict):
    """Ingest track with full DJ and analysis metadata"""
    
    episode_body = f"""
    Complete track ingestion:
    
    Track: {track_data['title']} by {track_data['artist']}
    
    Musical Analysis:
    - Key: {analysis_data['key']} (Confidence: {analysis_data['key_confidence']})
    - BPM: {analysis_data['bpm']} (Confidence: {analysis_data['bpm_confidence']})
    - Energy Profile: {analysis_data['energy_profile']}
    - Structure: Intro at {analysis_data['intro_ms']}ms, Outro at {analysis_data['outro_ms']}ms
    
    DJ Metadata:
    - Rating: {track_data['rating']}/5
    - Color: {track_data['color']}
    - Cue Points: {len(track_data['cue_points'])}
    - Analyzed: {track_data['analyzed']}
    
    Mix Compatibility:
    - Compatible Keys: {analysis_data['compatible_keys']}
    - Energy Level: {analysis_data['energy_level']}
    
    Source:
    - Platform: {track_data['source_platform']}
    - Quality: {track_data['quality']}
    - File Path: {track_data['file_path']}
    """
    
    await graphiti.add_episode(
        name=f"complete_track_{track_data['id']}",
        episode_body=episode_body,
        entity_types=COMPLETE_MUSIC_ENTITY_TYPES,
        edge_types=COMPLETE_EDGE_TYPES,
        source="complete_ingestion"
    )
```

## Conclusion

The Rekordbox integration plan had a solid hybrid database architecture but was missing critical DJ-specific ontologies for Graphiti. This unified ontology document provides:

1. **Complete DJ-specific entities** for cue points, beat grids, loops, and waveforms
2. **P2P source tracking** for Soulseek integration
3. **Enhanced relationships** for mixing compatibility and performance tracking
4. **Proper separation of concerns** between PostgreSQL (facts) and Neo4j/Graphiti (intelligence)

The complete ontology now properly supports all aspects of a professional DJ workflow while maintaining the temporal awareness and relationship tracking that Graphiti excels at.