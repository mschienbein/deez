"""
YouTube data models.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Thumbnail:
    """Video thumbnail."""
    
    url: str
    width: int
    height: int
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Thumbnail":
        """Create from API response."""
        return cls(
            url=data.get("url", ""),
            width=data.get("width", 0),
            height=data.get("height", 0)
        )


@dataclass
class Video:
    """YouTube video."""
    
    id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    duration: int  # seconds
    view_count: int
    like_count: int
    upload_date: str
    thumbnails: List[Thumbnail] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    url: str = ""
    is_live: bool = False
    is_upcoming: bool = False
    availability: str = "public"
    age_restricted: bool = False
    
    def __post_init__(self):
        """Post-initialization."""
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.id}"
    
    @classmethod
    def from_ytdlp(cls, data: Dict[str, Any]) -> "Video":
        """Create from yt-dlp response."""
        thumbnails = []
        for thumb in data.get("thumbnails", []):
            thumbnails.append(Thumbnail.from_api(thumb))
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=(data.get("description") or "")[:500],  # Truncate
            channel_id=data.get("channel_id", ""),
            channel_title=data.get("uploader", ""),
            duration=data.get("duration", 0),
            view_count=data.get("view_count", 0),
            like_count=data.get("like_count", 0),
            upload_date=data.get("upload_date", ""),
            thumbnails=thumbnails,
            tags=data.get("tags", []),
            url=data.get("webpage_url", ""),
            is_live=data.get("is_live", False),
            age_restricted=data.get("age_limit", 0) > 0,
            availability=data.get("availability", "public")
        )
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Video":
        """Create from YouTube Data API response."""
        snippet = data.get("snippet", {})
        statistics = data.get("statistics", {})
        content_details = data.get("contentDetails", {})
        
        # Parse duration from ISO 8601
        duration_str = content_details.get("duration", "PT0S")
        duration = cls._parse_duration(duration_str)
        
        thumbnails = []
        for size, thumb_data in snippet.get("thumbnails", {}).items():
            thumbnails.append(Thumbnail.from_api(thumb_data))
        
        return cls(
            id=data.get("id", ""),
            title=snippet.get("title", ""),
            description=(snippet.get("description") or "")[:500],
            channel_id=snippet.get("channelId", ""),
            channel_title=snippet.get("channelTitle", ""),
            duration=duration,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            upload_date=snippet.get("publishedAt", ""),
            thumbnails=thumbnails,
            tags=snippet.get("tags", []),
            is_live=snippet.get("liveBroadcastContent") == "live",
            is_upcoming=snippet.get("liveBroadcastContent") == "upcoming"
        )
    
    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def to_music_track(self) -> Dict[str, Any]:
        """Convert to music track format."""
        # Try to extract artist and track from title
        artist = self.channel_title
        track_title = self.title
        
        # Common patterns: "Artist - Title", "Artist: Title"
        for sep in [" - ", ": "]:
            if sep in self.title:
                parts = self.title.split(sep, 1)
                if len(parts) == 2:
                    artist, track_title = parts
                    break
        
        # Clean up common suffixes
        for suffix in [" (Official Video)", " (Official Audio)", " [Official Video]", " (Lyrics)"]:
            if track_title.endswith(suffix):
                track_title = track_title[:-len(suffix)]
        
        return {
            "id": self.id,
            "title": track_title.strip(),
            "artist": artist.strip(),
            "album": "",
            "duration": self.duration,
            "platform": "youtube",
            "platform_url": self.url,
            "thumbnail": self.thumbnails[0].url if self.thumbnails else "",
            "available": self.availability == "public",
            "metadata": {
                "view_count": self.view_count,
                "like_count": self.like_count,
                "upload_date": self.upload_date,
                "channel": self.channel_title,
                "tags": self.tags
            }
        }


@dataclass
class Playlist:
    """YouTube playlist."""
    
    id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    video_count: int
    thumbnails: List[Thumbnail] = field(default_factory=list)
    videos: List[Video] = field(default_factory=list)
    url: str = ""
    visibility: str = "public"
    
    def __post_init__(self):
        """Post-initialization."""
        if not self.url:
            self.url = f"https://www.youtube.com/playlist?list={self.id}"
    
    @classmethod
    def from_ytdlp(cls, data: Dict[str, Any]) -> "Playlist":
        """Create from yt-dlp response."""
        thumbnails = []
        for thumb in data.get("thumbnails", []):
            thumbnails.append(Thumbnail.from_api(thumb))
        
        # Parse videos if included
        videos = []
        for entry in data.get("entries", []):
            if entry:
                videos.append(Video.from_ytdlp(entry))
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=(data.get("description") or "")[:500],
            channel_id=data.get("channel_id", ""),
            channel_title=data.get("uploader", ""),
            video_count=data.get("playlist_count", len(videos)),
            thumbnails=thumbnails,
            videos=videos,
            url=data.get("webpage_url", ""),
            visibility=data.get("availability", "public")
        )
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Playlist":
        """Create from YouTube Data API response."""
        snippet = data.get("snippet", {})
        content_details = data.get("contentDetails", {})
        
        thumbnails = []
        for size, thumb_data in snippet.get("thumbnails", {}).items():
            thumbnails.append(Thumbnail.from_api(thumb_data))
        
        return cls(
            id=data.get("id", ""),
            title=snippet.get("title", ""),
            description=(snippet.get("description") or "")[:500],
            channel_id=snippet.get("channelId", ""),
            channel_title=snippet.get("channelTitle", ""),
            video_count=content_details.get("itemCount", 0),
            thumbnails=thumbnails,
            visibility=data.get("status", {}).get("privacyStatus", "public")
        )


@dataclass
class Channel:
    """YouTube channel."""
    
    id: str
    title: str
    description: str
    subscriber_count: int
    video_count: int
    view_count: int
    thumbnails: List[Thumbnail] = field(default_factory=list)
    url: str = ""
    custom_url: Optional[str] = None
    country: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization."""
        if not self.url:
            self.url = f"https://www.youtube.com/channel/{self.id}"
    
    @classmethod
    def from_ytdlp(cls, data: Dict[str, Any]) -> "Channel":
        """Create from yt-dlp response."""
        thumbnails = []
        for thumb in data.get("thumbnails", []):
            thumbnails.append(Thumbnail.from_api(thumb))
        
        return cls(
            id=data.get("id", ""),
            title=data.get("uploader", ""),
            description=(data.get("description") or "")[:500],
            subscriber_count=data.get("subscriber_count", 0),
            video_count=data.get("playlist_count", 0),
            view_count=data.get("view_count", 0),
            thumbnails=thumbnails,
            url=data.get("uploader_url", "")
        )
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Channel":
        """Create from YouTube Data API response."""
        snippet = data.get("snippet", {})
        statistics = data.get("statistics", {})
        
        thumbnails = []
        for size, thumb_data in snippet.get("thumbnails", {}).items():
            thumbnails.append(Thumbnail.from_api(thumb_data))
        
        return cls(
            id=data.get("id", ""),
            title=snippet.get("title", ""),
            description=(snippet.get("description") or "")[:500],
            subscriber_count=int(statistics.get("subscriberCount", 0)),
            video_count=int(statistics.get("videoCount", 0)),
            view_count=int(statistics.get("viewCount", 0)),
            thumbnails=thumbnails,
            custom_url=snippet.get("customUrl"),
            country=snippet.get("country")
        )


