"""
Rekordbox Models - Simple data models for Rekordbox entities

Provides cleaner interfaces for working with Rekordbox data.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class RekordboxTrack:
    """Simplified Rekordbox track model."""
    
    # Core fields
    id: int
    title: str
    artist: str
    album: Optional[str] = None
    
    # Technical
    bpm: Optional[float] = None
    key: Optional[str] = None
    duration_ms: Optional[int] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    
    # File info
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    
    # Metadata
    genre: Optional[str] = None
    label: Optional[str] = None
    remixer: Optional[str] = None
    composer: Optional[str] = None
    comments: Optional[str] = None
    grouping: Optional[str] = None
    
    # Track info
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    release_date: Optional[datetime] = None
    
    # User data
    rating: Optional[int] = None
    color: Optional[int] = None
    play_count: Optional[int] = None
    last_played: Optional[datetime] = None
    
    # Timestamps
    date_added: Optional[datetime] = None
    date_created: Optional[datetime] = None
    
    # Analysis
    analyzed: bool = False
    analyze_path: Optional[str] = None
    beat_grid_locked: bool = False
    
    # DJ data
    hot_cues: List[Dict[str, Any]] = field(default_factory=list)
    memory_cues: List[Dict[str, Any]] = field(default_factory=list)
    loops: List[Dict[str, Any]] = field(default_factory=list)
    
    # Raw pyrekordbox object
    _raw: Optional[Any] = None
    
    @classmethod
    def from_pyrekordbox(cls, rb_content: Any) -> 'RekordboxTrack':
        """Create from pyrekordbox content object."""
        track = cls(
            id=rb_content.ID,
            title=rb_content.Title or "",
            artist=rb_content.Artist.Name if rb_content.Artist else ""
        )
        
        # Populate other fields
        track.album = rb_content.Album.Name if rb_content.Album else None
        track.bpm = rb_content.Tempo
        track.key = rb_content.Tonality
        track.duration_ms = rb_content.Length
        track.bitrate = rb_content.BitRate
        track.sample_rate = rb_content.SampleRate
        
        track.file_path = rb_content.FolderPath
        track.file_size = rb_content.FileSize
        
        track.genre = rb_content.Genre.Name if rb_content.Genre else None
        track.label = rb_content.Label.Name if rb_content.Label else None
        track.remixer = rb_content.Remixer
        track.comments = rb_content.Comments
        track.grouping = rb_content.Grouping
        
        track.track_number = rb_content.TrackNumber
        track.disc_number = rb_content.DiscNumber
        
        track.rating = rb_content.Rating
        track.color = rb_content.ColorID
        track.play_count = rb_content.PlayCount
        
        track.analyzed = bool(rb_content.AnalyzePath)
        track.analyze_path = rb_content.AnalyzePath
        
        # Store raw object for advanced operations
        track._raw = rb_content
        
        return track
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'artist': self.artist
        }
        
        # Add non-None optional fields
        for field_name in [
            'album', 'bpm', 'key', 'duration_ms', 'bitrate',
            'sample_rate', 'file_path', 'genre', 'label',
            'remixer', 'composer', 'comments', 'rating'
        ]:
            value = getattr(self, field_name)
            if value is not None:
                data[field_name] = value
        
        return data


@dataclass
class RekordboxPlaylist:
    """Simplified Rekordbox playlist model."""
    
    id: int
    name: str
    parent_id: Optional[int] = None
    is_folder: bool = False
    track_ids: List[int] = field(default_factory=list)
    track_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Raw pyrekordbox object
    _raw: Optional[Any] = None
    
    @classmethod
    def from_pyrekordbox(cls, rb_playlist: Any) -> 'RekordboxPlaylist':
        """Create from pyrekordbox playlist object."""
        playlist = cls(
            id=rb_playlist.ID,
            name=rb_playlist.Name
        )
        
        # Check if it's a folder
        playlist.is_folder = not hasattr(rb_playlist, 'Songs') or rb_playlist.Songs is None
        
        # Get parent
        if rb_playlist.Parent:
            playlist.parent_id = rb_playlist.Parent.ID
        
        # Get tracks
        if not playlist.is_folder and rb_playlist.Songs:
            playlist.track_ids = [song.Content.ID for song in rb_playlist.Songs]
            playlist.track_count = len(playlist.track_ids)
        
        # Store raw object
        playlist._raw = rb_playlist
        
        return playlist
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'is_folder': self.is_folder,
            'track_count': self.track_count,
            'track_ids': self.track_ids
        }


@dataclass
class RekordboxHotCue:
    """Hot cue point model."""
    
    number: int                # Cue number (1-8)
    position: float            # Position in milliseconds
    color: Optional[str] = None
    name: Optional[str] = None
    
    @classmethod
    def from_pyrekordbox(cls, rb_cue: Any) -> 'RekordboxHotCue':
        """Create from pyrekordbox hot cue object."""
        return cls(
            number=rb_cue.Number,
            position=rb_cue.Position,
            color=rb_cue.Color if hasattr(rb_cue, 'Color') else None,
            name=rb_cue.Name if hasattr(rb_cue, 'Name') else None
        )


@dataclass
class RekordboxMemoryCue:
    """Memory cue point model."""
    
    position: float            # Position in milliseconds
    name: Optional[str] = None
    
    @classmethod
    def from_pyrekordbox(cls, rb_cue: Any) -> 'RekordboxMemoryCue':
        """Create from pyrekordbox memory cue object."""
        return cls(
            position=rb_cue.Position,
            name=rb_cue.Name if hasattr(rb_cue, 'Name') else None
        )


@dataclass
class RekordboxLoop:
    """Loop point model."""
    
    start: float              # Start position in milliseconds
    end: float                # End position in milliseconds
    name: Optional[str] = None
    active: bool = False
    
    @classmethod
    def from_pyrekordbox(cls, rb_loop: Any) -> 'RekordboxLoop':
        """Create from pyrekordbox loop object."""
        return cls(
            start=rb_loop.Start,
            end=rb_loop.End,
            name=rb_loop.Name if hasattr(rb_loop, 'Name') else None,
            active=rb_loop.Active if hasattr(rb_loop, 'Active') else False
        )


@dataclass
class RekordboxBeatGrid:
    """Beat grid information."""
    
    bpm: float
    first_beat: float         # Position of first beat
    locked: bool = False
    beats: List[float] = field(default_factory=list)
    
    @classmethod
    def from_pyrekordbox(cls, rb_grid: Any) -> 'RekordboxBeatGrid':
        """Create from pyrekordbox beat grid object."""
        return cls(
            bpm=rb_grid.BPM,
            first_beat=rb_grid.FirstBeat,
            locked=rb_grid.Locked if hasattr(rb_grid, 'Locked') else False,
            beats=list(rb_grid.Beats) if hasattr(rb_grid, 'Beats') else []
        )