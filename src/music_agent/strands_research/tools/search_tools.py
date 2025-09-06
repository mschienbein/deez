"""
Search tools for various music platforms.

These tools are used by data collector agents to search for track metadata.
"""

from typing import Dict, Any, Optional, List
from strands import tool
import asyncio
import hashlib
from datetime import datetime, timedelta


# Simple in-memory cache for demo
_cache: Dict[str, Dict[str, Any]] = {}


def _get_cache_key(platform: str, query: str) -> str:
    """Generate cache key."""
    return hashlib.md5(f"{platform}:{query}".encode()).hexdigest()


def _check_cache(platform: str, query: str, ttl_seconds: int = 3600) -> Optional[Dict[str, Any]]:
    """Check if result is in cache and still valid."""
    key = _get_cache_key(platform, query)
    if key in _cache:
        cached = _cache[key]
        if datetime.utcnow() < cached['expires']:
            return cached['data']
        else:
            del _cache[key]
    return None


def _cache_result(platform: str, query: str, result: Dict[str, Any], ttl_seconds: int = 3600):
    """Cache search result."""
    key = _get_cache_key(platform, query)
    _cache[key] = {
        'data': result,
        'expires': datetime.utcnow() + timedelta(seconds=ttl_seconds)
    }


@tool
async def search_spotify(
    query: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Search Spotify for track metadata.
    
    Args:
        query: Search query in "artist - title" format
        use_cache: Whether to use cached results
    
    Returns:
        Track metadata from Spotify including audio features
    """
    if use_cache:
        cached = _check_cache("spotify", query)
        if cached:
            return cached
    
    # Simulate API delay
    await asyncio.sleep(0.5)
    
    # Mock response - in production would use actual Spotify API
    result = {
        "platform": "spotify",
        "success": True,
        "tracks": [{
            "title": "Strobe",
            "artist": "deadmau5",
            "album": "For Lack of a Better Name",
            "duration_ms": 634000,
            "isrc": "USUS11000356",
            "spotify_id": "3Oa0j5wSr3Z3BmP8Qzqjyj",
            "popularity": 65,
            "preview_url": "https://p.scdn.co/preview/...",
            "external_urls": {
                "spotify": "https://open.spotify.com/track/3Oa0j5wSr3Z3BmP8Qzqjyj"
            },
            "audio_features": {
                "energy": 0.72,
                "danceability": 0.68,
                "valence": 0.42,
                "acousticness": 0.12,
                "instrumentalness": 0.89,
                "speechiness": 0.03,
                "liveness": 0.11
            }
        }],
        "confidence": 0.9
    }
    
    _cache_result("spotify", query, result)
    return result


@tool
async def search_beatport(
    query: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Search Beatport for electronic music metadata.
    
    Beatport specializes in electronic music and provides
    DJ-relevant metadata like BPM, key, and genre classification.
    
    Args:
        query: Search query
        use_cache: Whether to use cached results
    
    Returns:
        Track metadata from Beatport with DJ-specific fields
    """
    if use_cache:
        cached = _check_cache("beatport", query)
        if cached:
            return cached
    
    await asyncio.sleep(0.5)
    
    result = {
        "platform": "beatport",
        "success": True,
        "tracks": [{
            "title": "Strobe",
            "artist": "deadmau5",
            "mix": "Original Mix",
            "bpm": 128.0,
            "key": "C# min",
            "genre": "Progressive House",
            "sub_genre": "Melodic House",
            "label": "mau5trap",
            "release_date": "2009-10-06",
            "beatport_id": 1234567,
            "price": 2.49,
            "length": "10:34",
            "waveform_url": "https://geo-media.beatport.com/...",
            "preview": "https://geo-samples.beatport.com/..."
        }],
        "confidence": 0.95
    }
    
    _cache_result("beatport", query, result)
    return result


@tool
async def search_discogs(
    query: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Search Discogs for detailed release information.
    
    Discogs provides comprehensive discography data including
    pressing details, catalog numbers, and marketplace info.
    
    Args:
        query: Search query
        use_cache: Whether to use cached results
    
    Returns:
        Release metadata from Discogs
    """
    if use_cache:
        cached = _check_cache("discogs", query)
        if cached:
            return cached
    
    await asyncio.sleep(0.5)
    
    result = {
        "platform": "discogs",
        "success": True,
        "results": [{
            "title": "For Lack Of A Better Name",
            "artist": "Deadmau5",
            "type": "release",
            "year": 2009,
            "label": ["Ultra Records", "mau5trap"],
            "catalog_number": "UL 2339",
            "format": ["CD", "Album"],
            "genre": ["Electronic"],
            "style": ["Progressive House", "Electro House"],
            "tracklist": [
                {"position": "10", "title": "Strobe", "duration": "10:37"}
            ],
            "discogs_id": "r2034567",
            "marketplace": {
                "lowest_price": 8.99,
                "num_for_sale": 42,
                "median_price": 15.00
            }
        }],
        "confidence": 0.9
    }
    
    _cache_result("discogs", query, result)
    return result


@tool
async def search_deezer(
    query: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Search Deezer for track metadata.
    
    Args:
        query: Search query
        use_cache: Whether to use cached results
    
    Returns:
        Track metadata from Deezer
    """
    if use_cache:
        cached = _check_cache("deezer", query)
        if cached:
            return cached
    
    await asyncio.sleep(0.5)
    
    result = {
        "platform": "deezer",
        "success": True,
        "tracks": [{
            "title": "Strobe",
            "artist": "deadmau5",
            "album": "For Lack of a Better Name",
            "duration": 634,
            "isrc": "USUS11000356",
            "bpm": 128,
            "deezer_id": 12345678,
            "preview": "https://cdns-preview-d.dzcdn.net/...",
            "link": "https://www.deezer.com/track/12345678"
        }],
        "confidence": 0.85
    }
    
    _cache_result("deezer", query, result)
    return result


@tool
async def search_musicbrainz(
    query: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Search MusicBrainz for authoritative music metadata.
    
    MusicBrainz is an open music encyclopedia that provides
    detailed metadata including ISRCs, relationships, and credits.
    
    Args:
        query: Search query
        use_cache: Whether to use cached results
    
    Returns:
        Track metadata from MusicBrainz
    """
    if use_cache:
        cached = _check_cache("musicbrainz", query)
        if cached:
            return cached
    
    await asyncio.sleep(0.5)
    
    result = {
        "platform": "musicbrainz",
        "success": True,
        "recordings": [{
            "title": "Strobe",
            "artist": "deadmau5",
            "length": 634000,
            "isrc": ["USUS11000356"],
            "recording_id": "8f3471b5-7e6a-48da-86a9-c1c7680b2ed5",
            "release": {
                "title": "For Lack of a Better Name",
                "date": "2009-10-06",
                "label": "Ultra Records",
                "catalog_number": "UL 2339"
            },
            "credits": {
                "producer": ["Joel Zimmerman"],
                "composer": ["Joel Zimmerman"],
                "engineer": ["Joel Zimmerman"]
            }
        }],
        "confidence": 0.85
    }
    
    _cache_result("musicbrainz", query, result)
    return result


@tool
async def search_soundcloud(
    query: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Search SoundCloud for tracks.
    
    SoundCloud often has remixes, bootlegs, and unreleased tracks
    not available on other platforms.
    
    Args:
        query: Search query
        use_cache: Whether to use cached results
    
    Returns:
        Track metadata from SoundCloud
    """
    if use_cache:
        cached = _check_cache("soundcloud", query)
        if cached:
            return cached
    
    await asyncio.sleep(0.5)
    
    result = {
        "platform": "soundcloud",
        "success": True,
        "tracks": [{
            "title": "Strobe (Radio Edit)",
            "artist": "deadmau5",
            "duration": 377000,
            "genre": "Progressive House",
            "tags": ["progressive", "house", "deadmau5", "electronic"],
            "soundcloud_id": 123456789,
            "stream_url": "https://api.soundcloud.com/tracks/123456789/stream",
            "waveform_url": "https://w1.sndcdn.com/...",
            "plays_count": 5234567,
            "likes_count": 123456
        }],
        "confidence": 0.7
    }
    
    _cache_result("soundcloud", query, result)
    return result