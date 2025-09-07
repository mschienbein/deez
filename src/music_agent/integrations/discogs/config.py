"""
Configuration for Discogs API integration.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DiscogsConfig:
    """Discogs API configuration."""
    
    # Authentication
    user_token: Optional[str] = None
    consumer_key: Optional[str] = None
    consumer_secret: Optional[str] = None
    
    # API settings
    base_url: str = "https://api.discogs.com"
    user_agent: str = "MusicAgent/1.0"
    
    # Rate limiting
    requests_per_minute: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Search defaults
    default_per_page: int = 50
    max_per_page: int = 100
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    @classmethod
    def from_env(cls) -> "DiscogsConfig":
        """Create configuration from environment variables."""
        return cls(
            user_token=os.getenv("DISCOGS_USER_TOKEN"),
            consumer_key=os.getenv("DISCOGS_CONSUMER_KEY"),
            consumer_secret=os.getenv("DISCOGS_CONSUMER_SECRET"),
            user_agent=os.getenv("DISCOGS_USER_AGENT", "MusicAgent/1.0"),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        # Authentication is optional but recommended for better rate limits
        if not self.user_token and not (self.consumer_key and self.consumer_secret):
            print("Warning: No Discogs authentication configured. Rate limits will be restricted.")
        pass