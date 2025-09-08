"""
YouTube-specific exceptions.
"""


class YouTubeError(Exception):
    """Base YouTube exception."""
    pass


class YouTubeAuthError(YouTubeError):
    """Authentication error."""
    pass


class YouTubeAPIError(YouTubeError):
    """API request error."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class YouTubeDownloadError(YouTubeError):
    """Download error."""
    
    def __init__(self, message: str, video_id: str = None, error_code: str = None):
        super().__init__(message)
        self.video_id = video_id
        self.error_code = error_code


class YouTubePlaylistError(YouTubeError):
    """Playlist operation error."""
    
    def __init__(self, message: str, playlist_id: str = None):
        super().__init__(message)
        self.playlist_id = playlist_id


class YouTubeSearchError(YouTubeError):
    """Search error."""
    pass


class YouTubeQuotaError(YouTubeError):
    """API quota exceeded error."""
    pass


class YouTubeRateLimitError(YouTubeError):
    """Rate limit error."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class YouTubeVideoNotFoundError(YouTubeError):
    """Video not found error."""
    
    def __init__(self, video_id: str):
        super().__init__(f"Video not found: {video_id}")
        self.video_id = video_id


class YouTubeVideoUnavailableError(YouTubeError):
    """Video unavailable error."""
    
    def __init__(self, video_id: str, reason: str = None):
        message = f"Video unavailable: {video_id}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)
        self.video_id = video_id
        self.reason = reason


class YouTubeAgeRestrictionError(YouTubeError):
    """Age restricted content error."""
    
    def __init__(self, video_id: str):
        super().__init__(f"Age restricted video: {video_id}")
        self.video_id = video_id


class YouTubePrivateVideoError(YouTubeError):
    """Private video error."""
    
    def __init__(self, video_id: str):
        super().__init__(f"Private video: {video_id}")
        self.video_id = video_id


class YouTubeFormatNotFoundError(YouTubeError):
    """Requested format not available."""
    
    def __init__(self, format_selector: str, video_id: str = None):
        message = f"Format not found: {format_selector}"
        if video_id:
            message += f" for video {video_id}"
        super().__init__(message)
        self.format_selector = format_selector
        self.video_id = video_id