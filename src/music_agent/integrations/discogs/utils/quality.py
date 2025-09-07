"""
Quality estimation utilities for Discogs data.
"""

from typing import Optional


def estimate_track_quality(
    format: str,
    year: Optional[int] = None
) -> int:
    """
    Estimate quality score based on format and year.
    
    Args:
        format: Release format
        year: Release year
        
    Returns:
        Quality score (0-100)
    """
    format_lower = format.lower()
    
    # Base scores by format
    if any(f in format_lower for f in ['flac', 'wav', 'aiff']):
        score = 90
    elif 'vinyl' in format_lower or '12"' in format_lower:
        score = 85
    elif 'cd' in format_lower:
        score = 80
    elif any(f in format_lower for f in ['320', 'mp3']):
        score = 75
    elif 'digital' in format_lower or 'file' in format_lower:
        score = 70
    elif 'cassette' in format_lower:
        score = 50
    else:
        score = 60
    
    # Adjust for age (older digital formats likely lower quality)
    if year and year < 2000 and 'digital' in format_lower:
        score -= 10
    elif year and year < 1990:
        score -= 5
    
    return max(0, min(100, score))