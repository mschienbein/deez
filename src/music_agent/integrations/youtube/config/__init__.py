"""
YouTube configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class YouTubeAuthConfig:
    """Configuration for YouTube authentication."""
    
    cookies_file: Optional[str] = None
    api_key: Optional[str] = None  # For YouTube Data API (optional)
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "YouTubeAuthConfig":
        """Create configuration from environment variables."""
        return cls(
            cookies_file=os.getenv("YOUTUBE_COOKIES_FILE"),
            api_key=os.getenv("YOUTUBE_API_KEY"),
            oauth_client_id=os.getenv("YOUTUBE_CLIENT_ID"),
            oauth_client_secret=os.getenv("YOUTUBE_CLIENT_SECRET")
        )


@dataclass
class DownloadConfig:
    """Configuration for downloads."""
    
    output_dir: str = "./downloads/youtube"
    audio_format: str = "mp3"  # mp3, m4a, opus, etc.
    audio_quality: str = "0"  # 0 = best, 9 = worst
    video_quality: str = "bestvideo+bestaudio"
    extract_audio: bool = True
    embed_metadata: bool = True
    embed_thumbnail: bool = True
    write_info_json: bool = False
    write_subtitles: bool = False
    subtitle_langs: List[str] = field(default_factory=lambda: ["en"])
    concurrent_downloads: int = 3
    rate_limit: Optional[str] = None  # e.g., "50K" for 50KB/s
    retries: int = 3
    
    @classmethod
    def from_env(cls) -> "DownloadConfig":
        """Create configuration from environment variables."""
        return cls(
            output_dir=os.getenv("YOUTUBE_DOWNLOAD_DIR", "./downloads/youtube"),
            audio_format=os.getenv("YOUTUBE_AUDIO_FORMAT", "mp3"),
            audio_quality=os.getenv("YOUTUBE_AUDIO_QUALITY", "0"),
            video_quality=os.getenv("YOUTUBE_VIDEO_QUALITY", "bestvideo+bestaudio"),
            extract_audio=os.getenv("YOUTUBE_EXTRACT_AUDIO", "true").lower() == "true",
            embed_metadata=os.getenv("YOUTUBE_EMBED_METADATA", "true").lower() == "true",
            embed_thumbnail=os.getenv("YOUTUBE_EMBED_THUMBNAIL", "true").lower() == "true",
            concurrent_downloads=int(os.getenv("YOUTUBE_CONCURRENT_DOWNLOADS", "3")),
            rate_limit=os.getenv("YOUTUBE_RATE_LIMIT"),
            retries=int(os.getenv("YOUTUBE_RETRIES", "3"))
        )


@dataclass
class SearchConfig:
    """Configuration for search operations."""
    
    default_limit: int = 10
    max_results: int = 50
    search_timeout: int = 30
    include_shorts: bool = False
    safe_search: bool = False
    region_code: str = "US"
    language: str = "en"
    

@dataclass
class PlaylistConfig:
    """Configuration for playlist operations."""
    
    max_items: int = 500
    reverse_order: bool = False
    start_index: int = 1
    end_index: Optional[int] = None
    date_after: Optional[str] = None  # YYYYMMDD
    date_before: Optional[str] = None  # YYYYMMDD
    match_filter: Optional[str] = None  # yt-dlp filter expression
    reject_filter: Optional[str] = None
    

@dataclass
class YtDlpConfig:
    """Configuration for yt-dlp options."""
    
    executable: str = "yt-dlp"
    update_on_start: bool = False
    quiet: bool = False
    no_warnings: bool = False
    ignore_errors: bool = True
    no_check_certificate: bool = False
    prefer_free_formats: bool = False
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    cache_dir: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "YtDlpConfig":
        """Create configuration from environment variables."""
        return cls(
            executable=os.getenv("YTDLP_EXECUTABLE", "yt-dlp"),
            update_on_start=os.getenv("YTDLP_UPDATE", "false").lower() == "true",
            quiet=os.getenv("YTDLP_QUIET", "false").lower() == "true",
            ignore_errors=os.getenv("YTDLP_IGNORE_ERRORS", "true").lower() == "true",
            cache_dir=os.getenv("YTDLP_CACHE_DIR")
        )


@dataclass
class YouTubeConfig:
    """Main YouTube configuration."""
    
    auth: YouTubeAuthConfig = field(default_factory=YouTubeAuthConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    playlist: PlaylistConfig = field(default_factory=PlaylistConfig)
    ytdlp: YtDlpConfig = field(default_factory=YtDlpConfig)
    
    @classmethod
    def from_env(cls) -> "YouTubeConfig":
        """Create configuration from environment variables."""
        return cls(
            auth=YouTubeAuthConfig.from_env(),
            download=DownloadConfig.from_env(),
            search=SearchConfig(),
            playlist=PlaylistConfig(),
            ytdlp=YtDlpConfig.from_env()
        )