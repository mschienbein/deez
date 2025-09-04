"""
Configuration management for Mixcloud integration.

Handles all configuration options with environment variable support.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str = "https://api.mixcloud.com"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: int = 20  # requests per second
    user_agent: str = "MixcloudClient/1.0"
    
    def __post_init__(self):
        """Load from environment variables."""
        self.base_url = os.getenv("MIXCLOUD_API_URL", self.base_url)
        self.timeout = int(os.getenv("MIXCLOUD_API_TIMEOUT", str(self.timeout)))
        self.max_retries = int(os.getenv("MIXCLOUD_MAX_RETRIES", str(self.max_retries)))
        self.rate_limit = int(os.getenv("MIXCLOUD_RATE_LIMIT", str(self.rate_limit)))


@dataclass
class AuthConfig:
    """Authentication configuration."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:8080/callback"
    scope: str = ""  # No specific scopes in Mixcloud
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_file: str = "~/.mixcloud_token"
    
    def __post_init__(self):
        """Load from environment variables."""
        self.client_id = os.getenv("MIXCLOUD_CLIENT_ID", self.client_id)
        self.client_secret = os.getenv("MIXCLOUD_CLIENT_SECRET", self.client_secret)
        self.redirect_uri = os.getenv("MIXCLOUD_REDIRECT_URI", self.redirect_uri)
        self.access_token = os.getenv("MIXCLOUD_ACCESS_TOKEN", self.access_token)
        self.refresh_token = os.getenv("MIXCLOUD_REFRESH_TOKEN", self.refresh_token)
        
        # Expand token file path
        self.token_file = os.path.expanduser(self.token_file)


