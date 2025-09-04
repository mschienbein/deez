"""
Category model for Mixcloud.

Represents a content category on Mixcloud.
"""

from typing import Dict, Any, Optional, List

from .base import BaseModel
from ..types import CategoryResponse


class Category(BaseModel):
    """Represents a Mixcloud category."""
    
    def _parse_data(self):
        """Parse category data."""
        # Basic info
        self.key = self._raw_data.get("key", "")
        self.url = self._raw_data.get("url", "")
        self.name = self._raw_data.get("name", "")
        self.slug = self._raw_data.get("slug", "")
        self.format = self._raw_data.get("format", "")
        
        # Description
        self.description = self._raw_data.get("description", "")
        
        # Images
        self.pictures = self._raw_data.get("pictures", {})
        self.picture = self.pictures.get("large", "") if self.pictures else ""
        self.thumbnail = self.pictures.get("medium", "") if self.pictures else ""
        
        # Statistics
        self.cloudcast_count = self._parse_int(self._raw_data.get("cloudcast_count"))
        self.follower_count = self._parse_int(self._raw_data.get("follower_count"))
        
        # Subcategories
        self.subcategories = self._raw_data.get("subcategories", [])
    
    @property
    def id(self) -> str:
        """Get category ID (slug)."""
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
    
    @property
    def has_subcategories(self) -> bool:
        """Check if category has subcategories."""
        return bool(self.subcategories)
    
    def get_subcategory_names(self) -> List[str]:
        """
        Get list of subcategory names.
        
        Returns:
            List of subcategory names
        """
        names = []
        for subcat in self.subcategories:
            if isinstance(subcat, dict) and "name" in subcat:
                names.append(subcat["name"])
            elif isinstance(subcat, str):
                names.append(subcat)
        return names
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get category statistics.
        
        Returns:
            Dictionary with category stats
        """
        return {
            "cloudcasts": self.cloudcast_count or 0,
            "followers": self.follower_count or 0,
            "subcategories": len(self.subcategories),
        }
    
    def to_info(self) -> Dict[str, Any]:
        """
        Convert to info format.
        
        Returns:
            Dictionary with category information
        """
        return {
            "id": self.id,
            "name": self.name,
            "format": self.format,
            "url": self.mixcloud_url,
            "description": self.description,
            "image_url": self.image_url,
            "stats": self.get_stats(),
            "subcategories": self.get_subcategory_names(),
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        return f"name='{self.name}', format='{self.format}'"


__all__ = ["Category"]