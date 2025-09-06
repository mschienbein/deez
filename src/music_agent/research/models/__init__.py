"""
Music Metadata Research System - Data Models

Universal metadata models for comprehensive track information across all platforms.
"""

from .track_metadata import (
    TrackQuality,
    TrackStatus,
    UniversalTrackMetadata,
    ArtworkInfo,
    PlatformMetadata
)

__all__ = [
    'TrackQuality',
    'TrackStatus',
    'UniversalTrackMetadata',
    'ArtworkInfo',
    'PlatformMetadata'
]