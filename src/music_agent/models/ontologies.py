"""
Music Domain Ontologies for Graphiti
Complete entity and relationship definitions for the music knowledge graph
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============= CORE MUSIC ENTITIES =============

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
    
    # DJ-specific metadata
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


class Artist(BaseModel):
    """Musical artist or band"""
    name: str = Field(description="Artist or band name")
    genres: List[str] = Field(default_factory=list, description="Associated genres")
    founded_year: Optional[int] = Field(None, description="Year founded/born")
    origin_country: Optional[str] = Field(None, description="Country of origin")
    label: Optional[str] = Field(None, description="Record label")
    spotify_id: Optional[str] = Field(None)
    deezer_id: Optional[str] = Field(None)
    discogs_id: Optional[str] = Field(None)
    beatport_id: Optional[str] = Field(None)


class Album(BaseModel):
    """Music album or EP"""
    title: str = Field(description="Album title")
    artist: str = Field(description="Primary artist")
    release_date: Optional[datetime] = Field(None)
    label: Optional[str] = Field(None, description="Record label")
    total_tracks: Optional[int] = Field(None)
    album_type: Optional[str] = Field(None, description="album, single, compilation, ep")
    upc: Optional[str] = Field(None, description="Universal Product Code")


class Genre(BaseModel):
    """Musical genre or style"""
    name: str = Field(description="Genre name")
    parent_genre: Optional[str] = Field(None, description="Parent genre if subgenre")
    era: Optional[str] = Field(None, description="Associated era or time period")
    characteristics: List[str] = Field(default_factory=list)


class Playlist(BaseModel):
    """Music playlist or collection"""
    name: str = Field(description="Playlist name")
    curator: Optional[str] = Field(None, description="Playlist creator")
    description: Optional[str] = Field(None)
    mood: Optional[str] = Field(None, description="Playlist mood or vibe")
    purpose: Optional[str] = Field(None, description="workout, party, study, etc")
    platform: Optional[str] = Field(None, description="Source platform")
    platform_id: Optional[str] = Field(None)


# ============= DJ-SPECIFIC ENTITIES =============

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


# ============= P2P & NETWORK ENTITIES =============

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


# ============= USER PREFERENCE ENTITIES =============

class ListeningSession(BaseModel):
    """User listening session or context"""
    context: str = Field(description="Context of listening: party, workout, relaxing, etc")
    mood: Optional[str] = Field(None)
    energy_level: Optional[str] = Field(None, description="low, medium, high")
    time_of_day: Optional[str] = Field(None, description="morning, afternoon, evening, night")


class MusicPreference(BaseModel):
    """User music preference or taste profile"""
    preference_type: str = Field(description="like, dislike, favorite, banned")
    target: str = Field(description="What the preference applies to")
    reason: Optional[str] = Field(None, description="Why this preference exists")
    strength: Optional[float] = Field(None, description="Strength of preference 0-1")


# ============= RELATIONSHIPS =============

class PerformedBy(BaseModel):
    """Track performed by artist"""
    role: Optional[str] = Field(None, description="vocalist, producer, featured, remix")


class BelongsToAlbum(BaseModel):
    """Track belongs to album"""
    track_number: Optional[int] = Field(None)
    disc_number: Optional[int] = Field(None, default=1)


class RemixOf(BaseModel):
    """Track is remix of another"""
    remixer: str = Field(description="Remixing artist")
    style: Optional[str] = Field(None, description="Remix style")


class SimilarTo(BaseModel):
    """Tracks/artists are similar"""
    similarity_score: Optional[float] = Field(None, description="Similarity 0-1")
    similarity_type: Optional[str] = Field(None, description="style, tempo, mood, etc")


class MixedWith(BaseModel):
    """Tracks that mix well together"""
    compatibility_score: float = Field(description="How well they mix 0-1")
    key_compatible: bool
    bpm_compatible: bool
    energy_compatible: bool
    tested: bool = Field(default=False, description="Actually mixed together")
    notes: Optional[str] = Field(None)


class ContainsTrack(BaseModel):
    """Playlist contains track"""
    position: Optional[int] = Field(None)
    added_date: Optional[datetime] = Field(None)


class PreferredBy(BaseModel):
    """User prefers entity"""
    preference_score: float = Field(description="Preference strength 0-1")
    context: Optional[str] = Field(None, description="When this preference applies")


class DiscoveredThrough(BaseModel):
    """Track/artist discovered through source"""
    source: str = Field(description="Discovery source: recommendation, playlist, radio, etc")
    timestamp: datetime = Field(default_factory=datetime.now)


# ============= ENTITY TYPE REGISTRY =============

MUSIC_ENTITY_TYPES = {
    # Core music entities
    'Track': Track,
    'Artist': Artist,
    'Album': Album,
    'Genre': Genre,
    'Playlist': Playlist,
    
    # DJ-specific entities
    'CuePoint': CuePoint,
    'BeatGrid': BeatGrid,
    'Loop': Loop,
    'DJFolder': DJFolder,
    
    # P2P & Network entities
    'P2PSource': P2PSource,
    'DownloadSource': DownloadSource,
    
    # User preference entities
    'ListeningSession': ListeningSession,
    'MusicPreference': MusicPreference,
}

MUSIC_EDGE_TYPES = {
    # Basic relationships
    'PERFORMED_BY': PerformedBy,
    'BELONGS_TO_ALBUM': BelongsToAlbum,
    'REMIX_OF': RemixOf,
    'SIMILAR_TO': SimilarTo,
    'MIXED_WITH': MixedWith,
    'CONTAINS_TRACK': ContainsTrack,
    'PREFERRED_BY': PreferredBy,
    'DISCOVERED_THROUGH': DiscoveredThrough,
}