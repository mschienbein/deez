"""
Configuration management for SoundCloud integration.

Handles settings, environment variables, and defaults.
"""

import os
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class APIConfig:
    """API-related configuration."""
    
    client_id: Optional[str] = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_CLIENT_ID")
    )
    client_secret: Optional[str] = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_CLIENT_SECRET")
    )
    access_token: Optional[str] = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_ACCESS_TOKEN")
    )
    refresh_token: Optional[str] = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_REFRESH_TOKEN")
    )
    
    # API endpoints
    base_url: str = "https://api.soundcloud.com"
    api_v2_url: str = "https://api-v2.soundcloud.com"
    
    # Request settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    
    # Rate limiting
    requests_per_second: int = 15
    rate_limit_buffer: float = 0.1  # 10% buffer


@dataclass
class DownloadConfig:
    """Download-related configuration."""
    
    download_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("SOUNDCLOUD_DOWNLOAD_DIR", "./downloads/soundcloud")
        )
    )
    temp_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("SOUNDCLOUD_TEMP_DIR", "./temp/soundcloud")
        )
    )
    
    # Download settings
    chunk_size: int = 8192
    parallel_downloads: int = field(
        default_factory=lambda: int(os.getenv("SOUNDCLOUD_PARALLEL_DOWNLOADS", "5"))
    )
    download_quality: str = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_DOWNLOAD_QUALITY", "high")
    )
    
    # Features
    write_metadata: bool = True
    embed_artwork: bool = True
    artwork_size: str = "original"
    normalize_audio: bool = False
    
    # HLS settings
    enable_hls: bool = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_ENABLE_HLS", "true").lower() == "true"
    )
    hls_segment_timeout: int = 10
    hls_max_retries: int = 3
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class CacheConfig:
    """Cache-related configuration."""
    
    enable_cache: bool = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_ENABLE_CACHE", "true").lower() == "true"
    )
    cache_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("SOUNDCLOUD_CACHE_DIR", "./cache/soundcloud")
        )
    )
    
    # TTL values (in seconds)
    client_id_ttl: int = 86400  # 24 hours
    track_ttl: int = 3600  # 1 hour
    user_ttl: int = 3600  # 1 hour
    search_ttl: int = 1800  # 30 minutes
    stream_url_ttl: int = 300  # 5 minutes
    
    # Cache size limits
    max_cache_size_mb: int = 100
    max_entries: int = 1000
    
    def __post_init__(self):
        """Create cache directory if it doesn't exist."""
        if self.enable_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class ScraperConfig:
    """Web scraping configuration."""
    
    # Pages to scrape for client IDs
    scrape_urls: List[str] = field(default_factory=lambda: [
        "https://soundcloud.com/",
        "https://soundcloud.com/discover",
        "https://soundcloud.com/charts/top",
        "https://soundcloud.com/charts/new",
    ])
    
    # Scraping settings
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ])
    
    # Client ID pool
    client_id_pool_size: int = 5
    client_id_rotation_enabled: bool = True
    client_id_validation_interval: int = 3600  # 1 hour


@dataclass
class SoundCloudConfig:
    """Main configuration container."""
    
    api: APIConfig = field(default_factory=APIConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    
    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_LOG_LEVEL", "INFO")
    )
    log_file: Optional[Path] = field(
        default_factory=lambda: Path(os.getenv("SOUNDCLOUD_LOG_FILE")) 
        if os.getenv("SOUNDCLOUD_LOG_FILE") else None
    )
    
    # Feature flags
    enable_analytics: bool = False
    enable_telemetry: bool = False
    debug_mode: bool = field(
        default_factory=lambda: os.getenv("SOUNDCLOUD_DEBUG", "false").lower() == "true"
    )
    
    @classmethod
    def from_env(cls) -> "SoundCloudConfig":
        """Create configuration from environment variables."""
        return cls()
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "SoundCloudConfig":
        """Create configuration from dictionary."""
        api_config = APIConfig(**config_dict.get("api", {}))
        download_config = DownloadConfig(**config_dict.get("download", {}))
        cache_config = CacheConfig(**config_dict.get("cache", {}))
        scraper_config = ScraperConfig(**config_dict.get("scraper", {}))
        
        return cls(
            api=api_config,
            download=download_config,
            cache=cache_config,
            scraper=scraper_config,
            **{k: v for k, v in config_dict.items() 
               if k not in ["api", "download", "cache", "scraper"]}
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "api": {
                k: str(v) if isinstance(v, Path) else v
                for k, v in self.api.__dict__.items()
            },
            "download": {
                k: str(v) if isinstance(v, Path) else v
                for k, v in self.download.__dict__.items()
            },
            "cache": {
                k: str(v) if isinstance(v, Path) else v
                for k, v in self.cache.__dict__.items()
            },
            "scraper": {
                k: v for k, v in self.scraper.__dict__.items()
            },
            "log_level": self.log_level,
            "log_file": str(self.log_file) if self.log_file else None,
            "enable_analytics": self.enable_analytics,
            "enable_telemetry": self.enable_telemetry,
            "debug_mode": self.debug_mode,
        }


# Default configuration instance
default_config = SoundCloudConfig()


__all__ = [
    "APIConfig",
    "DownloadConfig", 
    "CacheConfig",
    "ScraperConfig",
    "SoundCloudConfig",
    "default_config",
]