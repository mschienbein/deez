"""
Beatport API integration.

A comprehensive Python client for the Beatport API v4, providing access to:
- Track search and metadata
- Release/album information
- Artist and label data
- Charts (Top 100, Hype, Essential, etc.)
- OAuth token-based authentication

Example:
    >>> from beatport import BeatportClient
    >>> client = BeatportClient()
    >>> 
    >>> # Search for tracks
    >>> tracks = client.search_tracks("techno", bpm_low=120, bpm_high=130)
    >>> 
    >>> # Get charts
    >>> top_100 = client.get_top_100()
"""

from .client import BeatportClient
from .config import BeatportConfig
from .exceptions import (
    BeatportError,
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
    APIError,
    RateLimitError,
    NotFoundError,
    NetworkError
)
from .models import (
    Track, Release, Artist, Label, Genre, Key,
    SearchQuery, SearchResult, Chart, ChartTrack,
    SearchType, ChartType, SortField, SortDirection, AudioFormat
)

__version__ = "1.0.0"

__all__ = [
    # Client
    'BeatportClient',
    'BeatportConfig',
    
    # Exceptions
    'BeatportError',
    'AuthenticationError',
    'TokenExpiredError',
    'InvalidCredentialsError',
    'APIError',
    'RateLimitError',
    'NotFoundError',
    'NetworkError',
    
    # Models
    'Track',
    'Release',
    'Artist',
    'Label',
    'Genre',
    'Key',
    'SearchQuery',
    'SearchResult',
    'Chart',
    'ChartTrack',
    
    # Enums
    'SearchType',
    'ChartType',
    'SortField',
    'SortDirection',
    'AudioFormat'
]