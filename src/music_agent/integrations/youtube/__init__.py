"""
YouTube integration for music discovery and download.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from .config import YouTubeConfig
from .auth import YouTubeAuth
from .api import YouTubeSearchAPI, YouTubeVideoAPI
from .download import YouTubeDownloadManager
from .playlist import YouTubePlaylistManager
from .models import Video, Playlist, Channel, SearchResult
from .exceptions import YouTubeError
from . import utils

logger = logging.getLogger(__name__)


class YouTubeClient:
    """
    Main YouTube client combining all functionality.
    """
    
    def __init__(self, config: Optional[YouTubeConfig] = None):
        """
        Initialize YouTube client.
        
        Args:
            config: YouTube configuration (uses defaults if None)
        """
        self.config = config or YouTubeConfig()
        
        # Initialize auth
        self.auth = YouTubeAuth(
            cookies_file=self.config.auth.cookies_file,
            api_key=self.config.auth.api_key
        )
        
        # Get credentials for yt-dlp
        credentials = self.auth.get_credentials()
        self.ytdlp_opts = credentials.to_ytdlp_opts()
        
        # Initialize API clients
        self.search = YouTubeSearchAPI(
            config=self.config.search,
            ytdlp_opts=self.ytdlp_opts
        )
        
        self.video = YouTubeVideoAPI(
            api_key=credentials.api_key,
            ytdlp_opts=self.ytdlp_opts
        )
        
        self.download = YouTubeDownloadManager(
            config=self.config.download,
            ytdlp_opts=self.ytdlp_opts
        )
        
        self.playlist = YouTubePlaylistManager(
            config=self.config.playlist,
            api_key=credentials.api_key,
            oauth_token=credentials.oauth_token,
            ytdlp_opts=self.ytdlp_opts
        )
    
    @classmethod
    def from_env(cls) -> "YouTubeClient":
        """Create client from environment variables."""
        config = YouTubeConfig.from_env()
        return cls(config)
    
    # Search methods
    def search_music(self, query: str, limit: int = 10) -> List[Video]:
        """
        Search for music videos.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of music videos
        """
        return self.search.search_music(query, limit)
    
    def search_all(self, query: str, limit: int = 10) -> SearchResult:
        """
        Search for all content types.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            SearchResult with videos, playlists, and channels
        """
        return self.search.search(query, limit)
    
    def search_artist(self, artist: str) -> SearchResult:
        """
        Search for an artist's content.
        
        Args:
            artist: Artist name
            
        Returns:
            SearchResult with artist's content
        """
        return self.search.search_artist(artist)
    
    def search_album(self, artist: str, album: str) -> List[Video]:
        """
        Search for album tracks.
        
        Args:
            artist: Artist name
            album: Album name
            
        Returns:
            List of album tracks
        """
        return self.search.search_album(artist, album)
    
    # Video methods
    def get_video(self, video_id: str) -> Video:
        """
        Get video information.
        
        Args:
            video_id: YouTube video ID or URL
            
        Returns:
            Video object
        """
        # Extract ID if URL provided
        if video_id.startswith("http"):
            video_id = utils.extract_video_id(video_id) or video_id
        
        return self.video.get_video(video_id)
    
    def get_video_url(self, video_id: str, quality: str = "bestaudio") -> str:
        """
        Get direct stream URL.
        
        Args:
            video_id: Video ID
            quality: Quality selector
            
        Returns:
            Direct stream URL
        """
        return self.video.get_video_url(video_id, quality)
    
    # Download methods
    def download_audio(
        self,
        video_id: str,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Download audio from video.
        
        Args:
            video_id: Video ID or URL
            output_dir: Output directory (uses config default if None)
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded audio file
        """
        # Extract ID if URL provided
        if video_id.startswith("http"):
            url = video_id
            video_id = utils.extract_video_id(video_id)
        else:
            url = utils.build_video_url(video_id)
        
        # Override output directory if specified
        if output_dir:
            original_dir = self.download.config.output_dir
            self.download.config.output_dir = output_dir
            self.download._ensure_output_dir()
        
        try:
            return self.download.download_url(
                url,
                extract_audio=True,
                progress_callback=progress_callback
            )
        finally:
            if output_dir:
                self.download.config.output_dir = original_dir
    
    def download_video(
        self,
        video_id: str,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Download video.
        
        Args:
            video_id: Video ID or URL
            output_dir: Output directory
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded video file
        """
        # Extract ID if URL provided
        if video_id.startswith("http"):
            url = video_id
            video_id = utils.extract_video_id(video_id)
        else:
            url = utils.build_video_url(video_id)
        
        # Override output directory if specified
        if output_dir:
            original_dir = self.download.config.output_dir
            self.download.config.output_dir = output_dir
            self.download._ensure_output_dir()
        
        try:
            return self.download.download_url(
                url,
                extract_audio=False,
                progress_callback=progress_callback
            )
        finally:
            if output_dir:
                self.download.config.output_dir = original_dir
    
    def download_playlist(
        self,
        playlist_id: str,
        extract_audio: bool = True,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """
        Download playlist.
        
        Args:
            playlist_id: Playlist ID or URL
            extract_audio: Extract audio only
            output_dir: Output directory
            progress_callback: Progress callback function
            
        Returns:
            List of downloaded file paths
        """
        # Extract ID if URL provided
        if playlist_id.startswith("http"):
            playlist_id = utils.extract_playlist_id(playlist_id) or playlist_id
        
        # Override output directory if specified
        if output_dir:
            original_dir = self.download.config.output_dir
            self.download.config.output_dir = output_dir
            self.download._ensure_output_dir()
        
        try:
            return self.download.download_playlist(
                playlist_id,
                extract_audio=extract_audio,
                progress_callback=progress_callback
            )
        finally:
            if output_dir:
                self.download.config.output_dir = original_dir
    
    # Playlist methods
    def get_playlist(self, playlist_id: str) -> Playlist:
        """
        Get playlist information.
        
        Args:
            playlist_id: Playlist ID or URL
            
        Returns:
            Playlist object with videos
        """
        # Extract ID if URL provided
        if playlist_id.startswith("http"):
            playlist_id = utils.extract_playlist_id(playlist_id) or playlist_id
        
        return self.playlist.get_playlist(playlist_id)
    
    def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy: str = "private"
    ) -> str:
        """
        Create a new playlist.
        
        Args:
            title: Playlist title
            description: Playlist description
            privacy: Privacy status (private, unlisted, public)
            
        Returns:
            Playlist ID
            
        Note: Requires OAuth authentication
        """
        return self.playlist.create_playlist(title, description, privacy)
    
    def add_to_playlist(
        self,
        playlist_id: str,
        video_id: str,
        position: Optional[int] = None
    ) -> bool:
        """
        Add video to playlist.
        
        Args:
            playlist_id: Playlist ID
            video_id: Video ID to add
            position: Position in playlist
            
        Returns:
            True if successful
            
        Note: Requires OAuth authentication
        """
        # Extract IDs if URLs provided
        if playlist_id.startswith("http"):
            playlist_id = utils.extract_playlist_id(playlist_id) or playlist_id
        
        if video_id.startswith("http"):
            video_id = utils.extract_video_id(video_id) or video_id
        
        return self.playlist.add_video_to_playlist(playlist_id, video_id, position)
    
    def update_playlist(
        self,
        playlist_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy: Optional[str] = None
    ) -> bool:
        """
        Update playlist metadata.
        
        Args:
            playlist_id: Playlist ID
            title: New title
            description: New description
            privacy: New privacy status
            
        Returns:
            True if successful
            
        Note: Requires OAuth authentication
        """
        if playlist_id.startswith("http"):
            playlist_id = utils.extract_playlist_id(playlist_id) or playlist_id
        
        return self.playlist.update_playlist(playlist_id, title, description, privacy)
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            True if successful
            
        Note: Requires OAuth authentication
        """
        if playlist_id.startswith("http"):
            playlist_id = utils.extract_playlist_id(playlist_id) or playlist_id
        
        return self.playlist.delete_playlist(playlist_id)
    
    def get_user_playlists(self, channel_id: Optional[str] = None) -> List[Playlist]:
        """
        Get user's playlists.
        
        Args:
            channel_id: Channel ID (uses authenticated user if None)
            
        Returns:
            List of playlists
        """
        return self.playlist.get_user_playlists(channel_id)
    
    # Utility methods
    def parse_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Parse YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with type and ID
        """
        return utils.parse_youtube_url(url)
    
    def extract_music_metadata(self, video: Video) -> Dict[str, Any]:
        """
        Extract music metadata from video.
        
        Args:
            video: Video object
            
        Returns:
            Music metadata dictionary
        """
        return video.to_music_track()
    
    def authenticate(self) -> bool:
        """
        Check authentication status.
        
        Returns:
            True if authenticated
        """
        credentials = self.auth.get_credentials()
        if credentials.api_key and self.auth.validate_api_key():
            logger.info("Authenticated with API key")
            return True
        
        if credentials.cookies_file:
            if self.auth.load_cookies_from_browser():
                logger.info("Authenticated with cookies")
                return True
        
        logger.warning("No valid authentication found")
        return False


# Convenience functions for backward compatibility
def youtube_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for music on YouTube."""
    client = YouTubeClient.from_env()
    videos = client.search_music(query, limit)
    return [video.to_music_track() for video in videos]


def get_youtube_video_info(video_id: str) -> Optional[Dict[str, Any]]:
    """Get YouTube video information."""
    try:
        client = YouTubeClient.from_env()
        video = client.get_video(video_id)
        return video.to_music_track()
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None


def download_youtube_audio(url: str, output_dir: str = "./downloads") -> Optional[str]:
    """Download audio from YouTube video."""
    try:
        client = YouTubeClient.from_env()
        return client.download_audio(url, output_dir)
    except Exception as e:
        logger.error(f"Failed to download audio: {e}")
        return None


def get_youtube_playlist_videos(playlist_url: str) -> List[Dict[str, Any]]:
    """Get videos from YouTube playlist."""
    try:
        client = YouTubeClient.from_env()
        playlist = client.get_playlist(playlist_url)
        return [video.to_music_track() for video in playlist.videos]
    except Exception as e:
        logger.error(f"Failed to get playlist: {e}")
        return []


__all__ = [
    "YouTubeClient",
    "YouTubeConfig",
    "YouTubeAuth",
    "YouTubeSearchAPI",
    "YouTubeVideoAPI",
    "YouTubeDownloadManager",
    "YouTubePlaylistManager",
    "Video",
    "Playlist",
    "Channel",
    "SearchResult",
    "YouTubeError",
    "utils",
    # Backward compatibility functions
    "youtube_search",
    "get_youtube_video_info",
    "download_youtube_audio",
    "get_youtube_playlist_videos"
]