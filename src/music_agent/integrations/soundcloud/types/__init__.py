"""
Type definitions for SoundCloud integration.

Centralized type hints and interfaces for better type safety
and code documentation.
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal, Union
from datetime import datetime
from pathlib import Path

# API Response Types
class TrackResponse(TypedDict, total=False):
    """Raw track response from SoundCloud API."""
    id: int
    kind: Literal["track"]
    created_at: str
    user_id: int
    duration: int
    commentable: bool
    state: str
    original_content_size: int
    last_modified: str
    sharing: str
    tag_list: str
    permalink: str
    streamable: bool
    embeddable_by: str
    downloadable: bool
    purchase_url: Optional[str]
    label_id: Optional[int]
    purchase_title: Optional[str]
    genre: str
    title: str
    description: str
    label_name: Optional[str]
    release: Optional[str]
    track_type: Optional[str]
    key_signature: Optional[str]
    isrc: Optional[str]
    video_url: Optional[str]
    bpm: Optional[float]
    release_year: Optional[int]
    release_month: Optional[int]
    release_day: Optional[int]
    original_format: str
    license: str
    uri: str
    user: Dict[str, Any]
    permalink_url: str
    artwork_url: Optional[str]
    waveform_url: str
    stream_url: Optional[str]
    playback_count: int
    download_count: int
    favoritings_count: int
    reposts_count: int
    comment_count: int
    likes_count: int
    download_url: Optional[str]
    media: Optional[Dict[str, Any]]


class PlaylistResponse(TypedDict, total=False):
    """Raw playlist response from SoundCloud API."""
    id: int
    kind: Literal["playlist", "system-playlist"]
    created_at: str
    user_id: int
    duration: int
    sharing: str
    tag_list: str
    permalink: str
    streamable: bool
    embeddable_by: str
    purchase_url: Optional[str]
    label_id: Optional[int]
    type: str
    playlist_type: str
    ean: Optional[str]
    description: str
    genre: str
    release: Optional[str]
    purchase_title: Optional[str]
    label_name: Optional[str]
    title: str
    release_year: Optional[int]
    release_month: Optional[int]
    release_day: Optional[int]
    license: str
    uri: str
    user: Dict[str, Any]
    permalink_url: str
    artwork_url: Optional[str]
    likes_count: int
    tracks: List[Union[TrackResponse, Dict[str, Any]]]
    track_count: int
    is_album: bool
    published_at: Optional[str]


class UserResponse(TypedDict, total=False):
    """Raw user response from SoundCloud API."""
    id: int
    kind: Literal["user"]
    permalink: str
    username: str
    last_modified: str
    uri: str
    permalink_url: str
    avatar_url: str
    country: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    description: Optional[str]
    city: Optional[str]
    discogs_name: Optional[str]
    myspace_name: Optional[str]
    website: Optional[str]
    website_title: Optional[str]
    track_count: int
    playlist_count: int
    online: bool
    plan: str
    public_favorites_count: int
    followers_count: int
    followings_count: int
    reposts_count: int
    comments_count: int


class CommentResponse(TypedDict, total=False):
    """Raw comment response from SoundCloud API."""
    id: int
    kind: Literal["comment"]
    created_at: str
    user_id: int
    track_id: int
    timestamp: Optional[int]
    body: str
    uri: str
    user: Dict[str, Any]


# Search Types
class SearchFilters(TypedDict, total=False):
    """Filters for search queries."""
    q: str  # Query string
    limit: int
    offset: int
    linked_partitioning: bool
    genres: Optional[List[str]]
    tags: Optional[List[str]]
    duration_from: Optional[int]  # milliseconds
    duration_to: Optional[int]
    created_at_from: Optional[datetime]
    created_at_to: Optional[datetime]
    bpm_from: Optional[float]
    bpm_to: Optional[float]
    key_signature: Optional[str]
    downloadable: Optional[bool]
    streamable: Optional[bool]
    public: Optional[bool]
    private: Optional[bool]


class SearchResult(TypedDict):
    """Search result container."""
    collection: List[Union[TrackResponse, PlaylistResponse, UserResponse]]
    next_href: Optional[str]
    query_urn: Optional[str]
    total_results: Optional[int]
    facets: Optional[Dict[str, Any]]


# Download Types
class DownloadOptions(TypedDict, total=False):
    """Options for downloading tracks."""
    output_path: Optional[Path]
    quality: Literal["high", "medium", "low"]
    write_metadata: bool
    embed_artwork: bool
    artwork_size: Literal["original", "t500x500", "t300x300", "large", "t67x67"]
    normalize_audio: bool
    convert_format: Optional[Literal["mp3", "wav", "flac"]]
    chunk_size: int
    resume: bool
    progress_callback: Optional[Any]  # Callable[[int, int], None]


class StreamInfo(TypedDict):
    """Stream information for a track."""
    url: str
    protocol: Literal["http", "hls", "progressive"]
    format: str
    quality: str


# Authentication Types
class AuthCredentials(TypedDict, total=False):
    """Authentication credentials."""
    client_id: Optional[str]
    client_secret: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    username: Optional[str]
    password: Optional[str]
    redirect_uri: Optional[str]
    scope: Optional[str]


class TokenResponse(TypedDict):
    """OAuth token response."""
    access_token: str
    expires_in: int
    scope: str
    refresh_token: Optional[str]
    token_type: str


# Request Types
class RequestOptions(TypedDict, total=False):
    """Options for API requests."""
    headers: Optional[Dict[str, str]]
    params: Optional[Dict[str, Any]]
    timeout: Optional[int]
    max_retries: Optional[int]
    retry_delay: Optional[float]
    verify_ssl: bool


# Pagination Types
class PaginationParams(TypedDict, total=False):
    """Pagination parameters."""
    limit: int
    offset: int
    linked_partitioning: bool
    cursor: Optional[str]


class PaginatedResponse(TypedDict, total=False):
    """Paginated API response."""
    collection: List[Any]
    next_href: Optional[str]
    future_href: Optional[str]
    cursor: Optional[str]


# Cache Types
class CacheEntry(TypedDict):
    """Cache entry structure."""
    data: Any
    timestamp: float
    ttl: int
    key: str


# Export types for easy importing
__all__ = [
    # Response types
    "TrackResponse",
    "PlaylistResponse",
    "UserResponse",
    "CommentResponse",
    # Search types
    "SearchFilters",
    "SearchResult",
    # Download types
    "DownloadOptions",
    "StreamInfo",
    # Auth types
    "AuthCredentials",
    "TokenResponse",
    # Request types
    "RequestOptions",
    "PaginationParams",
    "PaginatedResponse",
    # Cache types
    "CacheEntry",
]