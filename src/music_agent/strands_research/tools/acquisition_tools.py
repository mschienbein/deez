"""
Acquisition tools for finding where to buy, stream, or download tracks.

These tools help locate the best sources for acquiring identified tracks.
"""

from typing import Dict, Any, List, Optional
from strands import tool

from ..models.metadata import TrackQuality, AcquisitionOption


# Platform acquisition capabilities
PLATFORM_CAPABILITIES = {
    "beatport": {
        "type": "purchase",
        "quality": TrackQuality.LOSSLESS,
        "formats": ["WAV", "AIFF", "MP3 320"],
        "typical_price": 2.49,
        "region_restricted": False
    },
    "spotify": {
        "type": "stream",
        "quality": TrackQuality.HIGH,
        "formats": ["OGG 320"],
        "requires_subscription": True,
        "region_restricted": True
    },
    "bandcamp": {
        "type": "purchase",
        "quality": TrackQuality.LOSSLESS,
        "formats": ["FLAC", "WAV", "MP3 V0"],
        "pay_what_you_want": True,
        "region_restricted": False
    },
    "itunes": {
        "type": "purchase",
        "quality": TrackQuality.HIGH,
        "formats": ["AAC 256"],
        "typical_price": 1.29,
        "region_restricted": True
    },
    "amazon": {
        "type": "purchase",
        "quality": TrackQuality.HIGH,
        "formats": ["MP3 320"],
        "typical_price": 1.29,
        "region_restricted": True
    },
    "deezer": {
        "type": "stream",
        "quality": TrackQuality.LOSSLESS,
        "formats": ["FLAC", "MP3 320"],
        "requires_subscription": True,
        "region_restricted": True
    },
    "tidal": {
        "type": "stream",
        "quality": TrackQuality.LOSSLESS,
        "formats": ["FLAC", "MQA"],
        "requires_subscription": True,
        "region_restricted": True
    },
    "soundcloud": {
        "type": "stream",
        "quality": TrackQuality.MEDIUM,
        "formats": ["MP3 128"],
        "free_tier": True,
        "region_restricted": False
    },
    "youtube": {
        "type": "stream",
        "quality": TrackQuality.MEDIUM,
        "formats": ["Various"],
        "free_tier": True,
        "region_restricted": True
    },
    "juno": {
        "type": "purchase",
        "quality": TrackQuality.LOSSLESS,
        "formats": ["WAV", "MP3 320"],
        "typical_price": 1.99,
        "region_restricted": False
    },
    "traxsource": {
        "type": "purchase",
        "quality": TrackQuality.LOSSLESS,
        "formats": ["WAV", "AIFF", "MP3 320"],
        "typical_price": 2.49,
        "region_restricted": False
    }
}


