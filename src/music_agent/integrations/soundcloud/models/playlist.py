"""
Playlist model for SoundCloud.

Represents a SoundCloud playlist or album with tracks.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseModel
from .track import Track
from ..types import PlaylistResponse


class Playlist(BaseModel):
    """Represents a SoundCloud playlist or album."""
    
    def __init__(self, data: Dict[str, Any], client=None):
        """
        Initialize playlist from API data.
        
        Args:
            data: Playlist data from API
            client: Optional SoundCloud client
        """
        # Core attributes
        self.id: int = 0
        self.title: str = ""
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        
        # URLs
        self.permalink_url: str = ""
        self.artwork_url: Optional[str] = None
        
        # Metadata
        self.description: Optional[str] = None
        self.genre: Optional[str] = None
        self.tags: List[str] = []
        self.duration: int = 0  # Total duration in milliseconds
        self.release_date: Optional[datetime] = None
        self.label_name: Optional[str] = None
        
        # Type info
        self.playlist_type: str = ""  # playlist, album, compilation, ep
        self.is_album: bool = False
        
        # Tracks
        self.tracks: List[Track] = []
        self.track_count: int = 0
        self._track_ids: List[int] = []  # For lazy loading
        
        # Statistics
        self.likes_count: int = 0
        self.reposts_count: int = 0
        
        # Flags
        self.public: bool = True
        self.streamable: bool = True
        
        # User info
        self.user_id: int = 0
        self.user: Optional[Dict[str, Any]] = None
        self.username: Optional[str] = None
        
        # Additional info
        self.license: Optional[str] = None
        self.purchase_url: Optional[str] = None
        self.ean: Optional[str] = None  # Album barcode
        
        super().__init__(data, client)
    
    def _parse_data(self, data: Dict[str, Any]):
        """Parse raw API data into playlist attributes."""
        # Core attributes
        self.id = data.get("id", 0)
        self.title = data.get("title", "")
        
        # Parse dates
        self.created_at = self._parse_datetime(data.get("created_at"))
        self.updated_at = self._parse_datetime(data.get("last_modified"))
        self.release_date = self._parse_release_date(data)
        
        # URLs
        self.permalink_url = data.get("permalink_url", "")
        self.artwork_url = data.get("artwork_url")
        
        # Metadata
        self.description = data.get("description")
        self.genre = data.get("genre")
        self.tags = self._parse_tags(data.get("tag_list", ""))
        self.duration = data.get("duration", 0)
        self.label_name = data.get("label_name")
        
        # Type info
        self.playlist_type = data.get("playlist_type", data.get("type", "playlist"))
        self.is_album = data.get("is_album", False)
        
        # Parse tracks
        self._parse_tracks(data.get("tracks", []))
        self.track_count = data.get("track_count", len(self.tracks))
        
        # Statistics
        self.likes_count = data.get("likes_count", 0)
        self.reposts_count = data.get("reposts_count", 0)
        
        # Flags
        self.public = data.get("public", True)
        self.streamable = data.get("streamable", True)
        
        # User info
        self.user_id = data.get("user_id", 0)
        self.user = data.get("user")
        if self.user:
            self.username = self.user.get("username")
        
        # Additional info
        self.license = data.get("license")
        self.purchase_url = data.get("purchase_url")
        self.ean = data.get("ean")
    
    def _parse_tracks(self, tracks_data: List[Any]):
        """Parse tracks from API data."""
        self.tracks = []
        self._track_ids = []
        
        for track_data in tracks_data:
            if isinstance(track_data, dict):
                # Full track object
                if "title" in track_data:
                    track = Track(track_data, self._client)
                    # Set album info on track
                    track.album = self.title
                    track.track_number = len(self.tracks) + 1
                    self.tracks.append(track)
                # Just track ID (for lazy loading)
                elif "id" in track_data:
                    self._track_ids.append(track_data["id"])
            elif isinstance(track_data, int):
                # Direct track ID
                self._track_ids.append(track_data)
    
    def _parse_tags(self, tag_string: str) -> List[str]:
        """Parse space-separated tags."""
        if not tag_string:
            return []
        
        # Tags can be space-separated or quoted
        tags = []
        
        # Handle quoted tags
        import re
        quoted = re.findall(r'"([^"]+)"', tag_string)
        tags.extend(quoted)
        
        # Remove quoted parts and split remainder
        for quote in quoted:
            tag_string = tag_string.replace(f'"{quote}"', "")
        
        # Add remaining tags
        remaining = tag_string.split()
        tags.extend(remaining)
        
        return [tag.strip() for tag in tags if tag.strip()]
    
    def _parse_release_date(self, data: Dict[str, Any]) -> Optional[datetime]:
        """Parse release date from year/month/day fields."""
        # Try published_at first
        published = data.get("published_at")
        if published:
            return self._parse_datetime(published)
        
        # Try year/month/day fields
        year = data.get("release_year")
        month = data.get("release_month")
        day = data.get("release_day")
        
        if year:
            try:
                month = month or 1
                day = day or 1
                return datetime(year, month, day)
            except (ValueError, TypeError):
                pass
        
        return None
    
    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds."""
        return self.duration / 1000.0
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string (HH:MM:SS or MM:SS)."""
        total_seconds = int(self.duration_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    @property
    def artwork_url_high(self) -> Optional[str]:
        """Get high-quality artwork URL."""
        if not self.artwork_url:
            return None
        
        # Replace size in URL for higher quality
        return self.artwork_url.replace("-large", "-t500x500")
    
    async def load_tracks(self):
        """
        Load full track information if only IDs are stored.
        
        Requires client to be set.
        """
        if not self._client:
            raise RuntimeError("Client required to load tracks")
        
        if not self._track_ids:
            return
        
        # Load tracks from API
        from ..api import tracks as tracks_api
        
        loaded_tracks = await tracks_api.get_tracks(self._client, self._track_ids)
        
        for idx, track in enumerate(loaded_tracks):
            # Set album info
            track.album = self.title
            track.track_number = len(self.tracks) + idx + 1
            self.tracks.append(track)
        
        # Clear IDs after loading
        self._track_ids.clear()
    
    async def add_track(self, track: Track, position: Optional[int] = None) -> bool:
        """
        Add a track to the playlist.
        
        Args:
            track: Track to add
            position: Optional position (None = end)
            
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required to modify playlist")
        
        from ..api import playlists
        
        success = await playlists.add_track(
            self._client,
            self.id,
            track.id,
            position
        )
        
        if success:
            if position is not None and 0 <= position < len(self.tracks):
                self.tracks.insert(position, track)
            else:
                self.tracks.append(track)
            
            self.track_count = len(self.tracks)
            
            # Update track album info
            track.album = self.title
            track.track_number = self.tracks.index(track) + 1
        
        return success
    
    async def remove_track(self, track: Track) -> bool:
        """
        Remove a track from the playlist.
        
        Args:
            track: Track to remove
            
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required to modify playlist")
        
        from ..api import playlists
        
        success = await playlists.remove_track(self._client, self.id, track.id)
        
        if success and track in self.tracks:
            self.tracks.remove(track)
            self.track_count = len(self.tracks)
            
            # Update track numbers
            for idx, t in enumerate(self.tracks):
                t.track_number = idx + 1
        
        return success
    
    async def reorder_tracks(self, new_order: List[int]) -> bool:
        """
        Reorder tracks in the playlist.
        
        Args:
            new_order: List of track indices in new order
            
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required to modify playlist")
        
        if len(new_order) != len(self.tracks):
            raise ValueError("New order must contain all track indices")
        
        from ..api import playlists
        
        # Get track IDs in new order
        track_ids = [self.tracks[i].id for i in new_order]
        
        success = await playlists.reorder_tracks(self._client, self.id, track_ids)
        
        if success:
            # Reorder local tracks
            self.tracks = [self.tracks[i] for i in new_order]
            
            # Update track numbers
            for idx, track in enumerate(self.tracks):
                track.track_number = idx + 1
        
        return success
    
    async def download_all(self, output_dir: str, **options) -> List[str]:
        """
        Download all tracks in the playlist.
        
        Args:
            output_dir: Directory to save tracks
            **options: Download options
            
        Returns:
            List of downloaded file paths
        """
        if not self._client:
            raise RuntimeError("Client required for download")
        
        # Ensure tracks are loaded
        if self._track_ids:
            await self.load_tracks()
        
        from ..download import DownloadManager
        
        manager = DownloadManager(self._client)
        return await manager.download_playlist(self, output_dir, **options)
    
    def to_m3u(self) -> str:
        """
        Generate M3U playlist content.
        
        Returns:
            M3U formatted playlist
        """
        lines = ["#EXTM3U"]
        
        # Playlist info
        lines.append(f"#PLAYLIST:{self.title}")
        
        if self.description:
            lines.append(f"#EXTART:{self.username or 'Various Artists'}")
        
        # Add tracks
        for track in self.tracks:
            # Extended info
            duration = int(track.duration_seconds)
            artist_title = f"{track.artist} - {track.title}"
            lines.append(f"#EXTINF:{duration},{artist_title}")
            
            # URL or filename
            lines.append(track.permalink_url)
        
        return "\n".join(lines)
    
    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to format suitable for music agent.
        
        Returns:
            Dictionary with agent-compatible fields
        """
        return {
            "id": f"soundcloud:playlist:{self.id}",
            "title": self.title,
            "type": self.playlist_type,
            "is_album": self.is_album,
            "track_count": self.track_count,
            "duration": self.duration_seconds,
            "genre": self.genre,
            "tags": self.tags,
            "url": self.permalink_url,
            "artwork_url": self.artwork_url_high,
            "tracks": [track.to_agent_format() for track in self.tracks],
            "statistics": {
                "likes": self.likes_count,
                "reposts": self.reposts_count,
            },
            "metadata": {
                "label": self.label_name,
                "ean": self.ean,
                "release_date": self.release_date.isoformat() if self.release_date else None,
            },
            "source": "soundcloud",
        }
    
    def __len__(self) -> int:
        """Get number of tracks."""
        return len(self.tracks) + len(self._track_ids)
    
    def __iter__(self):
        """Iterate over tracks."""
        return iter(self.tracks)
    
    def __getitem__(self, index: int) -> Track:
        """Get track by index."""
        return self.tracks[index]


__all__ = ["Playlist"]