"""
User model for Deezer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum


class UserSubscription(Enum):
    """User subscription types."""
    FREE = "free"
    PREMIUM = "premium"
    PREMIUM_PLUS = "premium+"
    FAMILY = "family"
    STUDENT = "student"
    HIFI = "hifi"


@dataclass
class User:
    """Represents a Deezer user."""
    
    # Base fields
    id: str
    type: str = "user"
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # User fields
    name: str = ""
    lastname: Optional[str] = None
    firstname: Optional[str] = None
    email: Optional[str] = None
    status: int = 0
    birthday: Optional[datetime] = None
    inscription_date: Optional[datetime] = None
    gender: Optional[str] = None
    link: Optional[str] = None
    picture: Optional[str] = None
    picture_small: Optional[str] = None
    picture_medium: Optional[str] = None
    picture_big: Optional[str] = None
    picture_xl: Optional[str] = None
    country: Optional[str] = None
    lang: Optional[str] = None
    is_kid: bool = False
    explicit_content_level: Optional[str] = None
    explicit_content_levels_available: List[str] = field(default_factory=list)
    tracklist: Optional[str] = None
    
    # Subscription info
    subscription: Optional[UserSubscription] = None
    has_audio_ads: bool = True
    has_unlimited_downloads: bool = False
    has_hq: bool = False
    has_lossless: bool = False
    
    def __post_init__(self):
        """Initialize type."""
        self.type = "user"
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "User":
        """Create User from API response."""
        # Parse dates
        birthday = None
        if data.get("birthday"):
            try:
                birthday = datetime.strptime(data["birthday"], "%Y-%m-%d")
            except (ValueError, TypeError):
                pass
        
        inscription_date = None
        if data.get("inscription_date"):
            try:
                inscription_date = datetime.fromisoformat(data["inscription_date"])
            except (ValueError, TypeError):
                pass
        
        # Parse subscription
        subscription = None
        if data.get("subscription"):
            try:
                subscription = UserSubscription(data["subscription"].lower())
            except (ValueError, KeyError):
                pass
        
        return cls(
            id=str(data.get("id", "")),
            type="user",
            name=data.get("name", ""),
            lastname=data.get("lastname"),
            firstname=data.get("firstname"),
            email=data.get("email"),
            status=data.get("status", 0),
            birthday=birthday,
            inscription_date=inscription_date,
            gender=data.get("gender"),
            link=data.get("link"),
            picture=data.get("picture"),
            picture_small=data.get("picture_small"),
            picture_medium=data.get("picture_medium"),
            picture_big=data.get("picture_big"),
            picture_xl=data.get("picture_xl"),
            country=data.get("country"),
            lang=data.get("lang"),
            is_kid=data.get("is_kid", False),
            explicit_content_level=data.get("explicit_content_level"),
            explicit_content_levels_available=data.get("explicit_content_levels_available", []),
            tracklist=data.get("tracklist"),
            subscription=subscription,
            raw_data=data,
        )