"""
Cloudcast model for Mixcloud.

Represents a mix/show on Mixcloud.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseModel
from .user import User
from .tag import Tag
from ..types import CloudcastResponse


class Cloudcast(BaseModel):
    """Represents a Mixcloud cloudcast (mix/show)."""
    
    def _parse_data(self):
        """Parse cloudcast data."""
        # Basic info
        self.key = self._raw_data.get("key", "")
        self.url = self._raw_data.get("url", "")
        self.name = self._raw_data.get("name", "")
        self.slug = self._raw_data.get("slug", "")
        
        # User/owner
        user_data = self._raw_data.get("user")
        self.user = User(user_data) if user_data else None
        
        # Metadata
        self.description = self._raw_data.get("description", "")
        self.created_time = self._parse_datetime(self._raw_data.get("created_time"))
        self.updated_time = self._parse_datetime(self._raw_data.get("updated_time"))
        self.published_time = self._parse_datetime(self._raw_data.get("published_time"))
        
        # Audio info
        self.audio_length = self._parse_int(self._raw_data.get("audio_length"))
        self.duration = self.audio_length  # Alias
        
        # Images
        self.pictures = self._raw_data.get("pictures", {})
        self.picture = self.pictures.get("large", "") if self.pictures else ""
        self.thumbnail = self.pictures.get("medium", "") if self.pictures else ""
        
        # Statistics
        self.play_count = self._parse_int(self._raw_data.get("play_count"))
        self.listener_count = self._parse_int(self._raw_data.get("listener_count"))
        self.favorite_count = self._parse_int(self._raw_data.get("favorite_count"))
        self.repost_count = self._parse_int(self._raw_data.get("repost_count"))
        self.comment_count = self._parse_int(self._raw_data.get("comment_count"))
        
        # Tags
        tags_data = self._raw_data.get("tags", [])
        self.tags = Tag.from_list(tags_data) if tags_data else []
        
        # Sections/Tracklist
        self.sections = self._raw_data.get("sections", [])
        
        # Flags
        self.is_exclusive = self._parse_bool(self._raw_data.get("is_exclusive"))
        self.is_select = self._parse_bool(self._raw_data.get("is_select"))
        self.is_live = self._parse_bool(self._raw_data.get("is_live"))
        
        # URLs
        self.stream_url = self._raw_data.get("stream_url")
        self.preview_url = self._raw_data.get("preview_url")
        self.download_url = self._raw_data.get("download_url")
        
        # Additional metadata
        self.waveform_url = self._raw_data.get("waveform_url")
        self.license = self._raw_data.get("license")
    
    @property
    def id(self) -> str:
        """Get cloudcast ID (key without slashes)."""
        return self.key.replace("/", "_") if self.key else ""
    
    @property
    def username(self) -> str:
        """Get username of cloudcast owner."""
        return self.user.username if self.user else ""
    
    @property
    def user_url(self) -> str:
        """Get URL of cloudcast owner."""
        return self.user.url if self.user else ""
    
    @property
    def mixcloud_url(self) -> str:
        """Get full Mixcloud URL."""
        if self.url and not self.url.startswith("http"):
            return f"https://www.mixcloud.com{self.url}"
        return self.url
    
    @property
    def artwork_url(self) -> str:
        """Get best available artwork URL."""
        if self.pictures:
            # Try to get in order of preference
            for size in ["extra_large", "large", "medium", "small", "thumbnail"]:
                if size in self.pictures and self.pictures[size]:
                    return self.pictures[size]
        return self.picture or self.thumbnail or ""
    
    @property
    def duration_seconds(self) -> int:
        """Get duration in seconds."""
        return self.audio_length or 0
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.audio_length:
            return "00:00"
        
        hours = self.audio_length // 3600
        minutes = (self.audio_length % 3600) // 60
        seconds = self.audio_length % 60
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def tag_names(self) -> List[str]:
        """Get list of tag names."""
        return [tag.name for tag in self.tags]
    
    @property
    def is_downloadable(self) -> bool:
        """Check if cloudcast is downloadable."""
        return bool(self.download_url) and not self.is_exclusive
    
    @property
    def is_streamable(self) -> bool:
        """Check if cloudcast is streamable."""
        return bool(self.stream_url or self.preview_url)
    
    def get_stream_info(self) -> Dict[str, Any]:
        """
        Get stream information.
        
        Returns:
            Dictionary with stream URLs and metadata
        """
        return {
            "stream_url": self.stream_url,
            "preview_url": self.preview_url,
            "download_url": self.download_url,
            "is_exclusive": self.is_exclusive,
            "is_select": self.is_select,
            "is_downloadable": self.is_downloadable,
            "is_streamable": self.is_streamable,
            "duration": self.duration_seconds,
            "quality": "high" if self.stream_url else "preview",
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for tagging.
        
        Returns:
            Dictionary with metadata for ID3 tags
        """
        return {
            "title": self.name,
            "artist": self.username,
            "album": f"{self.username} - Mixcloud",
            "date": self.created_time.strftime("%Y") if self.created_time else None,
            "genre": self.tags[0].name if self.tags else None,
            "comment": self.description[:200] if self.description else None,
            "duration": self.duration_seconds,
            "url": self.mixcloud_url,
            "artwork_url": self.artwork_url,
        }
    
    def to_download_info(self) -> Dict[str, Any]:
        """
        Convert to download info format.
        
        Returns:
            Dictionary with download information
        """
        return {
            "id": self.id,
            "key": self.key,
            "url": self.mixcloud_url,
            "name": self.name,
            "username": self.username,
            "duration": self.duration_seconds,
            "artwork_url": self.artwork_url,
            "stream_info": self.get_stream_info(),
            "metadata": self.get_metadata(),
            "is_exclusive": self.is_exclusive,
            "created_at": self.created_time.isoformat() if self.created_time else None,
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        return f"name='{self.name}', user='{self.username}', duration={self.duration_formatted}"


__all__ = ["Cloudcast"]