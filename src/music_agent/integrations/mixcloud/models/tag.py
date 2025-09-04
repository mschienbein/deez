"""
Tag model for Mixcloud.

Represents a genre or tag on Mixcloud.
"""

from typing import Dict, Any, Optional

from .base import BaseModel
from ..types import TagResponse


class Tag(BaseModel):
    """Represents a Mixcloud tag/genre."""
    
    def _parse_data(self):
        """Parse tag data."""
        # Basic info
        self.key = self._raw_data.get("key", "")
        self.url = self._raw_data.get("url", "")
        self.name = self._raw_data.get("name", "")
        self.slug = self._raw_data.get("slug", "")
        
        # Statistics
        self.cloudcast_count = self._parse_int(self._raw_data.get("cloudcast_count"))
        self.follower_count = self._parse_int(self._raw_data.get("follower_count"))
        
        # Images
        self.pictures = self._raw_data.get("pictures", {})
        self.picture = self.pictures.get("large", "") if self.pictures else ""
        self.thumbnail = self.pictures.get("medium", "") if self.pictures else ""
    
    @property
    def id(self) -> str:
        """Get tag ID (slug)."""
        return self.slug or self.key.strip("/").split("/")[-1]
    
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
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get tag statistics.
        
        Returns:
            Dictionary with tag stats
        """
        return {
            "cloudcasts": self.cloudcast_count or 0,
            "followers": self.follower_count or 0,
        }
    
    def to_info(self) -> Dict[str, Any]:
        """
        Convert to info format.
        
        Returns:
            Dictionary with tag information
        """
        return {
            "id": self.id,
            "name": self.name,
            "url": self.mixcloud_url,
            "image_url": self.image_url,
            "stats": self.get_stats(),
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        return f"name='{self.name}'"


__all__ = ["Tag"]