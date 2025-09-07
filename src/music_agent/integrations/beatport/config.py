"""
Configuration for Beatport API integration.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BeatportConfig:
    """Beatport API configuration."""
    
    # Authentication
    username: Optional[str] = None
    password: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    
    # API settings
    base_url: str = "https://api.beatport.com"
    api_version: str = "v4"
    docs_url: str = "https://api.beatport.com/v4/docs/"
    client_id: Optional[str] = None  # Will be scraped from docs if not provided
    
    # Token management
    token_file: Optional[str] = None
    auto_refresh: bool = True
    
    # Request settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5  # Delay between requests
    
    # Search defaults
    default_per_page: int = 25
    max_per_page: int = 150
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    @classmethod
    def from_env(cls) -> "BeatportConfig":
        """Create configuration from environment variables."""
        token_file = os.getenv("BEATPORT_TOKEN_FILE")
        if not token_file:
            token_file = str(Path.home() / ".beatport_token.json")
            
        return cls(
            username=os.getenv("BEATPORT_USERNAME"),
            password=os.getenv("BEATPORT_PASSWORD"),
            access_token=os.getenv("BEATPORT_ACCESS_TOKEN"),
            refresh_token=os.getenv("BEATPORT_REFRESH_TOKEN"),
            client_id=os.getenv("BEATPORT_CLIENT_ID"),
            token_file=token_file,
            timeout=int(os.getenv("BEATPORT_TIMEOUT", "30")),
            rate_limit_delay=float(os.getenv("BEATPORT_RATE_LIMIT", "0.5")),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.access_token and not (self.username and self.password):
            raise ValueError(
                "Beatport authentication required. "
                "Set either BEATPORT_ACCESS_TOKEN or both "
                "BEATPORT_USERNAME and BEATPORT_PASSWORD"
            )
    
    def save_token(self, token_data: Dict[str, Any]) -> None:
        """
        Save token data to file.
        
        Args:
            token_data: Token data to save
        """
        if self.token_file:
            Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """
        Load token data from file.
        
        Returns:
            Token data or None if not found
        """
        if self.token_file and Path(self.token_file).exists():
            try:
                with open(self.token_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None