@tool
def find_purchase_options(
    metadata: Dict[str, Any],
    max_price: Optional[float] = None,
    preferred_format: str = "lossless"
) -> List[Dict[str, Any]]:
    """
    Find purchase options for a track.
    
    Searches for places to buy the track in various formats
    and qualities, prioritizing DJ-friendly sources.
    
    Args:
        metadata: Track metadata including IDs from various platforms
        max_price: Maximum price filter (optional)
        preferred_format: Preferred audio format - 'lossless', 'high', or 'any'
    
    Returns:
        List of purchase options sorted by quality and price
    """
    options = []
    
    # Check Beatport (best for electronic music)
    if metadata.get("beatport_id") or "beatport" in metadata.get("sources", []):
        option = AcquisitionOption(
            source="beatport",
            type="purchase",
            quality=TrackQuality.LOSSLESS,
            price=2.49,
            currency="USD",
            url=f"https://www.beatport.com/track/-/{metadata.get('beatport_id', '123')}",
            formats=["WAV", "AIFF", "MP3 320"],
            notes="Best for electronic music, DJ-friendly formats"
        )
        options.append(option)
    
    # Check Bandcamp (good for independent releases)
    if metadata.get("label") and "independent" in metadata.get("label", "").lower():
        option = AcquisitionOption(
            source="bandcamp",
            type="purchase",
            quality=TrackQuality.LOSSLESS,
            price=None,  # Pay what you want
            currency="USD",
            url=f"https://bandcamp.com/search?q={metadata.get('artist')}+{metadata.get('title')}",
            formats=["FLAC", "WAV", "MP3 V0"],
            notes="Support artists directly, pay-what-you-want option"
        )
        options.append(option)
    
    # Check iTunes/Apple Music
    if metadata.get("isrc"):
        option = AcquisitionOption(
            source="itunes",
            type="purchase",
            quality=TrackQuality.HIGH,
            price=1.29,
            currency="USD",
            url=f"https://music.apple.com/search?term={metadata.get('artist')}+{metadata.get('title')}",
            formats=["AAC 256"],
            notes="High-quality AAC format"
        )
        options.append(option)
    
    # Check Juno Download
    if "electronic" in metadata.get("genre", "").lower():
        option = AcquisitionOption(
            source="juno",
            type="purchase",
            quality=TrackQuality.LOSSLESS,
            price=1.99,
            currency="USD",
            url=f"https://www.junodownload.com/search/?q={metadata.get('artist')}+{metadata.get('title')}",
            formats=["WAV", "MP3 320"],
            notes="Good for electronic music"
        )
        options.append(option)
    
    # Check Traxsource
    if any(g in metadata.get("genre", "").lower() for g in ["house", "techno", "electronic"]):
        option = AcquisitionOption(
            source="traxsource",
            type="purchase",
            quality=TrackQuality.LOSSLESS,
            price=2.49,
            currency="USD",
            url=f"https://www.traxsource.com/search?term={metadata.get('artist')}+{metadata.get('title')}",
            formats=["WAV", "AIFF", "MP3 320"],
            notes="Specializes in house and electronic music"
        )
        options.append(option)
    
    # Filter by max price if specified
    if max_price:
        options = [o for o in options if not o.price or o.price <= max_price]
    
    # Filter by preferred format
    if preferred_format == "lossless":
        options = [o for o in options if o.quality == TrackQuality.LOSSLESS]
    elif preferred_format == "high":
        options = [o for o in options if o.quality in [TrackQuality.LOSSLESS, TrackQuality.HIGH]]
    
    # Sort by quality (highest first) then price (lowest first)
    options.sort(key=lambda x: (-x.quality.value if hasattr(x.quality, 'value') else 0, x.price or 0))
    
    return [option.dict() for option in options]


@tool
def find_streaming_options(
    metadata: Dict[str, Any],
    include_free: bool = True,
    include_subscription: bool = True
) -> List[Dict[str, Any]]:
    """
    Find streaming options for a track.
    
    Args:
        metadata: Track metadata
        include_free: Include free streaming options
        include_subscription: Include subscription services
    
    Returns:
        List of streaming options
    """
    options = []
    
    # Spotify
    if metadata.get("spotify_id") or "spotify" in metadata.get("sources", []):
        option = AcquisitionOption(
            source="spotify",
            type="stream",
            quality=TrackQuality.HIGH,
            requires_subscription=True,
            url=f"https://open.spotify.com/track/{metadata.get('spotify_id', '')}",
            formats=["OGG 320"],
            notes="Most popular streaming service"
        )
        if include_subscription:
            options.append(option)
    
    # Deezer
    if metadata.get("isrc") or "deezer" in metadata.get("sources", []):
        option = AcquisitionOption(
            source="deezer",
            type="stream",
            quality=TrackQuality.LOSSLESS,
            requires_subscription=True,
            url=f"https://www.deezer.com/search/{metadata.get('artist')}%20{metadata.get('title')}",
            formats=["FLAC", "MP3 320"],
            notes="HiFi tier offers lossless streaming"
        )
        if include_subscription:
            options.append(option)
    
    # Tidal
    if metadata.get("isrc"):
        option = AcquisitionOption(
            source="tidal",
            type="stream",
            quality=TrackQuality.LOSSLESS,
            requires_subscription=True,
            url=f"https://tidal.com/search?q={metadata.get('artist')}+{metadata.get('title')}",
            formats=["FLAC", "MQA"],
            notes="High-fidelity and master quality audio"
        )
        if include_subscription:
            options.append(option)
    
    # SoundCloud
    if "soundcloud" in metadata.get("sources", []):
        option = AcquisitionOption(
            source="soundcloud",
            type="stream",
            quality=TrackQuality.MEDIUM,
            requires_subscription=False,
            url=f"https://soundcloud.com/search?q={metadata.get('artist')}%20{metadata.get('title')}",
            formats=["MP3 128"],
            notes="Free tier available, good for remixes"
        )
        if include_free:
            options.append(option)
    
    # YouTube
    option = AcquisitionOption(
        source="youtube",
        type="stream",
        quality=TrackQuality.MEDIUM,
        requires_subscription=False,
        url=f"https://www.youtube.com/results?search_query={metadata.get('artist')}+{metadata.get('title')}",
        formats=["Various"],
        notes="Free with ads, YouTube Music available"
    )
    if include_free:
        options.append(option)
    
    return [option.dict() for option in options]


