"""
Utility functions for Bandcamp integration.
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


def is_bandcamp_url(url: str) -> bool:
    """
    Check if URL is a Bandcamp URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if Bandcamp URL
    """
    try:
        parsed = urlparse(url)
        # Check for standard bandcamp.com URLs
        if "bandcamp.com" in parsed.netloc:
            return True
        
        # Check for custom Bandcamp-powered domains
        # These are domains that use Bandcamp's platform but have custom URLs
        custom_bandcamp_domains = [
            "music.monstercat.com",
            "billwurtz.com",
            # Add more known custom domains as needed
        ]
        
        for domain in custom_bandcamp_domains:
            if domain in parsed.netloc:
                return True
        
        # Check if the page has Bandcamp structure
        # This is a fallback for unknown custom domains
        # We'll validate this in the scraper
        if "/album/" in parsed.path or "/track/" in parsed.path:
            return True
            
        return False
    except:
        return False


def parse_bandcamp_url(url: str) -> Tuple[str, str, str]:
    """
    Parse Bandcamp URL and extract type and identifiers.
    
    Args:
        url: Bandcamp URL
        
    Returns:
        Tuple of (type, artist, item) where:
        - type: "album", "track", or "artist"
        - artist: Artist/band subdomain or name
        - item: Album/track name or empty for artist page
    """
    if not is_bandcamp_url(url):
        raise ValueError(f"Not a Bandcamp URL: {url}")
    
    parsed = urlparse(url)
    
    # Extract artist from subdomain or custom domain
    artist = ""
    if ".bandcamp.com" in parsed.netloc:
        artist = parsed.netloc.split(".bandcamp.com")[0]
    else:
        # For custom domains, use the domain as artist identifier
        artist = parsed.netloc.replace("www.", "").replace("music.", "")
    
    # Determine type from path
    path = parsed.path.strip("/")
    
    if not path:
        return ("artist", artist, "")
    elif path.startswith("album/") or "/album/" in path:
        album_name = path.split("album/")[-1]
        return ("album", artist, album_name)
    elif path.startswith("track/") or "/track/" in path:
        track_name = path.split("track/")[-1]
        return ("track", artist, track_name)
    else:
        # Could be a custom domain artist page
        return ("artist", artist, "")


def get_bandcamp_url(artist: str, item_type: str = "artist", item_name: str = "") -> str:
    """
    Build a Bandcamp URL.
    
    Args:
        artist: Artist/band name
        item_type: Type of item ("artist", "album", "track")
        item_name: Name of album/track (if applicable)
        
    Returns:
        Bandcamp URL
    """
    base_url = f"https://{artist}.bandcamp.com"
    
    if item_type == "album" and item_name:
        return f"{base_url}/album/{item_name}"
    elif item_type == "track" and item_name:
        return f"{base_url}/track/{item_name}"
    else:
        return base_url


def sanitize_for_url(text: str) -> str:
    """
    Sanitize text for use in URLs.
    
    Args:
        text: Text to sanitize
        
    Returns:
        URL-safe text
    """
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Convert to lowercase
    text = text.lower().strip('-')
    
    return text


def extract_json_from_html(html: str, pattern: str) -> Optional[dict]:
    """
    Extract JSON data from HTML using regex pattern.
    
    Args:
        html: HTML content
        pattern: Regex pattern to find JSON
        
    Returns:
        Parsed JSON dict or None
    """
    import json
    
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return None
    
    try:
        json_str = match.group(1)
        # Clean up common issues
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Quote keys
        json_str = json_str.replace("'", '"')  # Single to double quotes
        
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        return None


def format_duration(seconds: Optional[int]) -> str:
    """
    Format duration in seconds to string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration (MM:SS or HH:MM:SS)
    """
    if not seconds:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_price(price: Optional[float], currency: Optional[str] = None) -> str:
    """
    Format price with currency.
    
    Args:
        price: Price value
        currency: Currency code
        
    Returns:
        Formatted price string
    """
    if price is None:
        return "Free"
    
    if price == 0:
        return "Free / Name Your Price"
    
    # Currency symbols
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "CAD": "CA$",
        "AUD": "AU$",
        "JPY": "¥",
    }
    
    symbol = symbols.get(currency, currency or "$")
    return f"{symbol}{price:.2f}"


__all__ = [
    "is_bandcamp_url",
    "parse_bandcamp_url",
    "get_bandcamp_url",
    "sanitize_for_url",
    "extract_json_from_html",
    "format_duration",
    "format_price",
]