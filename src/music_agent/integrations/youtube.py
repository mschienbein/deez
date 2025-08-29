"""YouTube integration using yt-dlp."""

import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

from ..utils.config import config

logger = logging.getLogger(__name__)


class YouTubeIntegration:
    """YouTube integration for music discovery and download."""
    
    def __init__(self, cookies_file: Optional[str] = None):
        """Initialize YouTube integration."""
        self.cookies_file = cookies_file or config.youtube.cookies_file
        self.rate_limit = config.youtube.rate_limit
        self.audio_format = config.youtube.audio_format
        self.audio_quality = config.youtube.audio_quality
    
    def _get_yt_dlp_command(self, extra_args: Optional[List[str]] = None) -> List[str]:
        """Build yt-dlp command with common options."""
        cmd = ["yt-dlp"]
        
        if self.cookies_file:
            cmd.extend(["--cookies", self.cookies_file])
        
        if extra_args:
            cmd.extend(extra_args)
        
        return cmd
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for music videos on YouTube."""
        try:
            cmd = self._get_yt_dlp_command([
                f"ytsearch{limit}:{query}",
                "--dump-json",
                "--no-download",
                "--flat-playlist"
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"yt-dlp search failed: {result.stderr}")
                return []
            
            results = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        track_info = self._format_video_info(video_info)
                        results.append(track_info)
                    except json.JSONDecodeError:
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return []
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed video information."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            cmd = self._get_yt_dlp_command([
                url,
                "--dump-json",
                "--no-download"
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get video info: {result.stderr}")
                return None
            
            video_info = json.loads(result.stdout.strip())
            return self._format_video_info(video_info)
            
        except Exception as e:
            logger.error(f"Failed to get video info {video_id}: {e}")
            return None
    
    def get_playlist_videos(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get videos from a playlist."""
        try:
            url = f"https://www.youtube.com/playlist?list={playlist_id}"
            cmd = self._get_yt_dlp_command([
                url,
                "--dump-json",
                "--no-download",
                "--flat-playlist"
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get playlist videos: {result.stderr}")
                return []
            
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        track_info = self._format_video_info(video_info)
                        videos.append(track_info)
                    except json.JSONDecodeError:
                        continue
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get playlist videos {playlist_id}: {e}")
            return []
    
    def get_download_url(self, video_id: str, format_selector: str = "bestaudio") -> Optional[str]:
        """Get direct download URL for a video."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            cmd = self._get_yt_dlp_command([
                url,
                "--get-url",
                "-f", format_selector
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get download URL: {result.stderr}")
                return None
            
            return result.stdout.strip()
            
        except Exception as e:
            logger.error(f"Failed to get download URL for {video_id}: {e}")
            return None
    
    def download_audio(
        self,
        url: str,
        output_dir: str = "./downloads",
        quality: Optional[str] = None
    ) -> Optional[str]:
        """Download audio from YouTube video."""
        try:
            audio_quality = quality or self.audio_quality
            
            cmd = self._get_yt_dlp_command([
                url,
                "-x",  # Extract audio
                "--audio-format", self.audio_format,
                "--audio-quality", audio_quality,
                "-o", f"{output_dir}/%(title)s.%(ext)s",
                "--embed-metadata"
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout for downloads
            )
            
            if result.returncode != 0:
                logger.error(f"Download failed: {result.stderr}")
                return None
            
            # Extract output filename from stdout
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if "Destination:" in line or "has already been downloaded" in line:
                    # Extract filename
                    filename = line.split()[-1]
                    return filename
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to download audio from {url}: {e}")
            return None
    
    def parse_youtube_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse YouTube URL to extract type and ID."""
        import re
        
        # Video patterns
        video_patterns = [
            r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
            r"youtu\.be/([a-zA-Z0-9_-]+)",
            r"youtube\.com/embed/([a-zA-Z0-9_-]+)"
        ]
        
        for pattern in video_patterns:
            match = re.search(pattern, url)
            if match:
                return {
                    "type": "video",
                    "id": match.group(1)
                }
        
        # Playlist pattern
        playlist_match = re.search(r"youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)", url)
        if playlist_match:
            return {
                "type": "playlist",
                "id": playlist_match.group(1)
            }
        
        return None
    
    def extract_music_metadata(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract music metadata from video info."""
        title = video_info.get("title", "")
        description = video_info.get("description", "")
        
        # Try to parse artist and track from title
        artist = ""
        track_title = title
        
        # Common patterns: "Artist - Title", "Artist: Title", "Title by Artist"
        separators = [" - ", ": ", " by "]
        for sep in separators:
            if sep in title:
                parts = title.split(sep, 1)
                if len(parts) == 2:
                    if sep == " by ":
                        track_title, artist = parts
                    else:
                        artist, track_title = parts
                    break
        
        # Clean up common suffixes
        suffixes_to_remove = [
            " (Official Video)",
            " (Official Audio)",
            " (Lyric Video)",
            " (Lyrics)",
            " [Official Video]",
            " [Official Audio]"
        ]
        
        for suffix in suffixes_to_remove:
            if track_title.endswith(suffix):
                track_title = track_title[:-len(suffix)]
                break
        
        return {
            "artist": artist.strip(),
            "title": track_title.strip(),
            "original_title": title
        }
    
    def _format_video_info(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format video data to standardized format."""
        # Extract music metadata
        music_metadata = self.extract_music_metadata(video_info)
        
        return {
            "id": video_info.get("id", ""),
            "title": music_metadata["title"] or video_info.get("title", ""),
            "artist": music_metadata["artist"],
            "album": "",  # Not available from YouTube
            "duration": int(video_info.get("duration", 0)),
            "view_count": video_info.get("view_count", 0),
            "like_count": video_info.get("like_count", 0),
            "upload_date": video_info.get("upload_date", ""),
            "uploader": video_info.get("uploader", ""),
            "description": video_info.get("description", "")[:500],  # Truncate
            "thumbnail": video_info.get("thumbnail", ""),
            "platform": "youtube",
            "platform_url": f"https://www.youtube.com/watch?v={video_info.get('id', '')}",
            "available": True,
            "original_title": music_metadata["original_title"]
        }


# Convenience functions for use with Strands tools
def youtube_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for music on YouTube."""
    youtube = YouTubeIntegration()
    return youtube.search(query, limit)


def get_youtube_video_info(video_id: str) -> Optional[Dict[str, Any]]:
    """Get YouTube video information."""
    youtube = YouTubeIntegration()
    return youtube.get_video_info(video_id)


def download_youtube_audio(url: str, output_dir: str = "./downloads") -> Optional[str]:
    """Download audio from YouTube video."""
    youtube = YouTubeIntegration()
    return youtube.download_audio(url, output_dir)


def get_youtube_playlist_videos(playlist_url: str) -> List[Dict[str, Any]]:
    """Get videos from YouTube playlist."""
    youtube = YouTubeIntegration()
    url_info = youtube.parse_youtube_url(playlist_url)
    
    if url_info and url_info["type"] == "playlist":
        return youtube.get_playlist_videos(url_info["id"])
    
    return []