@dataclass
class DownloadConfig:
    """Download configuration."""
    download_dir: str = "./downloads"
    parallel_downloads: int = 3
    chunk_size: int = 8192
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    write_metadata: bool = True
    embed_artwork: bool = True
    artwork_size: str = "large"  # small, medium, large, extra_large
    create_folders: bool = True  # Create user/show folders
    filename_template: str = "{user} - {name}.mp3"
    overwrite: bool = False
    quality: str = "high"  # high, medium, low
    format: str = "mp3"  # mp3, m4a, original
    
    def __post_init__(self):
        """Load from environment variables."""
        self.download_dir = os.getenv("MIXCLOUD_DOWNLOAD_DIR", self.download_dir)
        self.parallel_downloads = int(os.getenv("MIXCLOUD_PARALLEL_DOWNLOADS", str(self.parallel_downloads)))
        self.chunk_size = int(os.getenv("MIXCLOUD_CHUNK_SIZE", str(self.chunk_size)))
        self.write_metadata = os.getenv("MIXCLOUD_WRITE_METADATA", "true").lower() == "true"
        self.embed_artwork = os.getenv("MIXCLOUD_EMBED_ARTWORK", "true").lower() == "true"
        self.overwrite = os.getenv("MIXCLOUD_OVERWRITE", "false").lower() == "true"
        
        # Create download directory if it doesn't exist
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    backend: str = "memory"  # memory, file, redis
    cache_dir: str = "~/.mixcloud_cache"
    default_ttl: int = 3600  # 1 hour
    max_size: int = 1000  # Maximum cache entries
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    def __post_init__(self):
        """Load from environment variables."""
        self.enabled = os.getenv("MIXCLOUD_CACHE_ENABLED", "true").lower() == "true"
        self.backend = os.getenv("MIXCLOUD_CACHE_BACKEND", self.backend)
        self.cache_dir = os.path.expanduser(os.getenv("MIXCLOUD_CACHE_DIR", self.cache_dir))
        self.default_ttl = int(os.getenv("MIXCLOUD_CACHE_TTL", str(self.default_ttl)))
        self.max_size = int(os.getenv("MIXCLOUD_CACHE_MAX_SIZE", str(self.max_size)))
        
        # Redis settings
        self.redis_host = os.getenv("REDIS_HOST", self.redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", str(self.redis_port)))
        self.redis_db = int(os.getenv("REDIS_DB", str(self.redis_db)))
        self.redis_password = os.getenv("REDIS_PASSWORD", self.redis_password)


@dataclass
class SearchConfig:
    """Search configuration."""
    default_limit: int = 20
    max_limit: int = 100
    default_type: str = "cloudcast"  # cloudcast, user, tag
    enable_fuzzy: bool = True
    cache_results: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.default_limit = int(os.getenv("MIXCLOUD_SEARCH_LIMIT", str(self.default_limit)))
        self.max_limit = int(os.getenv("MIXCLOUD_SEARCH_MAX_LIMIT", str(self.max_limit)))
        self.default_type = os.getenv("MIXCLOUD_SEARCH_TYPE", self.default_type)
        self.cache_results = os.getenv("MIXCLOUD_CACHE_SEARCH", "true").lower() == "true"


@dataclass
class StreamConfig:
    """Stream extraction configuration."""
    prefer_hls: bool = True
    fallback_to_preview: bool = True
    extract_method: str = "api"  # api, scrape, hybrid
    use_cdn_urls: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.prefer_hls = os.getenv("MIXCLOUD_PREFER_HLS", "true").lower() == "true"
        self.fallback_to_preview = os.getenv("MIXCLOUD_FALLBACK_PREVIEW", "true").lower() == "true"
        self.extract_method = os.getenv("MIXCLOUD_EXTRACT_METHOD", self.extract_method)


@dataclass
class MixcloudConfig:
    """Main Mixcloud configuration."""
    api: APIConfig = field(default_factory=APIConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    stream: StreamConfig = field(default_factory=StreamConfig)
    
    # Feature flags
    enable_downloads: bool = True
    enable_uploads: bool = False
    enable_live: bool = False
    enable_analytics: bool = False
    debug: bool = False
    
    def __post_init__(self):
        """Load feature flags from environment."""
        self.enable_downloads = os.getenv("MIXCLOUD_ENABLE_DOWNLOADS", "true").lower() == "true"
        self.enable_uploads = os.getenv("MIXCLOUD_ENABLE_UPLOADS", "false").lower() == "true"
        self.enable_live = os.getenv("MIXCLOUD_ENABLE_LIVE", "false").lower() == "true"
        self.enable_analytics = os.getenv("MIXCLOUD_ENABLE_ANALYTICS", "false").lower() == "true"
        self.debug = os.getenv("MIXCLOUD_DEBUG", "false").lower() == "true"
    
    @classmethod
    def from_env(cls) -> "MixcloudConfig":
        """Create configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MixcloudConfig":
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
        
        # Update Cache config
        if "cache" in data:
            for key, value in data["cache"].items():
                if hasattr(config.cache, key):
                    setattr(config.cache, key, value)
        
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
        for key in ["enable_downloads", "enable_uploads", "enable_live", "enable_analytics", "debug"]:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api": {
                "base_url": self.api.base_url,
                "timeout": self.api.timeout,
                "max_retries": self.api.max_retries,
                "rate_limit": self.api.rate_limit,
                "user_agent": self.api.user_agent,
            },
            "auth": {
                "client_id": self.auth.client_id,
                "client_secret": self.auth.client_secret,
                "redirect_uri": self.auth.redirect_uri,
                "access_token": self.auth.access_token,
            },
            "download": {
                "download_dir": self.download.download_dir,
                "parallel_downloads": self.download.parallel_downloads,
                "chunk_size": self.download.chunk_size,
                "write_metadata": self.download.write_metadata,
                "embed_artwork": self.download.embed_artwork,
                "quality": self.download.quality,
                "format": self.download.format,
            },
            "cache": {
                "enabled": self.cache.enabled,
                "backend": self.cache.backend,
                "default_ttl": self.cache.default_ttl,
                "max_size": self.cache.max_size,
            },
            "search": {
                "default_limit": self.search.default_limit,
                "default_type": self.search.default_type,
                "cache_results": self.search.cache_results,
            },
            "stream": {
                "prefer_hls": self.stream.prefer_hls,
                "fallback_to_preview": self.stream.fallback_to_preview,
                "extract_method": self.stream.extract_method,
            },
            "enable_downloads": self.enable_downloads,
            "enable_uploads": self.enable_uploads,
            "enable_live": self.enable_live,
            "enable_analytics": self.enable_analytics,
            "debug": self.debug,
        }


__all__ = [
    "MixcloudConfig",
    "APIConfig",
    "AuthConfig",
    "DownloadConfig",
    "CacheConfig",
    "SearchConfig",
    "StreamConfig",
]