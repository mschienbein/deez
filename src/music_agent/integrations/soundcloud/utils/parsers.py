"""
Parsing utilities for SoundCloud data.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs


def parse_url(url: str) -> Dict[str, Optional[str]]:
    """
    Parse SoundCloud URL to extract components.
    
    Args:
        url: SoundCloud URL
        
    Returns:
        Dictionary with URL components
    """
    result = {
        "type": None,
        "username": None,
        "resource": None,
        "resource_id": None,
    }
    
    if not url:
        return result
    
    try:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        if not path:
            return result
        
        parts = path.split("/")
        
        # API URL format: /tracks/123, /users/456, etc.
        if parts[0] in ["tracks", "users", "playlists"]:
            result["type"] = parts[0].rstrip("s")  # Remove plural
            if len(parts) > 1 and parts[1].isdigit():
                result["resource_id"] = parts[1]
        
        # Public URL format: /username/track or /username/sets/playlist
        elif len(parts) >= 1:
            result["username"] = parts[0]
            
            if len(parts) == 2:
                if parts[1] != "sets":
                    result["type"] = "track"
                    result["resource"] = parts[1]
            elif len(parts) >= 3 and parts[1] == "sets":
                result["type"] = "playlist"
                result["resource"] = parts[2]
            elif len(parts) == 1:
                result["type"] = "user"
        
        return result
        
    except Exception:
        return result


def extract_id_from_url(url: str) -> Optional[int]:
    """
    Extract numeric ID from SoundCloud API URL.
    
    Args:
        url: SoundCloud API URL
        
    Returns:
        Resource ID or None
    """
    if not url:
        return None
    
    # Look for pattern like /tracks/123, /users/456
    match = re.search(r"/(tracks|users|playlists)/(\d+)", url)
    if match:
        return int(match.group(2))
    
    return None


def parse_tags(tag_string: str) -> List[str]:
    """
    Parse tag string into list of tags.
    
    Args:
        tag_string: Space-separated or quoted tags
        
    Returns:
        List of tags
    """
    if not tag_string:
        return []
    
    tags = []
    
    # Handle quoted tags first
    quoted = re.findall(r'"([^"]+)"', tag_string)
    tags.extend(quoted)
    
    # Remove quoted parts
    for quote in quoted:
        tag_string = tag_string.replace(f'"{quote}"', "")
    
    # Split remaining by spaces
    remaining = tag_string.split()
    tags.extend(remaining)
    
    # Clean and deduplicate
    tags = [tag.strip() for tag in tags if tag.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_tags.append(tag)
    
    return unique_tags


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse duration string to milliseconds.
    
    Args:
        duration_str: Duration string (e.g., "3:45", "1:23:45")
        
    Returns:
        Duration in milliseconds or None
    """
    if not duration_str:
        return None
    
    try:
        parts = duration_str.split(":")
        
        if len(parts) == 1:
            # Just seconds
            seconds = float(parts[0])
        elif len(parts) == 2:
            # MM:SS
            minutes = int(parts[0])
            seconds = float(parts[1])
            seconds += minutes * 60
        elif len(parts) == 3:
            # HH:MM:SS
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            seconds += (hours * 3600) + (minutes * 60)
        else:
            return None
        
        return int(seconds * 1000)
        
    except (ValueError, TypeError):
        return None


def parse_timestamp(timestamp_str: str) -> Optional[int]:
    """
    Parse timestamp comment format to milliseconds.
    
    Args:
        timestamp_str: Timestamp (e.g., "@1:23", "at 2:45")
        
    Returns:
        Timestamp in milliseconds or None
    """
    if not timestamp_str:
        return None
    
    # Look for time pattern
    match = re.search(r"(?:@|at\s+)?(\d+):(\d+)(?::(\d+))?", timestamp_str)
    if match:
        if match.group(3):  # HH:MM:SS
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            total_seconds = (hours * 3600) + (minutes * 60) + seconds
        else:  # MM:SS
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            total_seconds = (minutes * 60) + seconds
        
        return total_seconds * 1000
    
    return None


