"""
Track model for SoundCloud.

Represents a SoundCloud track with all its metadata and functionality.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from .base import BaseModel
from ..types import TrackResponse, DownloadOptions


class Track(BaseModel):
    """Represents a SoundCloud track."""
    
    def __init__(self, data: Dict[str, Any], client=None):
        """
        Initialize track from API data.
        
        Args:
            data: Track data from API
            client: Optional SoundCloud client
        """
        # Core attributes
        self.id: int = 0
        self.title: str = ""
        self.artist: str = ""
        self.duration: int = 0  # milliseconds
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        
        # URLs
        self.permalink_url: str = ""
        self.stream_url: Optional[str] = None
        self.download_url: Optional[str] = None
        self.waveform_url: Optional[str] = None
        self.artwork_url: Optional[str] = None
        
        # Metadata
        self.genre: Optional[str] = None
        self.tags: List[str] = []
        self.description: Optional[str] = None
        self.bpm: Optional[float] = None
        self.key_signature: Optional[str] = None
        self.release_date: Optional[datetime] = None
        self.label_name: Optional[str] = None
        self.isrc: Optional[str] = None
        
        # Statistics
        self.playback_count: int = 0
        self.likes_count: int = 0
        self.reposts_count: int = 0
        self.comment_count: int = 0
        self.download_count: int = 0
        
        # Flags
        self.downloadable: bool = False
        self.streamable: bool = True
        self.public: bool = True
        self.commentable: bool = True
        
        # User info
        self.user_id: int = 0
        self.user: Optional[Dict[str, Any]] = None
        self.username: Optional[str] = None
        
        # Additional info
        self.license: Optional[str] = None
        self.purchase_url: Optional[str] = None
        self.video_url: Optional[str] = None
        self.media: Optional[Dict[str, Any]] = None
        
        # Extra attributes for downloads
        self.album: Optional[str] = None
        self.track_number: Optional[int] = None
        
        super().__init__(data, client)
    
    def _parse_data(self, data: Dict[str, Any]):
        """Parse raw API data into track attributes."""
        # Core attributes
        self.id = data.get("id", 0)
        self.title = data.get("title", "")
        self.duration = data.get("duration", 0)
        
        # Parse dates
        self.created_at = self._parse_datetime(data.get("created_at"))
        self.updated_at = self._parse_datetime(data.get("last_modified"))
        self.release_date = self._parse_release_date(data)
        
        # URLs
        self.permalink_url = data.get("permalink_url", "")
        self.stream_url = data.get("stream_url")
        self.download_url = data.get("download_url")
        self.waveform_url = data.get("waveform_url")
        self.artwork_url = data.get("artwork_url")
        
        # Metadata
        self.genre = data.get("genre")
        self.tags = self._parse_tags(data.get("tag_list", ""))
        self.description = data.get("description")
        self.bpm = data.get("bpm")
        self.key_signature = data.get("key_signature")
        self.label_name = data.get("label_name")
        self.isrc = data.get("isrc")
        
        # Statistics
        self.playback_count = data.get("playback_count", 0)
        self.likes_count = data.get("likes_count", data.get("favoritings_count", 0))
        self.reposts_count = data.get("reposts_count", 0)
        self.comment_count = data.get("comment_count", 0)
        self.download_count = data.get("download_count", 0)
        
        # Flags
        self.downloadable = data.get("downloadable", False)
        self.streamable = data.get("streamable", True)
        self.public = data.get("public", True)
        self.commentable = data.get("commentable", True)
        
        # User info
        self.user_id = data.get("user_id", 0)
        self.user = data.get("user")
        if self.user:
            self.username = self.user.get("username")
        
        # Parse artist from title or user
        self._parse_artist()
        
        # Additional info
        self.license = data.get("license")
        self.purchase_url = data.get("purchase_url")
        self.video_url = data.get("video_url")
        self.media = data.get("media")
    
    def _parse_artist(self):
        """Extract artist name from title or user."""
        # Try to extract from title (format: "Artist - Title")
        if " - " in self.title:
            parts = self.title.split(" - ", 1)
            self.artist = parts[0].strip()
            self.title = parts[1].strip()
        elif self.username:
            self.artist = self.username
        else:
            self.artist = "Unknown Artist"
    
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
        """Get duration in seconds."""
        return self.duration / 1000.0
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string (MM:SS)."""
        total_seconds = int(self.duration_seconds)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    @property
    def is_downloadable(self) -> bool:
        """Check if track can be downloaded."""
        return self.downloadable and bool(self.download_url)
    
    @property
    def artwork_url_high(self) -> Optional[str]:
        """Get high-quality artwork URL."""
        if not self.artwork_url:
            return None
        
        # Replace size in URL for higher quality
        return self.artwork_url.replace("-large", "-t500x500")
    
    async def download(self, options: Optional[DownloadOptions] = None) -> Path:
        """
        Download the track.
        
        Args:
            options: Download options
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
        """
        if not self._client:
            raise RuntimeError("Client required for download")
        
        # Delegate to client's download manager
        from ..download import DownloadManager
        
        manager = DownloadManager(self._client)
        return await manager.download_track(self, options)
    
    async def get_stream_url(self) -> Optional[str]:
        """
        Get streaming URL for the track.
        
        Returns:
            Stream URL if available
        """
        if not self._client:
            raise RuntimeError("Client required for stream URL")
        
        # If we have a stream URL, return it
        if self.stream_url:
            return self.stream_url
        
        # Otherwise, try to get it from media
        if self.media and self.media.get("transcodings"):
            # Find progressive stream
            for transcoding in self.media["transcodings"]:
                if transcoding.get("format", {}).get("protocol") == "progressive":
                    return transcoding.get("url")
        
        return None
    
    async def get_comments(self, limit: int = 50) -> List["Comment"]:
        """
        Get comments for this track.
        
        Args:
            limit: Maximum number of comments
            
        Returns:
            List of comments
        """
        if not self._client:
            raise RuntimeError("Client required for comments")
        
        from ..api import tracks
        return await tracks.get_comments(self._client, self.id, limit)
    
    async def like(self) -> bool:
        """
        Like this track.
        
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required for liking")
        
        from ..api import tracks
        return await tracks.like(self._client, self.id)
    
    async def unlike(self) -> bool:
        """
        Unlike this track.
        
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required for unliking")
        
        from ..api import tracks
        return await tracks.unlike(self._client, self.id)
    
    async def repost(self) -> bool:
        """
        Repost this track.
        
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required for reposting")
        
        from ..api import tracks
        return await tracks.repost(self._client, self.id)
    
    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to format suitable for music agent.
        
        Returns:
            Dictionary with agent-compatible fields
        """
        return {
            "id": f"soundcloud:{self.id}",
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration_seconds,
            "genre": self.genre,
            "tags": self.tags,
            "url": self.permalink_url,
            "artwork_url": self.artwork_url_high,
            "statistics": {
                "plays": self.playback_count,
                "likes": self.likes_count,
                "reposts": self.reposts_count,
                "comments": self.comment_count,
            },
            "metadata": {
                "bpm": self.bpm,
                "key": self.key_signature,
                "isrc": self.isrc,
                "label": self.label_name,
            },
            "source": "soundcloud",
        }


__all__ = ["Track"]