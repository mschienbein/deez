"""
Enumeration types for MusicBrainz.
"""

from enum import Enum


class EntityType(Enum):
    """MusicBrainz entity types."""
    ARTIST = "artist"
    RELEASE = "release"
    RELEASE_GROUP = "release-group"
    RECORDING = "recording"
    WORK = "work"
    LABEL = "label"
    AREA = "area"
    EVENT = "event"
    PLACE = "place"
    SERIES = "series"
    URL = "url"


class ReleaseType(Enum):
    """Release types."""
    ALBUM = "album"
    SINGLE = "single"
    EP = "ep"
    BROADCAST = "broadcast"
    OTHER = "other"


class ReleaseStatus(Enum):
    """Release status."""
    OFFICIAL = "official"
    PROMOTION = "promotion"
    BOOTLEG = "bootleg"
    PSEUDO_RELEASE = "pseudo-release"


class SearchField(Enum):
    """Search fields for advanced queries."""
    ARTIST = "artist"
    ARTISTNAME = "artistname"
    RELEASE = "release"
    RELEASENAME = "releasename"
    RECORDING = "recording"
    RECORDINGNAME = "recordingname"
    TRACK = "track"
    TRACKNAME = "trackname"
    LABEL = "label"
    LABELNAME = "labelname"
    YEAR = "year"
    DATE = "date"
    COUNTRY = "country"
    FORMAT = "format"
    BARCODE = "barcode"
    CATNO = "catno"
    ISRC = "isrc"
    ISWC = "iswc"
    TAG = "tag"
    COMMENT = "comment"