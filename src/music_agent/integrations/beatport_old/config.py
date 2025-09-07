"""
Beatport configuration management.
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class BeatportConfig:
    """Configuration for Beatport integration."""
    
    # Authentication
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[int] = None
    
    # API settings
    base_url: str = "https://api.beatport.com/v4"
    auth_url: str = "https://api.beatport.com/v4/auth"
    docs_url: str = "https://api.beatport.com/v4/docs/"
    
    # Request settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5  # Delay between requests
    
    # Storage
    token_file: Optional[str] = None
    auto_refresh_token: bool = True
    
    # Features
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # Debug
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "BeatportConfig":
        """Create config from environment variables."""
        return cls(
            username=os.getenv("BEATPORT_USERNAME"),
            password=os.getenv("BEATPORT_PASSWORD"),
            client_id=os.getenv("BEATPORT_CLIENT_ID"),
            token_file=os.getenv("BEATPORT_TOKEN_FILE", "~/.beatport_token.json"),
            debug=os.getenv("BEATPORT_DEBUG", "false").lower() == "true",
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> "BeatportConfig":
        """Load config from JSON file."""
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(path) as f:
            data = json.load(f)
        
        return cls(**data)
    
    def save_token(self, token_data: Dict[str, Any]):
        """Save token data to file."""
        if not self.token_file:
            return
        
        path = Path(self.token_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update config with new token data
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        self.token_expires_at = token_data.get("expires_at")
        
        # Save to file
        with open(path, "w") as f:
            json.dump(token_data, f, indent=2)
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token data from file."""
        if not self.token_file:
            return None
        
        path = Path(self.token_file).expanduser()
        if not path.exists():
            return None
        
        try:
            with open(path) as f:
                token_data = json.load(f)
            
            # Update config with loaded token
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_expires_at = token_data.get("expires_at")
            
            return token_data
        except (json.JSONDecodeError, IOError):
            return None
    
    def clear_token(self):
        """Clear stored token."""
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        if self.token_file:
            path = Path(self.token_file).expanduser()
            if path.exists():
                path.unlink()