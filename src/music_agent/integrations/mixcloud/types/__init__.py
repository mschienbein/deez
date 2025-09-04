"""
Type definitions for Mixcloud API.

Provides TypedDict definitions for all API responses and requests.
"""

from typing import TypedDict, Optional, List, Dict, Any, Union
from datetime import datetime


# ============================================
# Authentication Types
# ============================================

class AuthCredentials(TypedDict, total=False):
    """OAuth2 authentication credentials."""
    client_id: Optional[str]
    client_secret: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    redirect_uri: Optional[str]
    scope: Optional[str]


class TokenResponse(TypedDict):
    """OAuth2 token response."""
    access_token: str
    token_type: str
    expires_in: Optional[int]
    refresh_token: Optional[str]
    scope: Optional[str]


# ============================================
# User Types
# ============================================

class UserResponse(TypedDict, total=False):
    """User API response."""
    key: str  # e.g., "/spartacus/"
    url: str  # Full URL to user page
    username: str
    name: str
    biog: Optional[str]
    country: Optional[str]
    city: Optional[str]
    created_time: Optional[str]
    updated_time: Optional[str]
    picture_primary_color: Optional[str]
    cloudcast_count: Optional[int]
    favorite_count: Optional[int]
    follower_count: Optional[int]
    following_count: Optional[int]
    is_pro: Optional[bool]
    is_premium: Optional[bool]
    is_verified: Optional[bool]
    pictures: Optional[Dict[str, str]]  # Different sizes


class UserConnectionsResponse(TypedDict):
    """User connections response."""
    facebook: Optional[str]
    twitter: Optional[str]


# ============================================
# Cloudcast (Show/Mix) Types
# ============================================

class CloudcastResponse(TypedDict, total=False):
    """Cloudcast (mix/show) API response."""
    key: str  # e.g., "/spartacus/party-time/"
    url: str  # Full URL to cloudcast
    name: str
    slug: str
    description: Optional[str]
    created_time: str
    updated_time: str
    audio_length: int  # Duration in seconds
    play_count: int
    favorite_count: int
    repost_count: int
    comment_count: int
    listener_count: int
    user: UserResponse
    tags: List['TagResponse']
    sections: List['SectionResponse']
    pictures: Dict[str, str]
    is_exclusive: bool
    is_unlisted: bool
    waveform_url: Optional[str]
    preview_url: Optional[str]  # Short preview URL
    stream_url: Optional[str]  # Full stream URL (if available)


class SectionResponse(TypedDict):
    """Track section in a cloudcast."""
    start_time: int  # Seconds from start
    track: Optional['TrackResponse']
    chapter: Optional[str]


class TrackResponse(TypedDict):
    """Track/song information."""
    artist: str
    song: str
    publisher: Optional[str]


# ============================================
# Tag & Category Types
# ============================================

class TagResponse(TypedDict):
    """Tag/genre API response."""
    key: str  # e.g., "/tag/house/"
    url: str
    name: str


class CategoryResponse(TypedDict):
    """Category API response."""
    key: str  # e.g., "/categories/house/"
    url: str
    name: str
    slug: str
    format: Optional[str]


# ============================================
# Comment Types
# ============================================

class CommentResponse(TypedDict):
    """Comment API response."""
    key: str
    comment: str
    created_time: str
    user: UserResponse
    submit_date: str


# ============================================
# Search Types
# ============================================

class SearchFilters(TypedDict, total=False):
    """Search filter parameters."""
    type: Optional[str]  # cloudcast, user, tag
    tag: Optional[List[str]]  # Filter by tags
    user: Optional[str]  # Filter by user
    before: Optional[str]  # Date filter
    after: Optional[str]  # Date filter
    audio_length: Optional[str]  # Duration filter
    country: Optional[str]


class SearchResponse(TypedDict):
    """Search results response."""
    data: List[Union[CloudcastResponse, UserResponse, TagResponse]]
    paging: 'PagingResponse'


# ============================================
# Feed & Activity Types
# ============================================

class FeedItemResponse(TypedDict):
    """Feed item response."""
    key: str
    type: str  # cloudcast, repost, favorite, etc.
    cloudcast: Optional[CloudcastResponse]
    user: Optional[UserResponse]
    created_time: str


class ActivityResponse(TypedDict):
    """User activity response."""
    type: str  # upload, favorite, repost, follow
    cloudcast: Optional[CloudcastResponse]
    user: Optional[UserResponse]
    created_time: str


