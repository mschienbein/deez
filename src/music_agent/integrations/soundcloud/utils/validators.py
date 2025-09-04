"""
Validation utilities for SoundCloud data.
"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """
    Validate if URL is a valid SoundCloud URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid SoundCloud URL
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url)
        
        # Check if it's a SoundCloud domain
        valid_domains = [
            "soundcloud.com",
            "www.soundcloud.com",
            "m.soundcloud.com",
            "api.soundcloud.com",
            "api-v2.soundcloud.com",
        ]
        
        return parsed.netloc in valid_domains
        
    except Exception:
        return False


def validate_track_id(track_id: any) -> bool:
    """
    Validate track ID.
    
    Args:
        track_id: Track ID to validate
        
    Returns:
        True if valid track ID
    """
    if track_id is None:
        return False
    
    # Track ID should be a positive integer
    try:
        id_int = int(track_id)
        return id_int > 0
    except (ValueError, TypeError):
        return False


def validate_client_id(client_id: str) -> bool:
    """
    Validate SoundCloud client ID format.
    
    Args:
        client_id: Client ID to validate
        
    Returns:
        True if valid client ID format
    """
    if not client_id or not isinstance(client_id, str):
        return False
    
    # Client ID should be 32 characters, alphanumeric
    pattern = r"^[a-zA-Z0-9]{32}$"
    return bool(re.match(pattern, client_id))


def validate_oauth_token(token: str) -> bool:
    """
    Validate OAuth token format.
    
    Args:
        token: OAuth token to validate
        
    Returns:
        True if valid token format
    """
    if not token or not isinstance(token, str):
        return False
    
    # OAuth tokens are typically in format: x-xxxxxx-xxxxxxxxx-xxxxxxxxxxxxx
    # But can vary, so just check basic format
    pattern = r"^[\w\-]+$"
    return bool(re.match(pattern, token)) and len(token) >= 20


def validate_username(username: str) -> bool:
    """
    Validate SoundCloud username.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid username
    """
    if not username or not isinstance(username, str):
        return False
    
    # Username rules:
    # - 3-25 characters
    # - Alphanumeric, underscores, hyphens
    # - Cannot start/end with hyphen or underscore
    if len(username) < 3 or len(username) > 25:
        return False
    
    pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_\-]*[a-zA-Z0-9]$"
    return bool(re.match(pattern, username))


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email to validate
        
    Returns:
        True if valid email format
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email validation
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_genre(genre: str) -> bool:
    """
    Validate genre name.
    
    Args:
        genre: Genre to validate
        
    Returns:
        True if valid genre
    """
    if not genre or not isinstance(genre, str):
        return False
    
    # Genre should be reasonable length and contain valid characters
    if len(genre) < 2 or len(genre) > 50:
        return False
    
    # Allow letters, numbers, spaces, &, -, /
    pattern = r"^[a-zA-Z0-9\s&\-/]+$"
    return bool(re.match(pattern, genre))


def validate_duration(duration: any) -> bool:
    """
    Validate duration value.
    
    Args:
        duration: Duration in milliseconds
        
    Returns:
        True if valid duration
    """
    try:
        duration_int = int(duration)
        # Duration should be positive and reasonable (< 24 hours)
        return 0 < duration_int < 86400000
    except (ValueError, TypeError):
        return False


def validate_bpm(bpm: any) -> bool:
    """
    Validate BPM value.
    
    Args:
        bpm: BPM value
        
    Returns:
        True if valid BPM
    """
    try:
        bpm_float = float(bpm)
        # BPM should be in reasonable range
        return 20 <= bpm_float <= 300
    except (ValueError, TypeError):
        return False


def validate_license(license: str) -> bool:
    """
    Validate license type.
    
    Args:
        license: License type
        
    Returns:
        True if valid license
    """
    if not license or not isinstance(license, str):
        return False
    
    valid_licenses = [
        "all-rights-reserved",
        "cc-by",
        "cc-by-sa",
        "cc-by-nc",
        "cc-by-nc-sa",
        "cc-by-nc-nd",
        "cc-by-nd",
        "cc0",
        "no-rights-reserved",
    ]
    
    return license.lower() in valid_licenses


def validate_file_format(filename: str, allowed_formats: Optional[list] = None) -> bool:
    """
    Validate file format by extension.
    
    Args:
        filename: Filename to validate
        allowed_formats: List of allowed extensions
        
    Returns:
        True if valid format
    """
    if not filename or not isinstance(filename, str):
        return False
    
    if allowed_formats is None:
        # Default audio formats
        allowed_formats = [
            ".mp3", ".m4a", ".ogg", ".opus",
            ".wav", ".flac", ".aiff", ".aac"
        ]
    
    # Get file extension
    import os
    _, ext = os.path.splitext(filename.lower())
    
    return ext in allowed_formats


def validate_api_response(response: dict) -> bool:
    """
    Validate API response structure.
    
    Args:
        response: API response dict
        
    Returns:
        True if valid response
    """
    if not response or not isinstance(response, dict):
        return False
    
    # Check for error indicators
    if "errors" in response or "error" in response:
        return False
    
    # Response should have some content
    return len(response) > 0


__all__ = [
    "validate_url",
    "validate_track_id",
    "validate_client_id",
    "validate_oauth_token",
    "validate_username",
    "validate_email",
    "validate_genre",
    "validate_duration",
    "validate_bpm",
    "validate_license",
    "validate_file_format",
    "validate_api_response",
]