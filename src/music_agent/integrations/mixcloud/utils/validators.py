"""
Validation utilities for Mixcloud integration.

Provides functions for validating data and URLs.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def is_mixcloud_url(url: str) -> bool:
    """
    Check if URL is a valid Mixcloud URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if valid Mixcloud URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc in ["mixcloud.com", "www.mixcloud.com", "m.mixcloud.com"]
    except:
        return False


def parse_mixcloud_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Parse Mixcloud URL and extract username and cloudcast slug.
    
    Args:
        url: Mixcloud URL
        
    Returns:
        Tuple of (username, cloudcast_slug) or None
    """
    if not is_mixcloud_url(url):
        return None
    
    # Pattern for cloudcast URL
    pattern = r"mixcloud\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    
    if match:
        username = match.group(1)
        cloudcast_slug = match.group(2).rstrip("/")
        return (username, cloudcast_slug)
    
    return None


def parse_user_url(url: str) -> Optional[str]:
    """
    Parse Mixcloud user URL and extract username.
    
    Args:
        url: Mixcloud user URL
        
    Returns:
        Username or None
    """
    if not is_mixcloud_url(url):
        return None
    
    # Pattern for user URL
    pattern = r"mixcloud\.com/([^/]+)/?$"
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)
    
    return None


def validate_username(username: str) -> bool:
    """
    Validate Mixcloud username.
    
    Args:
        username: Username to validate
        
    Returns:
        True if valid username
    """
    if not username:
        return False
    
    # Username should be alphanumeric with underscores/hyphens
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, username))


def validate_cloudcast_slug(slug: str) -> bool:
    """
    Validate cloudcast slug.
    
    Args:
        slug: Cloudcast slug to validate
        
    Returns:
        True if valid slug
    """
    if not slug:
        return False
    
    # Slug should be URL-safe
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, slug))


def validate_tag_name(tag: str) -> bool:
    """
    Validate tag name.
    
    Args:
        tag: Tag name to validate
        
    Returns:
        True if valid tag name
    """
    if not tag:
        return False
    
    # Tag should be alphanumeric with spaces/hyphens
    pattern = r"^[a-zA-Z0-9\s-]+$"
    return bool(re.match(pattern, tag))


def validate_email(email: str) -> bool:
    """
    Validate email address.
    
    Args:
        email: Email to validate
        
    Returns:
        True if valid email
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_duration(duration: int) -> bool:
    """
    Validate duration value.
    
    Args:
        duration: Duration in seconds
        
    Returns:
        True if valid duration
    """
    # Duration should be positive and reasonable (< 24 hours)
    return 0 < duration < 86400


def validate_file_path(path: str) -> bool:
    """
    Validate file path.
    
    Args:
        path: File path to validate
        
    Returns:
        True if valid path
    """
    if not path:
        return False
    
    # Check for invalid characters
    invalid_chars = '<>"|?*'
    for char in invalid_chars:
        if char in path:
            return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for filesystem.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    # Remove control characters
    filename = "".join(char for char in filename if ord(char) >= 32)
    
    # Limit length
    max_length = 200
    if len(filename) > max_length:
        # Keep extension if present
        parts = filename.rsplit(".", 1)
        if len(parts) == 2:
            name, ext = parts
            max_name_length = max_length - len(ext) - 1
            filename = f"{name[:max_name_length]}.{ext}"
        else:
            filename = filename[:max_length]
    
    return filename.strip()


def validate_api_response(response: dict) -> bool:
    """
    Validate API response structure.
    
    Args:
        response: API response dictionary
        
    Returns:
        True if valid response
    """
    if not isinstance(response, dict):
        return False
    
    # Check for error indicators
    if "error" in response:
        return False
    
    if response.get("status") == "error":
        return False
    
    return True


def validate_stream_url(url: str) -> bool:
    """
    Validate stream URL.
    
    Args:
        url: Stream URL to validate
        
    Returns:
        True if valid stream URL
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # Check for HTTP(S) protocol
        if parsed.scheme not in ["http", "https"]:
            return False
        
        # Check for valid netloc
        if not parsed.netloc:
            return False
        
        # Check for common stream patterns
        stream_patterns = [
            r"\.m3u8",  # HLS
            r"\.mp3",   # MP3
            r"\.m4a",   # M4A
            r"/stream",  # Stream endpoint
            r"/audio",   # Audio endpoint
        ]
        
        for pattern in stream_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Allow any HTTPS URL as potential stream
        return parsed.scheme == "https"
        
    except:
        return False


def validate_oauth_state(state: str) -> bool:
    """
    Validate OAuth state parameter.
    
    Args:
        state: OAuth state parameter
        
    Returns:
        True if valid state
    """
    if not state:
        return False
    
    # State should be alphanumeric (base64url)
    pattern = r"^[a-zA-Z0-9_-]+$"
    return bool(re.match(pattern, state))


__all__ = [
    "is_mixcloud_url",
    "parse_mixcloud_url",
    "parse_user_url",
    "validate_username",
    "validate_cloudcast_slug",
    "validate_tag_name",
    "validate_email",
    "validate_duration",
    "validate_file_path",
    "sanitize_filename",
    "validate_api_response",
    "validate_stream_url",
    "validate_oauth_state",
]