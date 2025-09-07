"""
Utility functions for Discogs integration.
"""

from .text import (
    clean_artist_name,
    parse_catalog_number,
    extract_year_from_released,
    normalize_format,
    is_various_artists,
    extract_remix_info,
)
from .time import format_duration, parse_duration
from .matching import calculate_match_score, merge_track_artists
from .quality import estimate_track_quality

__all__ = [
    "clean_artist_name",
    "parse_catalog_number",
    "format_duration",
    "parse_duration",
    "extract_year_from_released",
    "normalize_format",
    "calculate_match_score",
    "merge_track_artists",
    "estimate_track_quality",
    "is_various_artists",
    "extract_remix_info",
]