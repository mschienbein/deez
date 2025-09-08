"""
YouTube video API implementation.
"""

import json
import logging
import subprocess
from typing import Optional, Dict, Any, List
import httpx

from ..models import Video
from ..exceptions import (
    YouTubeVideoNotFoundError,
    YouTubeVideoUnavailableError,
    YouTubeAPIError,
    YouTubeQuotaError
)

logger = logging.getLogger(__name__)


class YouTubeVideoAPI:
    """YouTube video information API."""
    
    def __init__(self, api_key: Optional[str] = None, ytdlp_opts: Dict[str, Any] = None):
        """Initialize video API."""
        self.api_key = api_key
        self.ytdlp_opts = ytdlp_opts or {}
    
    def get_video(self, video_id: str) -> Video:
        """
        Get video information.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video object with metadata
        """
        # Try YouTube Data API first if available
        if self.api_key:
            try:
                return self._get_video_via_api(video_id)
            except (YouTubeAPIError, YouTubeQuotaError) as e:
                logger.warning(f"API failed, falling back to yt-dlp: {e}")
        
        # Fall back to yt-dlp
        return self._get_video_via_ytdlp(video_id)
    
    def _get_video_via_api(self, video_id: str) -> Video:
        """Get video using YouTube Data API."""
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,contentDetails,statistics,status",
            "id": video_id,
            "key": self.api_key
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params)
            
            if response.status_code == 403:
                error_data = response.json()
                if "quotaExceeded" in str(error_data):
                    raise YouTubeQuotaError("YouTube API quota exceeded")
                raise YouTubeAPIError(
                    "API request forbidden",
                    status_code=403,
                    response_data=error_data
                )
            
            if response.status_code != 200:
                raise YouTubeAPIError(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code
                )
            
            data = response.json()
            
            if not data.get("items"):
                raise YouTubeVideoNotFoundError(video_id)
            
            video_data = data["items"][0]
            
            # Check availability
            status = video_data.get("status", {})
            if status.get("privacyStatus") == "private":
                raise YouTubeVideoUnavailableError(video_id, "Private video")
            
            return Video.from_api(video_data)
    
    def _get_video_via_ytdlp(self, video_id: str) -> Video:
        """Get video using yt-dlp."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            cmd = ["yt-dlp", url, "--dump-json", "--no-download"]
            
            if self.ytdlp_opts.get("cookiefile"):
                cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr
                
                if "Video unavailable" in error_msg:
                    raise YouTubeVideoUnavailableError(video_id)
                elif "Private video" in error_msg:
                    raise YouTubeVideoUnavailableError(video_id, "Private video")
                elif "does not exist" in error_msg:
                    raise YouTubeVideoNotFoundError(video_id)
                
                raise YouTubeAPIError(f"Failed to get video info: {error_msg}")
            
            video_data = json.loads(result.stdout.strip())
            return Video.from_ytdlp(video_data)
            
        except subprocess.TimeoutExpired:
            raise YouTubeAPIError("Request timed out")
        except json.JSONDecodeError as e:
            raise YouTubeAPIError(f"Failed to parse video data: {e}")
        except Exception as e:
            if isinstance(e, (YouTubeVideoNotFoundError, YouTubeVideoUnavailableError)):
                raise
            raise YouTubeAPIError(f"Failed to get video info: {str(e)}")
    
    def get_multiple_videos(self, video_ids: List[str]) -> List[Video]:
        """
        Get information for multiple videos.
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            List of Video objects
        """
        videos = []
        
        # If we have API key, batch request
        if self.api_key and len(video_ids) <= 50:
            try:
                return self._get_videos_via_api(video_ids)
            except Exception as e:
                logger.warning(f"Batch API failed: {e}")
        
        # Fall back to individual requests
        for video_id in video_ids:
            try:
                video = self.get_video(video_id)
                videos.append(video)
            except Exception as e:
                logger.error(f"Failed to get video {video_id}: {e}")
                continue
        
        return videos
    
    def _get_videos_via_api(self, video_ids: List[str]) -> List[Video]:
        """Get multiple videos using YouTube Data API."""
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,contentDetails,statistics,status",
            "id": ",".join(video_ids[:50]),  # API limit
            "key": self.api_key,
            "maxResults": 50
        }
        
        with httpx.Client() as client:
            response = client.get(url, params=params)
            
            if response.status_code != 200:
                raise YouTubeAPIError(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code
                )
            
            data = response.json()
            videos = []
            
            for item in data.get("items", []):
                try:
                    video = Video.from_api(item)
                    videos.append(video)
                except Exception as e:
                    logger.error(f"Failed to parse video: {e}")
                    continue
            
            return videos
    
    def get_video_url(self, video_id: str, quality: str = "best") -> str:
        """
        Get direct URL for video/audio stream.
        
        Args:
            video_id: YouTube video ID
            quality: Quality selector (best, bestaudio, etc.)
            
        Returns:
            Direct URL for the stream
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            cmd = ["yt-dlp", url, "--get-url", "-f", quality]
            
            if self.ytdlp_opts.get("cookiefile"):
                cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise YouTubeAPIError(f"Failed to get stream URL: {result.stderr}")
            
            return result.stdout.strip()
            
        except Exception as e:
            raise YouTubeAPIError(f"Failed to get stream URL: {str(e)}")
    
    def get_available_formats(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get available formats for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of available formats
        """
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            cmd = ["yt-dlp", url, "--list-formats"]
            
            if self.ytdlp_opts.get("cookiefile"):
                cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise YouTubeAPIError(f"Failed to get formats: {result.stderr}")
            
            # Parse format list
            formats = []
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line and not line.startswith('['):
                    # Parse format line
                    parts = line.split()
                    if len(parts) >= 3:
                        format_info = {
                            "format_id": parts[0],
                            "ext": parts[1] if len(parts) > 1 else "",
                            "resolution": parts[2] if len(parts) > 2 else "",
                            "note": " ".join(parts[3:]) if len(parts) > 3 else ""
                        }
                        formats.append(format_info)
            
            return formats
            
        except Exception as e:
            raise YouTubeAPIError(f"Failed to get formats: {str(e)}")
    
    def extract_audio_metadata(self, video: Video) -> Dict[str, Any]:
        """
        Extract audio/music metadata from video.
        
        Args:
            video: Video object
            
        Returns:
            Dictionary with music metadata
        """
        return video.to_music_track()