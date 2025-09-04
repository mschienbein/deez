"""
Type definitions for Bandcamp integration.
"""

from typing import TypedDict, Optional, List, Dict, Any


class TrackInfo(TypedDict):
    """Information about a track."""
    id: str
    title: str
    artist: str
    album: Optional[str]
    duration: Optional[int]  # in seconds
    track_num: Optional[int]
    url: str
    stream_url: Optional[str]
    download_url: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    release_date: Optional[str]
    lyrics: Optional[str]
    tags: List[str]
    file_format: Optional[str]


class AlbumInfo(TypedDict):
    """Information about an album."""
    id: str
    title: str
    artist: str
    artist_id: Optional[str]
    url: str
    release_date: Optional[str]
    description: Optional[str]
    tracks: List[TrackInfo]
    artwork_url: Optional[str]
    tags: List[str]
    price: Optional[float]
    currency: Optional[str]
    label: Optional[str]
    format: Optional[str]  # Digital, Vinyl, CD, etc.
    about: Optional[str]


class ArtistInfo(TypedDict):
    """Information about an artist."""
    id: str
    name: str
    url: str
    location: Optional[str]
    bio: Optional[str]
    website: Optional[str]
    bandcamp_url: str
    image_url: Optional[str]
    albums: List[AlbumInfo]
    tracks: List[TrackInfo]
    genre: Optional[str]
    verified: bool


class SearchResult(TypedDict):
    """Search result item."""
    type: str  # "artist", "album", "track", "label"
    name: str
    artist: Optional[str]
    url: str
    image_url: Optional[str]
    genre: Optional[str]
    location: Optional[str]
    tags: List[str]
    released: Optional[str]
    num_tracks: Optional[int]


class DownloadOptions(TypedDict, total=False):
    """Options for downloading."""
    format: str  # mp3, flac, etc.
    quality: str  # high, medium, low
    embed_artwork: bool
    embed_lyrics: bool
    write_metadata: bool
    filename_template: str
    output_dir: str
    overwrite: bool


class StreamData(TypedDict):
    """Stream data extracted from page."""
    mp3_url: Optional[str]
    download_url: Optional[str]
    free: bool
    price: Optional[float]
    currency: Optional[str]
    formats: List[str]


class PageData(TypedDict):
    """Data extracted from a Bandcamp page."""
    type: str  # "album", "track", "artist"
    data: Dict[str, Any]
    stream_data: Optional[StreamData]
    metadata: Dict[str, Any]


__all__ = [
    "TrackInfo",
    "AlbumInfo",
    "ArtistInfo",
    "SearchResult",
    "DownloadOptions",
    "StreamData",
    "PageData",
]