# ============================================
# Playlist Types
# ============================================

class PlaylistResponse(TypedDict, total=False):
    """Playlist API response."""
    key: str
    url: str
    name: str
    slug: str
    description: Optional[str]
    cloudcast_count: int
    exclusive_cloudcast_count: int
    owner: UserResponse
    created_time: str
    updated_time: str
    pictures: Dict[str, str]


# ============================================
# Stats Types
# ============================================

class StatsResponse(TypedDict):
    """Statistics response."""
    play_count: int
    favorite_count: int
    repost_count: int
    comment_count: int
    listener_count: int
    peak_listener_count: Optional[int]


class ListeningHistoryResponse(TypedDict):
    """Listening history item."""
    cloudcast: CloudcastResponse
    listened_time: str


# ============================================
# Upload Types
# ============================================

class UploadRequest(TypedDict, total=False):
    """Upload request parameters."""
    name: str
    description: Optional[str]
    tags: Optional[List[str]]
    sections: Optional[List[Dict[str, Any]]]
    picture: Optional[bytes]
    is_unlisted: Optional[bool]
    publish_date: Optional[str]


class UploadResponse(TypedDict):
    """Upload response."""
    result: bool
    key: Optional[str]
    message: Optional[str]


# ============================================
# Download Types
# ============================================

class DownloadOptions(TypedDict, total=False):
    """Download options."""
    output_path: Optional[str]
    quality: Optional[str]  # high, medium, low
    format: Optional[str]  # mp3, m4a, original
    write_metadata: Optional[bool]
    embed_artwork: Optional[bool]
    progress_callback: Optional[Any]
    chunk_size: Optional[int]


class StreamInfo(TypedDict):
    """Stream information."""
    url: str
    format: str
    quality: str
    size: Optional[int]
    duration: Optional[int]


# ============================================
# Pagination Types
# ============================================

class PagingResponse(TypedDict):
    """Pagination information."""
    previous: Optional[str]
    next: Optional[str]


class PagedResponse(TypedDict):
    """Generic paged response."""
    data: List[Any]
    paging: PagingResponse


# ============================================
# Error Types
# ============================================

class ErrorResponse(TypedDict):
    """API error response."""
    error: str
    error_type: Optional[str]
    message: Optional[str]
    status_code: Optional[int]


# ============================================
# Widget Types
# ============================================

class WidgetOptions(TypedDict, total=False):
    """Widget embed options."""
    width: Optional[int]
    height: Optional[int]
    light: Optional[bool]
    hide_cover: Optional[bool]
    hide_artwork: Optional[bool]
    hide_tracklist: Optional[bool]
    mini: Optional[bool]
    autoplay: Optional[bool]
    start: Optional[int]  # Start time in seconds


# ============================================
# Live Stream Types
# ============================================

class LiveStreamResponse(TypedDict):
    """Live stream information."""
    key: str
    name: str
    description: Optional[str]
    is_live: bool
    viewer_count: Optional[int]
    stream_url: Optional[str]
    chat_enabled: bool


# ============================================
# Notification Types
# ============================================

class NotificationResponse(TypedDict):
    """Notification response."""
    key: str
    type: str  # follow, favorite, repost, comment
    message: str
    is_read: bool
    created_time: str
    user: Optional[UserResponse]
    cloudcast: Optional[CloudcastResponse]


__all__ = [
    # Authentication
    "AuthCredentials",
    "TokenResponse",
    
    # Core models
    "UserResponse",
    "UserConnectionsResponse",
    "CloudcastResponse",
    "SectionResponse",
    "TrackResponse",
    "TagResponse",
    "CategoryResponse",
    "CommentResponse",
    "PlaylistResponse",
    
    # Search & Discovery
    "SearchFilters",
    "SearchResponse",
    "FeedItemResponse",
    "ActivityResponse",
    
    # Stats & History
    "StatsResponse",
    "ListeningHistoryResponse",
    
    # Upload & Download
    "UploadRequest",
    "UploadResponse",
    "DownloadOptions",
    "StreamInfo",
    
    # Live & Notifications
    "LiveStreamResponse",
    "NotificationResponse",
    
    # Utils
    "PagingResponse",
    "PagedResponse",
    "ErrorResponse",
    "WidgetOptions",
]