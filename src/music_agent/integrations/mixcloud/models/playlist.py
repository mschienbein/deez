"""
Playlist model for Mixcloud.

Represents a playlist/collection of cloudcasts.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseModel
from .user import User
from ..types import PlaylistResponse


class Playlist(BaseModel):
    """Represents a Mixcloud playlist."""
    
    def _parse_data(self):
        """Parse playlist data."""
        # Basic info
        self.key = self._raw_data.get("key", "")
        self.url = self._raw_data.get("url", "")
        self.name = self._raw_data.get("name", "")
        self.slug = self._raw_data.get("slug", "")
        
        # Owner
        owner_data = self._raw_data.get("owner") or self._raw_data.get("user")
        self.owner = User(owner_data) if owner_data else None
        
        # Description
        self.description = self._raw_data.get("description", "")
        
        # Images
        self.pictures = self._raw_data.get("pictures", {})
        self.picture = self.pictures.get("large", "") if self.pictures else ""
        self.thumbnail = self.pictures.get("medium", "") if self.pictures else ""
        
        # Statistics
        self.cloudcast_count = self._parse_int(self._raw_data.get("cloudcast_count"))
        self.follower_count = self._parse_int(self._raw_data.get("follower_count"))
        self.play_count = self._parse_int(self._raw_data.get("play_count"))
        
        # Timestamps
        self.created_time = self._parse_datetime(self._raw_data.get("created_time"))
        self.updated_time = self._parse_datetime(self._raw_data.get("updated_time"))
        
        # Cloudcasts (if included)
        self.cloudcasts = self._raw_data.get("cloudcasts", [])
        
        # Flags
        self.is_public = self._parse_bool(self._raw_data.get("is_public", True))
        self.is_featured = self._parse_bool(self._raw_data.get("is_featured"))
    
    @property
    def id(self) -> str:
        """Get playlist ID."""
        return self.slug or self.key.strip("/").split("/")[-1]
    
    @property
    def owner_username(self) -> str:
        """Get owner username."""
        return self.owner.username if self.owner else ""
    
    @property
    def owner_display_name(self) -> str:
        """Get owner display name."""
        return self.owner.display_name if self.owner else ""
    
    @property
    def mixcloud_url(self) -> str:
        """Get full Mixcloud URL."""
        if self.url and not self.url.startswith("http"):
            return f"https://www.mixcloud.com{self.url}"
        return self.url
    
    @property
    def image_url(self) -> str:
        """Get best available image URL."""
        if self.pictures:
            # Try to get in order of preference
            for size in ["extra_large", "large", "medium", "small", "thumbnail"]:
                if size in self.pictures and self.pictures[size]:
                    return self.pictures[size]
        return self.picture or self.thumbnail or ""
    
    @property
    def total_duration(self) -> int:
        """Calculate total duration of all cloudcasts in seconds."""
        if not self.cloudcasts:
            return 0
        
        total = 0
        for cloudcast in self.cloudcasts:
            if isinstance(cloudcast, dict):
                duration = cloudcast.get("audio_length", 0)
                if duration:
                    total += duration
        return total
    
    @property
    def total_duration_formatted(self) -> str:
        """Get formatted total duration string."""
        total = self.total_duration
        if not total:
            return "00:00"
        
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_cloudcast_keys(self) -> List[str]:
        """
        Get list of cloudcast keys in playlist.
        
        Returns:
            List of cloudcast keys
        """
        keys = []
        for cloudcast in self.cloudcasts:
            if isinstance(cloudcast, dict) and "key" in cloudcast:
                keys.append(cloudcast["key"])
        return keys
    
    def get_cloudcast_urls(self) -> List[str]:
        """
        Get list of cloudcast URLs in playlist.
        
        Returns:
            List of cloudcast URLs
        """
        urls = []
        for cloudcast in self.cloudcasts:
            if isinstance(cloudcast, dict):
                url = cloudcast.get("url", "")
                if url and not url.startswith("http"):
                    url = f"https://www.mixcloud.com{url}"
                if url:
                    urls.append(url)
        return urls
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get playlist statistics.
        
        Returns:
            Dictionary with playlist stats
        """
        return {
            "cloudcasts": self.cloudcast_count or len(self.cloudcasts),
            "followers": self.follower_count or 0,
            "plays": self.play_count or 0,
            "total_duration": self.total_duration,
        }
    
    def to_info(self) -> Dict[str, Any]:
        """
        Convert to info format.
        
        Returns:
            Dictionary with playlist information
        """
        return {
            "id": self.id,
            "name": self.name,
            "url": self.mixcloud_url,
            "owner": self.owner_username,
            "owner_display_name": self.owner_display_name,
            "description": self.description,
            "image_url": self.image_url,
            "stats": self.get_stats(),
            "cloudcast_count": self.cloudcast_count or len(self.cloudcasts),
            "total_duration": self.total_duration_formatted,
            "is_public": self.is_public,
            "is_featured": self.is_featured,
            "created_at": self.created_time.isoformat() if self.created_time else None,
            "updated_at": self.updated_time.isoformat() if self.updated_time else None,
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        count = self.cloudcast_count or len(self.cloudcasts)
        return f"name='{self.name}', owner='{self.owner_username}', cloudcasts={count}"


__all__ = ["Playlist"]