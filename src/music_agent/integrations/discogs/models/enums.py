"""
Enumerations for Discogs models.
"""

from enum import Enum


class SearchType(Enum):
    """Discogs search types."""
    RELEASE = "release"
    MASTER = "master"
    ARTIST = "artist"
    LABEL = "label"


class ReleaseFormat(Enum):
    """Common release formats."""
    VINYL = "Vinyl"
    CD = "CD"
    CASSETTE = "Cassette"
    FILE = "File"
    DVD = "DVD"
    DIGITAL = "Digital"


class Condition(Enum):
    """Media and sleeve conditions."""
    MINT = "Mint (M)"
    NEAR_MINT = "Near Mint (NM or M-)"
    VERY_GOOD_PLUS = "Very Good Plus (VG+)"
    VERY_GOOD = "Very Good (VG)"
    GOOD_PLUS = "Good Plus (G+)"
    GOOD = "Good (G)"
    FAIR = "Fair (F)"
    POOR = "Poor (P)"