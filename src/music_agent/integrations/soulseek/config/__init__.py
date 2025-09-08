"""
Soulseek/slskd configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SlskdConfig:
    """Configuration for slskd server connection."""
    
    host: str = "http://localhost:5030"
    port: int = 5030
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url_base: str = "/"
    no_auth: bool = False
    
    @classmethod
    def from_env(cls) -> "SlskdConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("SLSKD_HOST", "http://localhost:5030"),
            port=int(os.getenv("SLSKD_PORT", "5030")),
            api_key=os.getenv("SLSKD_API_KEY"),
            username=os.getenv("SLSKD_USERNAME"),
            password=os.getenv("SLSKD_PASSWORD"),
            url_base=os.getenv("SLSKD_URL_BASE", "/"),
            no_auth=os.getenv("SLSKD_NO_AUTH", "false").lower() == "true"
        )


@dataclass
class SearchConfig:
    """Configuration for search operations."""
    
    default_min_bitrate: int = 320
    default_max_results: int = 50
    default_timeout: int = 10
    file_limit_multiplier: float = 2.0  # Get extra results to filter
    filter_responses: bool = True
    wait_time: int = 5  # Time to wait for results to populate
    

@dataclass
class DownloadConfig:
    """Configuration for download operations."""
    
    output_dir: str = "./downloads/soulseek"
    max_wait_time: int = 300  # Max time to wait for download in seconds
    monitor_interval: int = 2  # Interval to check download status
    create_folders: bool = True
    overwrite: bool = False
    
    @classmethod
    def from_env(cls) -> "DownloadConfig":
        """Create configuration from environment variables."""
        return cls(
            output_dir=os.getenv("SOULSEEK_DOWNLOAD_DIR", "./downloads/soulseek"),
            max_wait_time=int(os.getenv("SOULSEEK_DOWNLOAD_TIMEOUT", "300")),
            monitor_interval=int(os.getenv("SOULSEEK_MONITOR_INTERVAL", "2")),
            create_folders=os.getenv("SOULSEEK_CREATE_FOLDERS", "true").lower() == "true",
            overwrite=os.getenv("SOULSEEK_OVERWRITE", "false").lower() == "true"
        )


@dataclass
class SoulseekConfig:
    """Main Soulseek configuration."""
    
    slskd: SlskdConfig = field(default_factory=SlskdConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    enable_memory: bool = False
    
    @classmethod
    def from_env(cls) -> "SoulseekConfig":
        """Create configuration from environment variables."""
        return cls(
            slskd=SlskdConfig.from_env(),
            search=SearchConfig(),
            download=DownloadConfig.from_env(),
            enable_memory=os.getenv("SOULSEEK_ENABLE_MEMORY", "false").lower() == "true"
        )