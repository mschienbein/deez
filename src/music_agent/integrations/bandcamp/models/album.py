"""
Album model for Bandcamp.
"""

from typing import Optional, List, Dict, Any

from .base import BaseModel
from .track import Track


class Album(BaseModel):
    """Represents a Bandcamp album."""
    
    def _parse_data(self):
        """Parse album data."""
        # Basic info
        self.id = self._data.get("id", "")
        self.title = self._data.get("title", "")
        self.artist = self._data.get("artist", "")
        self.artist_id = self._data.get("artist_id")
        self.url = self._data.get("url", "")
        
        # Metadata
        self.release_date = self._data.get("release_date")
        self.description = self._data.get("description")
        self.about = self._data.get("about")
        self.artwork_url = self._data.get("artwork_url")
        self.tags = self._data.get("tags", [])
        
        # Tracks
        tracks_data = self._data.get("tracks", [])
        self.tracks = [Track(track) for track in tracks_data]
        
        # Additional info
        self.label = self._data.get("label")
        self.format = self._data.get("format", "Digital")
        
        # Pricing
        self.price = self._data.get("price")
        self.currency = self._data.get("currency")
        self.free = self._data.get("free", False)
    
    @property
    def num_tracks(self) -> int:
        """Get number of tracks."""
        return len(self.tracks)
    
    @property
    def total_duration(self) -> int:
        """Get total duration in seconds."""
        return sum(track.duration or 0 for track in self.tracks)
    
    @property
    def total_duration_formatted(self) -> str:
        """Get formatted total duration."""
        total = self.total_duration
        if not total:
            return "00:00"
        
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_track_by_number(self, track_num: int) -> Optional[Track]:
        """
        Get track by number.
        
        Args:
            track_num: Track number
            
        Returns:
            Track or None
        """
        for track in self.tracks:
            if track.track_num == track_num:
                return track
        return None
    
    def get_track_by_title(self, title: str) -> Optional[Track]:
        """
        Get track by title.
        
        Args:
            title: Track title (case insensitive)
            
        Returns:
            Track or None
        """
        title_lower = title.lower()
        for track in self.tracks:
            if track.title.lower() == title_lower:
                return track
        return None
    
    def get_downloadable_tracks(self) -> List[Track]:
        """Get list of downloadable tracks."""
        return [track for track in self.tracks if track.is_downloadable]
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get album metadata.
        
        Returns:
            Metadata dictionary
        """
        return {
            "album": self.title,
            "albumartist": self.artist,
            "date": self.release_date,
            "genre": self.tags[0] if self.tags else None,
            "comment": self.description[:200] if self.description else None,
            "url": self.url,
            "artwork_url": self.artwork_url,
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for representation."""
        return f"title='{self.title}', artist='{self.artist}', tracks={self.num_tracks}"


__all__ = ["Album"]