def parse_api_error(error_response: Dict[str, Any]) -> Tuple[int, str]:
    """
    Parse API error response.
    
    Args:
        error_response: Error response from API
        
    Returns:
        Tuple of (error code, error message)
    """
    code = 0
    message = "Unknown error"
    
    if not error_response:
        return code, message
    
    # Check for error fields
    if "errors" in error_response:
        errors = error_response["errors"]
        if isinstance(errors, list) and errors:
            error = errors[0]
            if isinstance(error, dict):
                code = error.get("error_code", 0)
                message = error.get("error_message", message)
    elif "error" in error_response:
        error = error_response["error"]
        if isinstance(error, dict):
            code = error.get("code", 0)
            message = error.get("message", message)
        else:
            message = str(error)
    elif "error_message" in error_response:
        message = error_response["error_message"]
    
    return code, message


def parse_search_query(query: str) -> Dict[str, Any]:
    """
    Parse advanced search query.
    
    Args:
        query: Search query with potential operators
        
    Returns:
        Parsed query components
    """
    result = {
        "query": "",
        "filters": {},
        "exclude": [],
    }
    
    if not query:
        return result
    
    # Extract quoted phrases
    phrases = re.findall(r'"([^"]+)"', query)
    
    # Remove quoted parts temporarily
    temp_query = query
    for phrase in phrases:
        temp_query = temp_query.replace(f'"{phrase}"', "")
    
    # Parse operators
    words = temp_query.split()
    query_words = []
    
    for word in words:
        if ":" in word:
            # Operator format (genre:electronic)
            key, value = word.split(":", 1)
            if key in ["genre", "tag", "user", "license", "bpm"]:
                result["filters"][key] = value
        elif word.startswith("-"):
            # Exclusion
            result["exclude"].append(word[1:])
        elif word.startswith("#"):
            # Hashtag
            if "tags" not in result["filters"]:
                result["filters"]["tags"] = []
            result["filters"]["tags"].append(word[1:])
        else:
            query_words.append(word)
    
    # Rebuild query with phrases
    result["query"] = " ".join(query_words + phrases)
    
    return result


def parse_m3u(content: str) -> List[Dict[str, Any]]:
    """
    Parse M3U playlist content.
    
    Args:
        content: M3U file content
        
    Returns:
        List of playlist entries
    """
    entries = []
    lines = content.strip().split("\n")
    
    current_entry = {}
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("#EXTINF:"):
            # Parse extended info
            match = re.match(r"#EXTINF:([\d\-]+),(.+)", line)
            if match:
                current_entry = {
                    "duration": int(match.group(1)),
                    "title": match.group(2),
                }
        elif line.startswith("#PLAYLIST:"):
            # Playlist name (ignore for entries)
            pass
        elif line.startswith("#"):
            # Other comment (ignore)
            pass
        elif line:
            # This is the URL/filename
            if current_entry:
                current_entry["url"] = line
                entries.append(current_entry)
                current_entry = {}
            else:
                # Simple entry without extended info
                entries.append({"url": line})
    
    return entries


def parse_client_id_from_js(javascript: str) -> Optional[str]:
    """
    Parse client ID from JavaScript code.
    
    Args:
        javascript: JavaScript code
        
    Returns:
        Client ID or None
    """
    if not javascript:
        return None
    
    # Various patterns used in SoundCloud's JS
    patterns = [
        r'client_id["\']?\s*:\s*["\']([a-zA-Z0-9]+)["\']',
        r'client_id=([a-zA-Z0-9]+)',
        r'"clientId":"([a-zA-Z0-9]+)"',
        r'clientId\s*:\s*"([a-zA-Z0-9]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, javascript)
        if match:
            client_id = match.group(1)
            # Validate it looks like a client ID
            if len(client_id) == 32 and client_id.isalnum():
                return client_id
    
    return None


__all__ = [
    "parse_url",
    "extract_id_from_url",
    "parse_tags",
    "parse_duration",
    "parse_timestamp",
    "parse_api_error",
    "parse_search_query",
    "parse_m3u",
    "parse_client_id_from_js",
]