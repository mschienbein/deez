"""
Formatting utilities for SoundCloud data.
"""

import re
from datetime import datetime
from typing import Optional, Union


def format_duration(milliseconds: int) -> str:
    """
    Format duration from milliseconds to human-readable string.
    
    Args:
        milliseconds: Duration in milliseconds
        
    Returns:
        Formatted duration (HH:MM:SS or MM:SS)
    """
    if milliseconds <= 0:
        return "0:00"
    
    total_seconds = milliseconds // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"


def format_date(date: Optional[Union[datetime, str]]) -> str:
    """
    Format date to human-readable string.
    
    Args:
        date: Date as datetime or ISO string
        
    Returns:
        Formatted date string
    """
    if not date:
        return "Unknown"
    
    if isinstance(date, str):
        try:
            # Parse ISO format
            if "T" in date:
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            else:
                date = datetime.strptime(date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return date
    
    if isinstance(date, datetime):
        # Format as relative time if recent
        now = datetime.now(date.tzinfo)
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            return date.strftime("%Y-%m-%d")
    
    return str(date)


def format_number(number: int, short: bool = False) -> str:
    """
    Format large numbers for display.
    
    Args:
        number: Number to format
        short: Use short format (1.2K instead of 1,234)
        
    Returns:
        Formatted number string
    """
    if number < 0:
        return str(number)
    
    if short:
        if number >= 1000000:
            return f"{number / 1000000:.1f}M"
        elif number >= 1000:
            return f"{number / 1000:.1f}K"
    
    # Add thousands separator
    return f"{number:,}"


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Sanitize string for use as filename.
    
    Args:
        name: String to sanitize
        max_length: Maximum length
        
    Returns:
        Sanitized filename
    """
    if not name:
        return "Unknown"
    
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    
    # Remove control characters
    name = "".join(c for c in name if ord(c) >= 32)
    
    # Remove leading/trailing spaces and dots
    name = name.strip(". ")
    
    # Limit length
    if len(name) > max_length:
        # Keep extension if present
        parts = name.rsplit(".", 1)
        if len(parts) == 2 and len(parts[1]) <= 4:
            base_max = max_length - len(parts[1]) - 1
            name = f"{parts[0][:base_max]}.{parts[1]}"
        else:
            name = name[:max_length]
    
    # Ensure non-empty
    if not name:
        name = "Unknown"
    
    return name


def format_filesize(bytes: int) -> str:
    """
    Format file size to human-readable string.
    
    Args:
        bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if bytes < 0:
        return "Unknown"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes)
    unit_idx = 0
    
    while size >= 1024 and unit_idx < len(units) - 1:
        size /= 1024
        unit_idx += 1
    
    if unit_idx == 0:
        return f"{int(size)} {units[unit_idx]}"
    else:
        return f"{size:.2f} {units[unit_idx]}"


def format_bitrate(bitrate: int) -> str:
    """
    Format bitrate to human-readable string.
    
    Args:
        bitrate: Bitrate in bits per second
        
    Returns:
        Formatted bitrate string
    """
    if bitrate < 0:
        return "Unknown"
    
    kbps = bitrate / 1000
    
    if kbps >= 1000:
        return f"{kbps / 1000:.1f} Mbps"
    else:
        return f"{int(kbps)} kbps"


def format_percentage(value: float, total: float) -> str:
    """
    Format percentage value.
    
    Args:
        value: Current value
        total: Total value
        
    Returns:
        Formatted percentage string
    """
    if total <= 0:
        return "0%"
    
    percentage = (value / total) * 100
    
    if percentage < 1:
        return f"{percentage:.2f}%"
    else:
        return f"{percentage:.1f}%"


def clean_html(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text with potential HTML
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    
    # Decode HTML entities
    import html
    clean = html.unescape(clean)
    
    # Remove extra whitespace
    clean = " ".join(clean.split())
    
    return clean


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Account for suffix length
    max_length -= len(suffix)
    
    # Try to break at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    
    if last_space > max_length * 0.8:  # If space is reasonably close
        truncated = truncated[:last_space]
    
    return truncated + suffix


__all__ = [
    "format_duration",
    "format_date",
    "format_number",
    "sanitize_filename",
    "format_filesize",
    "format_bitrate",
    "format_percentage",
    "clean_html",
    "truncate_text",
]