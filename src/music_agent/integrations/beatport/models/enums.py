"""
Enumeration types for Beatport.
"""

from enum import Enum


class SearchType(Enum):
    """Search types available in Beatport API."""
    TRACKS = "tracks"
    RELEASES = "releases"
    ARTISTS = "artists"
    LABELS = "labels"


class ChartType(Enum):
    """Chart types available."""
    TOP_100 = "top-100"
    HYPE = "hype"
    ESSENTIAL = "essential"
    BEATPORT_PICKS = "beatport-picks"


class SortField(Enum):
    """Sort fields for queries."""
    RELEASE_DATE = "release_date"
    PUBLISH_DATE = "publish_date"
    BPM = "bpm"
    NAME = "name"
    PRICE = "price"
    LENGTH = "length"
    RATING = "rating"


class SortDirection(Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"


class AudioFormat(Enum):
    """Audio format types."""
    MP3_128 = "mp3-128"
    MP3_320 = "mp3-320"
    MP4_256 = "mp4-256"
    WAV = "wav"
    AIFF = "aiff"