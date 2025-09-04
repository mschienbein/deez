"""
Configuration for Bandcamp integration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ScraperConfig:
    """Scraper configuration."""
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: float = 0.5  # seconds between requests
    use_cache: bool = True
    cache_ttl: int = 3600  # 1 hour


@dataclass
class DownloadConfig:
    """Download configuration."""
    download_dir: str = "./downloads/bandcamp"
    chunk_size: int = 8192
    parallel_downloads: int = 3
    write_metadata: bool = True
    embed_artwork: bool = True
    embed_lyrics: bool = True
    format: str = "mp3"  # mp3, flac, etc.
    quality: str = "high"
    filename_template: str = "{artist} - {title}"
    create_artist_folders: bool = True
    create_album_folders: bool = True
    overwrite: bool = False
    
    def __post_init__(self):
        """Create download directory."""
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class SearchConfig:
    """Search configuration."""
    results_per_page: int = 20
    search_timeout: int = 10
    include_tracks: bool = True
    include_albums: bool = True
    include_artists: bool = True


@dataclass
class BandcampConfig:
    """Main Bandcamp configuration."""
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    
    # Feature flags
    enable_downloads: bool = True
    enable_search: bool = True
    enable_caching: bool = True
    debug: bool = False
    
    def __post_init__(self):
        """Load from environment variables."""
        self.enable_downloads = os.getenv("BANDCAMP_ENABLE_DOWNLOADS", "true").lower() == "true"
        self.enable_search = os.getenv("BANDCAMP_ENABLE_SEARCH", "true").lower() == "true"
        self.enable_caching = os.getenv("BANDCAMP_ENABLE_CACHING", "true").lower() == "true"
        self.debug = os.getenv("BANDCAMP_DEBUG", "false").lower() == "true"
        
        # Update download directory from env
        if env_dir := os.getenv("BANDCAMP_DOWNLOAD_DIR"):
            self.download.download_dir = env_dir
            Path(env_dir).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "BandcampConfig":
        """Create configuration from environment variables."""
        return cls()


__all__ = [
    "BandcampConfig",
    "ScraperConfig",
    "DownloadConfig",
    "SearchConfig",
]