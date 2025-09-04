"""
Track model for Bandcamp.
"""

from typing import Optional, List, Dict, Any

from .base import BaseModel


class Track(BaseModel):
    """Represents a Bandcamp track."""
    
    def _parse_data(self):
        """Parse track data."""
        # Basic info
        self.id = self._data.get("id", "")
        self.title = self._data.get("title", "")
        self.artist = self._data.get("artist", "")
        self.album = self._data.get("album")
        self.url = self._data.get("url", "")
        
        # Audio info
        self.duration = self._data.get("duration")  # in seconds
        self.track_num = self._data.get("track_num")
        
        # Streaming/download
        self.stream_url = self._data.get("stream_url")
        self.download_url = self._data.get("download_url")
        self.file_format = self._data.get("file_format", "mp3")
        
        # Metadata
        self.release_date = self._data.get("release_date")
        self.lyrics = self._data.get("lyrics")
        self.tags = self._data.get("tags", [])
        
        # Pricing
        self.price = self._data.get("price")
        self.currency = self._data.get("currency")
        self.free = self._data.get("free", False)
    
    @property
    def is_streamable(self) -> bool:
        """Check if track can be streamed."""
        return bool(self.stream_url)
    
    @property
    def is_downloadable(self) -> bool:
        """Check if track can be downloaded."""
        return bool(self.download_url or self.stream_url)
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration:
            return "00:00"
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for tagging.
        
        Returns:
            Metadata dictionary
        """
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "track": self.track_num,
            "date": self.release_date,
            "genre": self.tags[0] if self.tags else None,
            "comment": f"Downloaded from Bandcamp: {self.url}",
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for representation."""
        return f"title='{self.title}', artist='{self.artist}'"


__all__ = ["Track"]