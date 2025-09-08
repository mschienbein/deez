"""
Configuration management for Deezer integration.

Handles all configuration options with environment variable support.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str = "https://www.deezer.com"
    api_base: str = "https://api.deezer.com"
    gateway_url: str = "https://www.deezer.com/ajax/gw-light.php"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: int = 20  # requests per second
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def __post_init__(self):
        """Load from environment variables."""
        self.base_url = os.getenv("DEEZER_BASE_URL", self.base_url)
        self.timeout = int(os.getenv("DEEZER_API_TIMEOUT", str(self.timeout)))
        self.max_retries = int(os.getenv("DEEZER_MAX_RETRIES", str(self.max_retries)))
        self.rate_limit = int(os.getenv("DEEZER_RATE_LIMIT", str(self.rate_limit)))


@dataclass
class AuthConfig:
    """Authentication configuration."""
    arl: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    session_file: str = "~/.deezer_session"
    auto_refresh: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.arl = os.getenv("DEEZER_ARL", self.arl)
        self.email = os.getenv("DEEZER_EMAIL", self.email)
        self.password = os.getenv("DEEZER_PASSWORD", self.password)
        self.session_file = os.path.expanduser(
            os.getenv("DEEZER_SESSION_FILE", self.session_file)
        )
        self.auto_refresh = os.getenv("DEEZER_AUTO_REFRESH", "true").lower() == "true"


@dataclass
class DownloadConfig:
    """Download configuration."""
    download_dir: str = "./downloads/deezer"
    parallel_downloads: int = 3
    chunk_size: int = 8192
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    write_metadata: bool = True
    embed_artwork: bool = True
    artwork_size: str = "1000x1000"
    create_folders: bool = True
    filename_template: str = "{artist} - {title}"
    overwrite: bool = False
    quality: str = "FLAC"  # FLAC, MP3_320, MP3_128
    fallback_quality: str = "MP3_320"  # If preferred quality not available
    
    def __post_init__(self):
        """Load from environment variables."""
        self.download_dir = os.getenv("DEEZER_DOWNLOAD_DIR", self.download_dir)
        self.parallel_downloads = int(
            os.getenv("DEEZER_PARALLEL_DOWNLOADS", str(self.parallel_downloads))
        )
        self.chunk_size = int(os.getenv("DEEZER_CHUNK_SIZE", str(self.chunk_size)))
        self.write_metadata = os.getenv("DEEZER_WRITE_METADATA", "true").lower() == "true"
        self.embed_artwork = os.getenv("DEEZER_EMBED_ARTWORK", "true").lower() == "true"
        self.overwrite = os.getenv("DEEZER_OVERWRITE", "false").lower() == "true"
        self.quality = os.getenv("DEEZER_QUALITY", self.quality)
        self.fallback_quality = os.getenv("DEEZER_FALLBACK_QUALITY", self.fallback_quality)
        
        # Create download directory if it doesn't exist
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class SearchConfig:
    """Search configuration."""
    default_limit: int = 25
    default_type: str = "track"  # track, album, artist, playlist
    cache_results: bool = True
    cache_ttl: int = 3600  # 1 hour
    fuzzy_matching: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.default_limit = int(os.getenv("DEEZER_SEARCH_LIMIT", str(self.default_limit)))
        self.default_type = os.getenv("DEEZER_SEARCH_TYPE", self.default_type)
        self.cache_results = os.getenv("DEEZER_CACHE_RESULTS", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("DEEZER_CACHE_TTL", str(self.cache_ttl)))


@dataclass
class StreamConfig:
    """Stream configuration."""
    buffer_size: int = 1024 * 1024  # 1MB
    enable_cache: bool = True
    cache_dir: str = "~/.deezer_cache"
    decrypt_streams: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.buffer_size = int(os.getenv("DEEZER_BUFFER_SIZE", str(self.buffer_size)))
        self.enable_cache = os.getenv("DEEZER_ENABLE_CACHE", "true").lower() == "true"
        self.cache_dir = os.path.expanduser(
            os.getenv("DEEZER_CACHE_DIR", self.cache_dir)
        )
        self.decrypt_streams = os.getenv("DEEZER_DECRYPT_STREAMS", "true").lower() == "true"


@dataclass
class DeezerConfig:
    """Main Deezer configuration."""
    api: APIConfig = field(default_factory=APIConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    stream: StreamConfig = field(default_factory=StreamConfig)
    
    # Feature flags
    enable_downloads: bool = True
    enable_lyrics: bool = True
    enable_flow: bool = True
    enable_radio: bool = True
    debug: bool = False
    
    def __post_init__(self):
        """Load feature flags from environment."""
        self.enable_downloads = os.getenv("DEEZER_ENABLE_DOWNLOADS", "true").lower() == "true"
        self.enable_lyrics = os.getenv("DEEZER_ENABLE_LYRICS", "true").lower() == "true"
        self.enable_flow = os.getenv("DEEZER_ENABLE_FLOW", "true").lower() == "true"
        self.enable_radio = os.getenv("DEEZER_ENABLE_RADIO", "true").lower() == "true"
        self.debug = os.getenv("DEEZER_DEBUG", "false").lower() == "true"
    
    @classmethod
    def from_env(cls) -> "DeezerConfig":
        """Create configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeezerConfig":
        """Create configuration from dictionary."""
        config = cls()
        
        # Update API config
        if "api" in data:
            for key, value in data["api"].items():
                if hasattr(config.api, key):
                    setattr(config.api, key, value)
        
        # Update Auth config
        if "auth" in data:
            for key, value in data["auth"].items():
                if hasattr(config.auth, key):
                    setattr(config.auth, key, value)
        
        # Update Download config
        if "download" in data:
            for key, value in data["download"].items():
                if hasattr(config.download, key):
                    setattr(config.download, key, value)
        
        # Update Search config
        if "search" in data:
            for key, value in data["search"].items():
                if hasattr(config.search, key):
                    setattr(config.search, key, value)
        
        # Update Stream config
        if "stream" in data:
            for key, value in data["stream"].items():
                if hasattr(config.stream, key):
                    setattr(config.stream, key, value)
        
        # Update feature flags
        for key in ["enable_downloads", "enable_lyrics", "enable_flow", "enable_radio", "debug"]:
            if key in data:
                setattr(config, key, data[key])
        
        return config


__all__ = [
    "DeezerConfig",
    "APIConfig",
    "AuthConfig",
    "DownloadConfig",
    "SearchConfig",
    "StreamConfig",
]