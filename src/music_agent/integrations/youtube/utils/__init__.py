"""
YouTube utility functions.
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


def parse_youtube_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse YouTube URL to extract type and ID.
    
    Args:
        url: YouTube URL
        
    Returns:
        Dictionary with 'type' and 'id' keys, or None if invalid
    """
    # Video ID patterns
    video_patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)",
        r"youtube\.com/embed/([a-zA-Z0-9_-]+)",
        r"youtube\.com/v/([a-zA-Z0-9_-]+)",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]+)"
    ]
    
    for pattern in video_patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "type": "video",
                "id": match.group(1)
            }
    
    # Playlist pattern
    playlist_match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
    if playlist_match:
        return {
            "type": "playlist",
            "id": playlist_match.group(1)
        }
    
    # Channel patterns
    channel_patterns = [
        r"youtube\.com/channel/([a-zA-Z0-9_-]+)",
        r"youtube\.com/c/([a-zA-Z0-9_-]+)",
        r"youtube\.com/@([a-zA-Z0-9_-]+)",
        r"youtube\.com/user/([a-zA-Z0-9_-]+)"
    ]
    
    for pattern in channel_patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "type": "channel",
                "id": match.group(1),
                "handle": match.group(1) if "@" in pattern else None
            }
    
    return None


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID or None
    """
    result = parse_youtube_url(url)
    if result and result["type"] == "video":
        return result["id"]
    return None


def extract_playlist_id(url: str) -> Optional[str]:
    """
    Extract playlist ID from YouTube URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        Playlist ID or None
    """
    result = parse_youtube_url(url)
    if result and result["type"] == "playlist":
        return result["id"]
    return None


def build_video_url(video_id: str) -> str:
    """
    Build YouTube video URL from ID.
    
    Args:
        video_id: Video ID
        
    Returns:
        Full YouTube URL
    """
    return f"https://www.youtube.com/watch?v={video_id}"


def build_playlist_url(playlist_id: str) -> str:
    """
    Build YouTube playlist URL from ID.
    
    Args:
        playlist_id: Playlist ID
        
    Returns:
        Full YouTube playlist URL
    """
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def build_channel_url(channel_id: str) -> str:
    """
    Build YouTube channel URL from ID.
    
    Args:
        channel_id: Channel ID or handle
        
    Returns:
        Full YouTube channel URL
    """
    if channel_id.startswith("@"):
        return f"https://www.youtube.com/{channel_id}"
    elif channel_id.startswith("UC"):
        return f"https://www.youtube.com/channel/{channel_id}"
    else:
        return f"https://www.youtube.com/c/{channel_id}"


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration (e.g., "3:45", "1:02:30")
    """
    if seconds < 0:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: Duration string (e.g., "3:45", "1:02:30", "PT3M45S")
        
    Returns:
        Duration in seconds
    """
    # ISO 8601 format (PT3M45S)
    iso_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if iso_match:
        hours = int(iso_match.group(1) or 0)
        minutes = int(iso_match.group(2) or 0)
        seconds = int(iso_match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    
    # Standard format (3:45 or 1:02:30)
    parts = duration_str.split(':')
    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    
    return 0


def extract_music_metadata(title: str, channel: str = "") -> Dict[str, str]:
    """
    Extract artist and track from video title.
    
    Args:
        title: Video title
        channel: Channel name (optional)
        
    Returns:
        Dictionary with 'artist' and 'track' keys
    """
    # Remove common suffixes
    suffixes_to_remove = [
        " (Official Video)",
        " (Official Music Video)",
        " (Official Audio)",
        " (Official Lyric Video)",
        " (Lyric Video)",
        " (Lyrics)",
        " [Official Video]",
        " [Official Audio]",
        " [Official Music Video]",
        " [Lyric Video]",
        " [Lyrics]",
        " (Audio)",
        " [Audio]",
        " (HD)",
        " [HD]",
        " (HQ)",
        " [HQ]",
        " (4K)",
        " [4K]"
    ]
    
    clean_title = title
    for suffix in suffixes_to_remove:
        if clean_title.endswith(suffix):
            clean_title = clean_title[:-len(suffix)]
            break
    
    # Try to parse artist and track
    artist = ""
    track = clean_title
    
    # Common patterns: "Artist - Title", "Artist: Title", "Artist | Title"
    separators = [" - ", ": ", " | ", " – ", " — "]
    for sep in separators:
        if sep in clean_title:
            parts = clean_title.split(sep, 1)
            if len(parts) == 2:
                artist, track = parts
                break
    
    # Pattern: "Title by Artist" or "Title (by Artist)"
    by_match = re.search(r'^(.+?)\s+(?:\()?by\s+(.+?)(?:\))?$', clean_title, re.IGNORECASE)
    if by_match:
        track = by_match.group(1).strip()
        artist = by_match.group(2).strip()
    
    # If no artist found, use channel name if it looks like an artist
    if not artist and channel:
        # Remove "VEVO", "Official", etc. from channel
        channel_clean = re.sub(r'(?:VEVO|Official|Music|Records|Entertainment).*$', '', channel, flags=re.IGNORECASE).strip()
        if channel_clean and not any(word in channel_clean.lower() for word in ['youtube', 'channel', 'topic']):
            artist = channel_clean
    
    # Clean up featuring artists
    feat_patterns = [
        r'\s+\(feat\.?\s+(.+?)\)',
        r'\s+\[feat\.?\s+(.+?)\]',
        r'\s+ft\.?\s+(.+?)(?:\s|$)',
        r'\s+featuring\s+(.+?)(?:\s|$)'
    ]
    
    featuring = ""
    for pattern in feat_patterns:
        match = re.search(pattern, track, re.IGNORECASE)
        if match:
            featuring = match.group(1)
            track = re.sub(pattern, '', track, flags=re.IGNORECASE)
            break
    
    result = {
        "artist": artist.strip(),
        "track": track.strip(),
        "featuring": featuring.strip() if featuring else ""
    }
    
    return result


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for filesystem.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Trim whitespace
    filename = filename.strip('. ')
    
    # Truncate if too long
    if len(filename) > max_length:
        # Keep extension if present
        parts = filename.rsplit('.', 1)
        if len(parts) == 2 and len(parts[1]) <= 4:
            name, ext = parts
            max_name_length = max_length - len(ext) - 1
            filename = f"{name[:max_name_length]}.{ext}"
        else:
            filename = filename[:max_length]
    
    # Fallback if empty
    if not filename:
        filename = "untitled"
    
    return filename


def estimate_filesize(duration: int, bitrate: int = 128) -> int:
    """
    Estimate audio file size.
    
    Args:
        duration: Duration in seconds
        bitrate: Bitrate in kbps (default 128)
        
    Returns:
        Estimated file size in bytes
    """
    # Convert bitrate to bytes per second
    bytes_per_second = (bitrate * 1000) / 8
    
    # Calculate total size
    return int(duration * bytes_per_second)


def format_filesize(size_bytes: int) -> str:
    """
    Format file size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size (e.g., "3.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def is_music_video(title: str, channel: str = "", duration: int = 0) -> bool:
    """
    Check if a video is likely music content.
    
    Args:
        title: Video title
        channel: Channel name
        duration: Duration in seconds
        
    Returns:
        True if likely music content
    """
    title_lower = title.lower()
    channel_lower = channel.lower() if channel else ""
    
    # Music indicators in title
    music_title_indicators = [
        "official video", "official audio", "music video",
        "audio", "lyrics", "lyric video", "visualizer",
        "full album", "single", "ep", "remix", "cover",
        "acoustic", "live performance", "live session"
    ]
    
    for indicator in music_title_indicators:
        if indicator in title_lower:
            return True
    
    # Music channel indicators
    music_channel_indicators = [
        "vevo", "records", "music", "entertainment",
        "official", "band", "artist"
    ]
    
    for indicator in music_channel_indicators:
        if indicator in channel_lower:
            return True
    
    # Check if it's a topic channel
    if channel_lower.endswith(" - topic"):
        return True
    
    # Check duration (most music is 2-7 minutes)
    if 120 <= duration <= 420:
        # More likely to be music
        return True
    
    return False


def get_thumbnail_url(video_id: str, quality: str = "maxresdefault") -> str:
    """
    Get thumbnail URL for a video.
    
    Args:
        video_id: Video ID
        quality: Thumbnail quality (default, mqdefault, hqdefault, sddefault, maxresdefault)
        
    Returns:
        Thumbnail URL
    """
    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"