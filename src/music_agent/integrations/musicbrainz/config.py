"""
Configuration for MusicBrainz API integration.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class MusicBrainzConfig:
    """MusicBrainz API configuration."""
    
    # API settings
    base_url: str = "https://musicbrainz.org/ws/2/"
    user_agent: str = "DeezMusicAgent/1.0"
    app_name: str = "DeezMusicAgent"
    app_version: str = "1.0"
    contact_email: Optional[str] = None
    
    # Rate limiting
    requests_per_second: float = 1.0  # MusicBrainz requires 1 req/sec
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Search defaults
    default_limit: int = 25
    max_limit: int = 100
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # Authentication (optional for higher rate limits)
    username: Optional[str] = None
    password: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "MusicBrainzConfig":
        """Create configuration from environment variables."""
        return cls(
            user_agent=os.getenv("MUSICBRAINZ_USER_AGENT", "DeezMusicAgent/1.0"),
            app_name=os.getenv("MUSICBRAINZ_APP_NAME", "DeezMusicAgent"),
            app_version=os.getenv("MUSICBRAINZ_APP_VERSION", "1.0"),
            contact_email=os.getenv("MUSICBRAINZ_CONTACT_EMAIL"),
            username=os.getenv("MUSICBRAINZ_USERNAME"),
            password=os.getenv("MUSICBRAINZ_PASSWORD"),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        # MusicBrainz requires a proper user agent
        if not self.user_agent or self.user_agent == "":
            raise ValueError("MusicBrainz requires a user agent string")
        
        # Recommend contact email for better rate limits
        if not self.contact_email:
            print("Warning: No contact email set. Consider setting MUSICBRAINZ_CONTACT_EMAIL for better rate limits.")