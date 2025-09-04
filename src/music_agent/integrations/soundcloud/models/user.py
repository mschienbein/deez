"""
User model for SoundCloud.

Represents a SoundCloud user profile.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseModel
from ..types import UserResponse


class User(BaseModel):
    """Represents a SoundCloud user."""
    
    def __init__(self, data: Dict[str, Any], client=None):
        """
        Initialize user from API data.
        
        Args:
            data: User data from API
            client: Optional SoundCloud client
        """
        # Core attributes
        self.id: int = 0
        self.username: str = ""
        self.permalink: str = ""
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        
        # URLs
        self.permalink_url: str = ""
        self.avatar_url: Optional[str] = None
        self.uri: str = ""
        
        # Profile info
        self.full_name: Optional[str] = None
        self.first_name: Optional[str] = None
        self.last_name: Optional[str] = None
        self.description: Optional[str] = None
        self.city: Optional[str] = None
        self.country: Optional[str] = None
        
        # Social links
        self.website: Optional[str] = None
        self.website_title: Optional[str] = None
        self.discogs_name: Optional[str] = None
        self.myspace_name: Optional[str] = None
        
        # Statistics
        self.track_count: int = 0
        self.playlist_count: int = 0
        self.followers_count: int = 0
        self.followings_count: int = 0
        self.likes_count: int = 0
        self.reposts_count: int = 0
        self.comments_count: int = 0
        
        # Status
        self.online: bool = False
        self.plan: str = "Free"  # Free, Pro, Pro Unlimited
        
        # Verification
        self.verified: bool = False
        
        super().__init__(data, client)
    
    def _parse_data(self, data: Dict[str, Any]):
        """Parse raw API data into user attributes."""
        # Core attributes
        self.id = data.get("id", 0)
        self.username = data.get("username", "")
        self.permalink = data.get("permalink", "")
        
        # Parse dates
        self.created_at = self._parse_datetime(data.get("created_at"))
        self.updated_at = self._parse_datetime(data.get("last_modified"))
        
        # URLs
        self.permalink_url = data.get("permalink_url", "")
        self.avatar_url = data.get("avatar_url")
        self.uri = data.get("uri", "")
        
        # Profile info
        self.full_name = data.get("full_name")
        self.first_name = data.get("first_name")
        self.last_name = data.get("last_name")
        self.description = data.get("description")
        self.city = data.get("city")
        self.country = data.get("country")
        
        # Social links
        self.website = data.get("website")
        self.website_title = data.get("website_title")
        self.discogs_name = data.get("discogs_name")
        self.myspace_name = data.get("myspace_name")
        
        # Statistics
        self.track_count = data.get("track_count", 0)
        self.playlist_count = data.get("playlist_count", 0)
        self.followers_count = data.get("followers_count", 0)
        self.followings_count = data.get("followings_count", 0)
        self.likes_count = data.get("public_favorites_count", 0)
        self.reposts_count = data.get("reposts_count", 0)
        self.comments_count = data.get("comments_count", 0)
        
        # Status
        self.online = data.get("online", False)
        self.plan = data.get("plan", "Free")
        
        # Verification
        self.verified = data.get("verified", False)
    
    @property
    def display_name(self) -> str:
        """Get display name (full name or username)."""
        return self.full_name or self.username
    
    @property
    def avatar_url_high(self) -> Optional[str]:
        """Get high-quality avatar URL."""
        if not self.avatar_url:
            return None
        
        # Replace size in URL for higher quality
        return self.avatar_url.replace("-large", "-t500x500")
    
    @property
    def is_pro(self) -> bool:
        """Check if user has Pro account."""
        return self.plan and "Pro" in self.plan
    
    async def get_tracks(self, limit: int = 50) -> List["Track"]:
        """
        Get user's tracks.
        
        Args:
            limit: Maximum number of tracks
            
        Returns:
            List of tracks
        """
        if not self._client:
            raise RuntimeError("Client required to get tracks")
        
        from ..api import users
        return await users.get_tracks(self._client, self.id, limit)
    
    async def get_playlists(self, limit: int = 50) -> List["Playlist"]:
        """
        Get user's playlists.
        
        Args:
            limit: Maximum number of playlists
            
        Returns:
            List of playlists
        """
        if not self._client:
            raise RuntimeError("Client required to get playlists")
        
        from ..api import users
        return await users.get_playlists(self._client, self.id, limit)
    
    async def get_likes(self, limit: int = 50) -> List["Track"]:
        """
        Get user's liked tracks.
        
        Args:
            limit: Maximum number of tracks
            
        Returns:
            List of liked tracks
        """
        if not self._client:
            raise RuntimeError("Client required to get likes")
        
        from ..api import users
        return await users.get_likes(self._client, self.id, limit)
    
    async def get_reposts(self, limit: int = 50) -> List[Any]:
        """
        Get user's reposts.
        
        Args:
            limit: Maximum number of reposts
            
        Returns:
            List of reposted items (tracks/playlists)
        """
        if not self._client:
            raise RuntimeError("Client required to get reposts")
        
        from ..api import users
        return await users.get_reposts(self._client, self.id, limit)
    
    async def get_followers(self, limit: int = 50) -> List["User"]:
        """
        Get user's followers.
        
        Args:
            limit: Maximum number of followers
            
        Returns:
            List of followers
        """
        if not self._client:
            raise RuntimeError("Client required to get followers")
        
        from ..api import users
        return await users.get_followers(self._client, self.id, limit)
    
    async def get_followings(self, limit: int = 50) -> List["User"]:
        """
        Get users this user follows.
        
        Args:
            limit: Maximum number of followings
            
        Returns:
            List of followed users
        """
        if not self._client:
            raise RuntimeError("Client required to get followings")
        
        from ..api import users
        return await users.get_followings(self._client, self.id, limit)
    
    async def follow(self) -> bool:
        """
        Follow this user.
        
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required to follow")
        
        from ..api import users
        return await users.follow(self._client, self.id)
    
    async def unfollow(self) -> bool:
        """
        Unfollow this user.
        
        Returns:
            True if successful
        """
        if not self._client:
            raise RuntimeError("Client required to unfollow")
        
        from ..api import users
        return await users.unfollow(self._client, self.id)
    
    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to format suitable for music agent.
        
        Returns:
            Dictionary with agent-compatible fields
        """
        return {
            "id": f"soundcloud:user:{self.id}",
            "username": self.username,
            "display_name": self.display_name,
            "url": self.permalink_url,
            "avatar_url": self.avatar_url_high,
            "location": {
                "city": self.city,
                "country": self.country,
            },
            "statistics": {
                "tracks": self.track_count,
                "playlists": self.playlist_count,
                "followers": self.followers_count,
                "followings": self.followings_count,
                "likes": self.likes_count,
                "reposts": self.reposts_count,
            },
            "metadata": {
                "plan": self.plan,
                "verified": self.verified,
                "website": self.website,
                "description": self.description,
            },
            "source": "soundcloud",
        }


__all__ = ["User"]