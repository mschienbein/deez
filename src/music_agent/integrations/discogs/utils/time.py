"""
Time and duration utilities for Discogs data.
"""

from typing import Optional


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to MM:SS or HH:MM:SS.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return ""
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse duration string to seconds.
    
    Args:
        duration_str: Duration as string (MM:SS or HH:MM:SS)
        
    Returns:
        Duration in seconds or None if invalid
    """
    if not duration_str:
        return None
    
    try:
        parts = duration_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, AttributeError):
        pass
    
    return None