@tool
def check_availability(
    metadata: Dict[str, Any],
    platforms: List[str]
) -> Dict[str, Any]:
    """
    Check track availability on specified platforms.
    
    Args:
        metadata: Track metadata
        platforms: List of platforms to check
    
    Returns:
        Availability status for each platform
    """
    availability = {}
    
    for platform in platforms:
        # Check if we have platform-specific ID or it was found there
        has_id = f"{platform}_id" in metadata
        was_found = platform in metadata.get("sources", [])
        
        if has_id or was_found:
            availability[platform] = {
                "available": True,
                "confidence": 0.9 if has_id else 0.7,
                "url": _generate_platform_url(platform, metadata)
            }
        else:
            # Estimate availability based on metadata
            is_mainstream = metadata.get("isrc") is not None
            is_electronic = "electronic" in metadata.get("genre", "").lower()
            
            if platform == "spotify" and is_mainstream:
                availability[platform] = {
                    "available": True,
                    "confidence": 0.6,
                    "url": None
                }
            elif platform == "beatport" and is_electronic:
                availability[platform] = {
                    "available": True,
                    "confidence": 0.7,
                    "url": None
                }
            else:
                availability[platform] = {
                    "available": False,
                    "confidence": 0.3,
                    "url": None
                }
    
    return availability


def _generate_platform_url(platform: str, metadata: Dict[str, Any]) -> Optional[str]:
    """Generate platform URL from metadata."""
    artist = metadata.get("artist", "")
    title = metadata.get("title", "")
    
    urls = {
        "spotify": f"https://open.spotify.com/search/{artist}%20{title}",
        "beatport": f"https://www.beatport.com/search?q={artist}%20{title}",
        "soundcloud": f"https://soundcloud.com/search?q={artist}%20{title}",
        "youtube": f"https://www.youtube.com/results?search_query={artist}+{title}",
        "deezer": f"https://www.deezer.com/search/{artist}%20{title}",
        "bandcamp": f"https://bandcamp.com/search?q={artist}+{title}"
    }
    
    return urls.get(platform)


@tool
def get_best_source(
    options: List[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Select the best acquisition source based on preferences.
    
    Args:
        options: List of acquisition options
        preferences: User preferences (quality, price, type)
    
    Returns:
        Best acquisition option based on criteria
    """
    if not options:
        return {"error": "No options available"}
    
    if not preferences:
        preferences = {
            "prefer_quality": "lossless",
            "prefer_type": "purchase",
            "max_price": None
        }
    
    # Score each option
    scored_options = []
    for option in options:
        score = 0
        
        # Quality score (0-5)
        quality = option.get("quality", "unknown")
        quality_scores = {
            "lossless": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "unknown": 1
        }
        score += quality_scores.get(quality, 1) * 2  # Weight quality heavily
        
        # Type preference
        option_type = option.get("type", "")
        if option_type == preferences.get("prefer_type", "purchase"):
            score += 3
        
        # Price score (lower is better for purchases)
        if option_type == "purchase":
            price = option.get("price")
            if price:
                max_price = preferences.get("max_price", 5.0)
                if price <= max_price:
                    # Inverse price score (cheaper is better)
                    score += (max_price - price) / max_price * 2
            else:
                score += 1  # Pay-what-you-want
        
        # Source reliability
        source = option.get("source", "")
        reliable_sources = ["beatport", "bandcamp", "spotify", "itunes"]
        if source in reliable_sources:
            score += 1
        
        scored_options.append((score, option))
    
    # Sort by score (highest first)
    scored_options.sort(key=lambda x: x[0], reverse=True)
    
    best_option = scored_options[0][1]
    
    return {
        "best_option": best_option,
        "score": scored_options[0][0],
        "reason": _explain_choice(best_option, preferences),
        "alternatives": [opt for _, opt in scored_options[1:3]]  # Top 3 alternatives
    }


def _explain_choice(option: Dict[str, Any], preferences: Dict[str, Any]) -> str:
    """Explain why this option was chosen."""
    reasons = []
    
    if option.get("quality") == "lossless":
        reasons.append("lossless quality")
    elif option.get("quality") == "high":
        reasons.append("high quality")
    
    if option.get("type") == "purchase":
        reasons.append("permanent ownership")
    elif option.get("type") == "stream":
        if not option.get("requires_subscription"):
            reasons.append("free streaming")
        else:
            reasons.append("subscription streaming")
    
    if option.get("price"):
        reasons.append(f"${option['price']:.2f}")
    
    return f"Best option: {option.get('source')} - {', '.join(reasons)}"