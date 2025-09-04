"""
Bandcamp integration for music agent.

Provides scraping-based access to Bandcamp for searching, 
browsing, and downloading music with metadata.
"""

from .client import BandcampClient
from .config import BandcampConfig
from .models import Album, Track
from .exceptions import (
    BandcampError,
    ScrapingError,
    DownloadError,
    InvalidURLError,
)

__version__ = "1.0.0"

__all__ = [
    "BandcampClient",
    "BandcampConfig",
    "Album",
    "Track",
    "BandcampError",
    "ScrapingError",
    "DownloadError",
    "InvalidURLError",
]