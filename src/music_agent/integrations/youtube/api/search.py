"""
YouTube search API implementation.
"""

import json
import logging
import subprocess
from typing import List, Dict, Any, Optional
from ..models import Video, Playlist, Channel, SearchResult
from ..exceptions import YouTubeSearchError
from ..config import SearchConfig

logger = logging.getLogger(__name__)


class YouTubeSearchAPI:
    """YouTube search functionality."""
    
    def __init__(self, config: SearchConfig, ytdlp_opts: Dict[str, Any] = None):
        """Initialize search API."""
        self.config = config
        self.ytdlp_opts = ytdlp_opts or {}
    
    def search(
        self,
        query: str,
        limit: int = None,
        filter_type: Optional[str] = None
    ) -> SearchResult:
        """
        Search YouTube for videos, playlists, or channels.
        
        Args:
            query: Search query
            limit: Maximum results (default from config)
            filter_type: Filter by type (video, playlist, channel)
            
        Returns:
            SearchResult containing videos, playlists, and channels
        """
        limit = limit or self.config.default_limit
        
        try:
            search_prefix = f"ytsearch{limit}:{query}"
            
            cmd = ["yt-dlp", search_prefix, "--dump-json", "--no-download", "--flat-playlist"]
            
            # Add authentication options
            if self.ytdlp_opts.get("cookiefile"):
                cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
            
            # Add region and language
            if self.config.region_code:
                cmd.extend(["--geo-bypass-country", self.config.region_code])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.search_timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Search failed: {result.stderr}")
                raise YouTubeSearchError(f"Search failed: {result.stderr}")
            
            entries = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Filter by type if specified
            if filter_type:
                entries = self._filter_by_type(entries, filter_type)
            
            return SearchResult.from_ytdlp(entries)
            
        except subprocess.TimeoutExpired:
            raise YouTubeSearchError("Search timed out")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise YouTubeSearchError(f"Search failed: {str(e)}")
    
    def search_music(self, query: str, limit: int = None) -> List[Video]:
        """
        Search specifically for music videos.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of Video objects
        """
        # Add music-specific search terms if not present
        music_terms = ["official video", "official audio", "music video", "audio"]
        has_music_term = any(term in query.lower() for term in music_terms)
        
        if not has_music_term:
            query = f"{query} official"
        
        result = self.search(query, limit, filter_type="video")
        
        # Filter to likely music videos
        music_videos = []
        for video in result.videos:
            if self._is_likely_music(video):
                music_videos.append(video)
        
        return music_videos
    
    def search_artist(self, artist: str) -> SearchResult:
        """
        Search for an artist's content.
        
        Args:
            artist: Artist name
            
        Returns:
            SearchResult with artist's videos, playlists, and channel
        """
        # Search for artist channel and content
        query = f"{artist} artist"
        result = self.search(query, limit=self.config.max_results)
        
        # Try to find official artist channel
        for channel in result.channels:
            if self._is_official_artist(channel, artist):
                # Get more content from this channel
                channel_videos = self.get_channel_videos(channel.id)
                result.videos.extend(channel_videos)
                break
        
        return result
    
    def search_album(self, artist: str, album: str) -> List[Video]:
        """
        Search for album tracks.
        
        Args:
            artist: Artist name
            album: Album name
            
        Returns:
            List of videos from the album
        """
        query = f"{artist} {album} full album playlist"
        result = self.search(query, limit=20)
        
        # Look for playlists first
        for playlist in result.playlists:
            if album.lower() in playlist.title.lower():
                # Get playlist videos
                from ..playlist import YouTubePlaylistManager
                from ..config import PlaylistConfig
                playlist_api = YouTubePlaylistManager(PlaylistConfig(), ytdlp_opts=self.ytdlp_opts)
                full_playlist = playlist_api.get_playlist(playlist.id)
                return full_playlist.videos
        
        # Fall back to individual tracks
        return result.videos
    
    def get_channel_videos(self, channel_id: str, limit: int = 50) -> List[Video]:
        """
        Get videos from a channel.
        
        Args:
            channel_id: YouTube channel ID
            limit: Maximum videos to retrieve
            
        Returns:
            List of videos from the channel
        """
        try:
            url = f"https://www.youtube.com/channel/{channel_id}/videos"
            
            cmd = [
                "yt-dlp", url,
                "--dump-json",
                "--no-download",
                "--flat-playlist",
                "--playlist-end", str(limit)
            ]
            
            if self.ytdlp_opts.get("cookiefile"):
                cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get channel videos: {result.stderr}")
                return []
            
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        entry = json.loads(line)
                        videos.append(Video.from_ytdlp(entry))
                    except json.JSONDecodeError:
                        continue
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []
    
    def _filter_by_type(self, entries: List[Dict], filter_type: str) -> List[Dict]:
        """Filter search results by type."""
        filtered = []
        
        for entry in entries:
            entry_type = entry.get("_type", "video")
            
            if filter_type == "video" and entry_type != "playlist":
                filtered.append(entry)
            elif filter_type == "playlist" and entry_type == "playlist":
                filtered.append(entry)
            elif filter_type == "channel" and entry.get("channel_id"):
                # Check if this is a channel result
                if entry.get("uploader_id") == entry.get("id"):
                    filtered.append(entry)
        
        return filtered
    
    def _is_likely_music(self, video: Video) -> bool:
        """Check if a video is likely music content."""
        music_indicators = [
            "official video", "official audio", "music video",
            "audio", "lyrics", "album", "single", "ep",
            "records", "entertainment", "vevo"
        ]
        
        title_lower = video.title.lower()
        channel_lower = video.channel_title.lower()
        
        # Check title and channel for music indicators
        for indicator in music_indicators:
            if indicator in title_lower or indicator in channel_lower:
                return True
        
        # Check if it's from a music label or VEVO channel
        music_channels = ["vevo", "records", "music", "entertainment"]
        for channel_indicator in music_channels:
            if channel_indicator in channel_lower:
                return True
        
        # Check duration (most music is 2-6 minutes)
        if 120 <= video.duration <= 360:
            return True
        
        return False
    
    def _is_official_artist(self, channel: Channel, artist: str) -> bool:
        """Check if a channel is the official artist channel."""
        artist_lower = artist.lower()
        channel_title_lower = channel.title.lower()
        
        # Direct match
        if artist_lower == channel_title_lower:
            return True
        
        # Official or VEVO channel
        if artist_lower in channel_title_lower:
            if "official" in channel_title_lower or "vevo" in channel_title_lower:
                return True
        
        # Check for music/topic channels
        if f"{artist_lower} - topic" == channel_title_lower:
            return True
        
        return False