"""
User model for Mixcloud.

Represents a Mixcloud user account.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseModel
from ..types import UserResponse


class User(BaseModel):
    """Represents a Mixcloud user."""
    
    def _parse_data(self):
        """Parse user data."""
        # Basic info
        self.key = self._raw_data.get("key", "")
        self.url = self._raw_data.get("url", "")
        self.username = self._raw_data.get("username", "")
        self.name = self._raw_data.get("name", "")
        
        # Profile info
        self.biog = self._raw_data.get("biog", "")
        self.about = self._raw_data.get("about", "")
        self.city = self._raw_data.get("city", "")
        self.country = self._raw_data.get("country", "")
        
        # Images
        self.pictures = self._raw_data.get("pictures", {})
        self.picture = self.pictures.get("large", "") if self.pictures else ""
        self.thumbnail = self.pictures.get("medium", "") if self.pictures else ""
        self.cover_pictures = self._raw_data.get("cover_pictures", {})
        
        # Statistics
        self.follower_count = self._parse_int(self._raw_data.get("follower_count"))
        self.following_count = self._parse_int(self._raw_data.get("following_count"))
        self.cloudcast_count = self._parse_int(self._raw_data.get("cloudcast_count"))
        self.favorite_count = self._parse_int(self._raw_data.get("favorite_count"))
        self.listen_count = self._parse_int(self._raw_data.get("listen_count"))
        
        # Flags
        self.is_pro = self._parse_bool(self._raw_data.get("is_pro"))
        self.is_premium = self._parse_bool(self._raw_data.get("is_premium"))
        self.is_select = self._parse_bool(self._raw_data.get("is_select"))
        self.is_verified = self._parse_bool(self._raw_data.get("is_verified"))
        
        # Dates
        self.created_time = self._parse_datetime(self._raw_data.get("created_time"))
        self.updated_time = self._parse_datetime(self._raw_data.get("updated_time"))
        
        # Social links
        self.website_url = self._raw_data.get("website_url", "")
        self.twitter_username = self._raw_data.get("twitter_username", "")
        self.facebook_username = self._raw_data.get("facebook_username", "")
        self.instagram_username = self._raw_data.get("instagram_username", "")
        
        # Metadata counts (when included)
        self.metadata = self._raw_data.get("metadata", {})
        if self.metadata:
            connections = self.metadata.get("connections", {})
            self.follower_count = self.follower_count or connections.get("followers", 0)
            self.following_count = self.following_count or connections.get("following", 0)
            self.cloudcast_count = self.cloudcast_count or connections.get("cloudcasts", 0)
    
    @property
    def id(self) -> str:
        """Get user ID (username)."""
        return self.username
    
    @property
    def display_name(self) -> str:
        """Get display name (falls back to username)."""
        return self.name or self.username
    
    @property
    def mixcloud_url(self) -> str:
        """Get full Mixcloud URL."""
        if self.url and not self.url.startswith("http"):
            return f"https://www.mixcloud.com{self.url}"
        return self.url
    
    @property
    def avatar_url(self) -> str:
        """Get best available avatar URL."""
        if self.pictures:
            # Try to get in order of preference
            for size in ["extra_large", "large", "medium", "small", "thumbnail"]:
                if size in self.pictures and self.pictures[size]:
                    return self.pictures[size]
        return self.picture or self.thumbnail or ""
    
    @property
    def cover_url(self) -> str:
        """Get best available cover image URL."""
        if self.cover_pictures:
            # Try to get in order of preference
            for size in ["extra_large", "large", "medium", "small"]:
                if size in self.cover_pictures and self.cover_pictures[size]:
                    return self.cover_pictures[size]
        return ""
    
    @property
    def location(self) -> str:
        """Get formatted location string."""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)
    
    @property
    def has_pro_features(self) -> bool:
        """Check if user has any pro features."""
        return self.is_pro or self.is_premium or self.is_select
    
    @property
    def social_links(self) -> Dict[str, str]:
        """Get all social media links."""
        links = {}
        
        if self.website_url:
            links["website"] = self.website_url
        if self.twitter_username:
            links["twitter"] = f"https://twitter.com/{self.twitter_username}"
        if self.facebook_username:
            links["facebook"] = f"https://facebook.com/{self.facebook_username}"
        if self.instagram_username:
            links["instagram"] = f"https://instagram.com/{self.instagram_username}"
        
        return links
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user stats
        """
        return {
            "followers": self.follower_count or 0,
            "following": self.following_count or 0,
            "cloudcasts": self.cloudcast_count or 0,
            "favorites": self.favorite_count or 0,
            "listens": self.listen_count or 0,
        }
    
    def to_profile_info(self) -> Dict[str, Any]:
        """
        Convert to profile info format.
        
        Returns:
            Dictionary with profile information
        """
        return {
            "id": self.id,
            "username": self.username,
            "name": self.display_name,
            "url": self.mixcloud_url,
            "avatar_url": self.avatar_url,
            "cover_url": self.cover_url,
            "bio": self.biog or self.about,
            "location": self.location,
            "stats": self.get_stats(),
            "social_links": self.social_links,
            "is_pro": self.has_pro_features,
            "is_verified": self.is_verified,
            "created_at": self.created_time.isoformat() if self.created_time else None,
        }
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        return f"username='{self.username}', name='{self.display_name}'"


__all__ = ["User"]