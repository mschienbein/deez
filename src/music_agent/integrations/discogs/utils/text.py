"""
Text processing utilities for Discogs data.
"""

import re
from typing import Optional, Tuple


def clean_artist_name(name: str) -> str:
    """
    Clean artist name by removing numbering and special characters.
    
    Args:
        name: Raw artist name from Discogs
        
    Returns:
        Cleaned artist name
    """
    # Remove leading numbers like "(2)" from "Artist Name (2)"
    name = re.sub(r'\s*\(\d+\)$', '', name)
    
    # Remove "The" from the beginning for better matching
    if name.startswith("The "):
        name = name[4:]
    
    return name.strip()


def parse_catalog_number(catno: str) -> Tuple[str, str]:
    """
    Parse catalog number into label code and number.
    
    Args:
        catno: Catalog number string
        
    Returns:
        Tuple of (label_code, number)
    """
    if not catno:
        return ("", "")
    
    # Split on common separators
    parts = re.split(r'[-\s]+', catno, 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    return (catno, "")


def extract_year_from_released(released: str) -> Optional[int]:
    """
    Extract year from release date string.
    
    Args:
        released: Release date string (various formats)
        
    Returns:
        Year as integer or None
    """
    if not released:
        return None
    
    # Try to find a 4-digit year
    match = re.search(r'\b(19\d{2}|20\d{2})\b', released)
    if match:
        return int(match.group(1))
    
    return None


def normalize_format(format_str: str) -> str:
    """
    Normalize format string for consistency.
    
    Args:
        format_str: Raw format string
        
    Returns:
        Normalized format string
    """
    format_map = {
        "12\"": "12 inch",
        "7\"": "7 inch",
        "10\"": "10 inch",
        "LP": "LP",
        "EP": "EP",
        "CD": "CD",
        "CDr": "CDr",
        "Cass": "Cassette",
        "File": "Digital",
        "FLAC": "Digital",
        "MP3": "Digital",
        "WAV": "Digital"
    }
    
    for key, value in format_map.items():
        if key.lower() in format_str.lower():
            return value
    
    return format_str


def is_various_artists(artist_name: str) -> bool:
    """
    Check if artist is "Various Artists" or similar.
    
    Args:
        artist_name: Artist name to check
        
    Returns:
        True if various artists compilation
    """
    various_patterns = [
        "various",
        "various artists",
        "v/a",
        "v.a.",
        "compilation",
        "sampler"
    ]
    
    artist_lower = artist_name.lower()
    return any(pattern in artist_lower for pattern in various_patterns)


def extract_remix_info(title: str) -> Tuple[str, Optional[str]]:
    """
    Extract base title and remixer from track title.
    
    Args:
        title: Full track title
        
    Returns:
        Tuple of (base_title, remixer_name)
    """
    # Common remix patterns
    patterns = [
        r'\((.*?)\s+[Rr]emix\)',
        r'\[(.*?)\s+[Rr]emix\]',
        r'-\s*(.*?)\s+[Rr]emix',
        r'\((.*?)\s+[Mm]ix\)',
        r'\[(.*?)\s+[Mm]ix\]',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            remixer = match.group(1).strip()
            base_title = re.sub(pattern, '', title).strip()
            return (base_title, remixer)
    
    return (title, None)