@dataclass
class SearchResult:
    """YouTube search result."""
    
    videos: List[Video] = field(default_factory=list)
    playlists: List[Playlist] = field(default_factory=list)
    channels: List[Channel] = field(default_factory=list)
    next_page_token: Optional[str] = None
    total_results: int = 0
    
    @classmethod
    def from_ytdlp(cls, entries: List[Dict[str, Any]]) -> "SearchResult":
        """Create from yt-dlp search results."""
        videos = []
        playlists = []
        channels = []
        
        for entry in entries:
            if not entry:
                continue
            
            # Determine type based on available fields
            if entry.get("_type") == "playlist":
                playlists.append(Playlist.from_ytdlp(entry))
            elif entry.get("_type") == "channel":
                channels.append(Channel.from_ytdlp(entry))
            else:
                videos.append(Video.from_ytdlp(entry))
        
        return cls(
            videos=videos,
            playlists=playlists,
            channels=channels,
            total_results=len(videos) + len(playlists) + len(channels)
        )


@dataclass
class DownloadProgress:
    """Download progress information."""
    
    video_id: str
    filename: str
    status: str  # downloading, finished, error
    downloaded_bytes: int
    total_bytes: int
    speed: Optional[float] = None  # bytes per second
    eta: Optional[int] = None  # seconds
    percent: float = 0.0
    error: Optional[str] = None
    
    @classmethod
    def from_ytdlp(cls, data: Dict[str, Any]) -> "DownloadProgress":
        """Create from yt-dlp progress hook."""
        return cls(
            video_id=data.get("info_dict", {}).get("id", ""),
            filename=data.get("filename", ""),
            status=data.get("status", ""),
            downloaded_bytes=data.get("downloaded_bytes", 0),
            total_bytes=data.get("total_bytes", 0) or data.get("total_bytes_estimate", 0),
            speed=data.get("speed"),
            eta=data.get("eta"),
            percent=data.get("downloaded_bytes", 0) / max(data.get("total_bytes", 1), 1) * 100
        )