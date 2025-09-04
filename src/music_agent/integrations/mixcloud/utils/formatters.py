"""
Formatting utilities for Mixcloud integration.

Provides functions for formatting data for display.
"""

from typing import Any, Optional
from datetime import datetime, timedelta


def format_duration(seconds: Optional[int]) -> str:
    """
    Format duration in seconds to readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (HH:MM:SS or MM:SS)
    """
    if not seconds:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_date(date: Optional[datetime], format: str = "%Y-%m-%d") -> str:
    """
    Format datetime to string.
    
    Args:
        date: Datetime object
        format: Date format string
        
    Returns:
        Formatted date string
    """
    if not date:
        return ""
    
    return date.strftime(format)


def format_relative_time(date: Optional[datetime]) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").
    
    Args:
        date: Datetime object
        
    Returns:
        Relative time string
    """
    if not date:
        return ""
    
    now = datetime.now(date.tzinfo)
    delta = now - date
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def format_number(number: Optional[int]) -> str:
    """
    Format number with thousand separators.
    
    Args:
        number: Number to format
        
    Returns:
        Formatted number string
    """
    if number is None:
        return "0"
    
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)


def format_file_size(bytes: int) -> str:
    """
    Format file size in bytes to human readable string.
    
    Args:
        bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def format_bitrate(bitrate: int) -> str:
    """
    Format bitrate to string.
    
    Args:
        bitrate: Bitrate in bps
        
    Returns:
        Formatted bitrate string
    """
    if bitrate >= 1000:
        return f"{bitrate // 1000} kbps"
    return f"{bitrate} bps"


def format_percentage(value: float, total: float) -> str:
    """
    Format value as percentage of total.
    
    Args:
        value: Current value
        total: Total value
        
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0%"
    
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_cloudcast_info(cloudcast: Any) -> str:
    """
    Format cloudcast information for display.
    
    Args:
        cloudcast: Cloudcast object
        
    Returns:
        Formatted cloudcast info string
    """
    parts = []
    
    # Add name and user
    parts.append(f"🎵 {cloudcast.name}")
    parts.append(f"👤 by {cloudcast.username}")
    
    # Add duration
    if cloudcast.duration_seconds:
        parts.append(f"⏱ {format_duration(cloudcast.duration_seconds)}")
    
    # Add stats
    if cloudcast.play_count:
        parts.append(f"▶️ {format_number(cloudcast.play_count)} plays")
    
    if cloudcast.favorite_count:
        parts.append(f"❤️ {format_number(cloudcast.favorite_count)} likes")
    
    # Add tags
    if cloudcast.tags:
        tags = ", ".join([tag.name for tag in cloudcast.tags[:3]])
        parts.append(f"🏷 {tags}")
    
    return "\n".join(parts)


def format_user_info(user: Any) -> str:
    """
    Format user information for display.
    
    Args:
        user: User object
        
    Returns:
        Formatted user info string
    """
    parts = []
    
    # Add name and username
    parts.append(f"👤 {user.display_name} (@{user.username})")
    
    # Add location
    if user.location:
        parts.append(f"📍 {user.location}")
    
    # Add stats
    stats = []
    if user.follower_count:
        stats.append(f"{format_number(user.follower_count)} followers")
    if user.cloudcast_count:
        stats.append(f"{format_number(user.cloudcast_count)} shows")
    
    if stats:
        parts.append(f"📊 {' • '.join(stats)}")
    
    # Add bio
    if user.biog:
        bio = truncate_text(user.biog, 150)
        parts.append(f"📝 {bio}")
    
    return "\n".join(parts)


def format_search_result(result: Any, result_type: str = "cloudcast") -> str:
    """
    Format search result for display.
    
    Args:
        result: Search result object
        result_type: Type of result
        
    Returns:
        Formatted result string
    """
    if result_type == "cloudcast":
        return format_cloudcast_info(result)
    elif result_type == "user":
        return format_user_info(result)
    elif result_type == "tag":
        return f"🏷 {result.name} ({format_number(result.cloudcast_count)} cloudcasts)"
    else:
        return str(result)


__all__ = [
    "format_duration",
    "format_date",
    "format_relative_time",
    "format_number",
    "format_file_size",
    "format_bitrate",
    "format_percentage",
    "truncate_text",
    "format_cloudcast_info",
    "format_user_info",
    "format_search_result",
]