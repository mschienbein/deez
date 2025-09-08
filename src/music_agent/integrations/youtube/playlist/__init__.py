"""
YouTube playlist manager.
"""

import json
import logging
import subprocess
from typing import List, Dict, Any, Optional
import httpx

from ..config import PlaylistConfig
from ..models import Playlist, Video
from ..exceptions import (
    YouTubePlaylistError,
    YouTubeAPIError,
    YouTubeAuthError
)

logger = logging.getLogger(__name__)


class YouTubePlaylistManager:
    """Manage YouTube playlists (read and write)."""
    
    def __init__(
        self,
        config: PlaylistConfig,
        api_key: Optional[str] = None,
        oauth_token: Optional[str] = None,
        ytdlp_opts: Dict[str, Any] = None
    ):
        """Initialize playlist manager."""
        self.config = config
        self.api_key = api_key
        self.oauth_token = oauth_token
        self.ytdlp_opts = ytdlp_opts or {}
    
    def get_playlist(self, playlist_id: str) -> Playlist:
        """
        Get playlist information and videos.
        
        Args:
            playlist_id: YouTube playlist ID
            
        Returns:
            Playlist object with videos
        """
        try:
            url = f"https://www.youtube.com/playlist?list={playlist_id}"
            
            cmd = [
                "yt-dlp", url,
                "--dump-json",
                "--no-download",
                "--flat-playlist"
            ]
            
            # Add playlist range options
            if self.config.start_index:
                cmd.extend(["--playlist-start", str(self.config.start_index)])
            
            if self.config.end_index:
                cmd.extend(["--playlist-end", str(self.config.end_index)])
            elif self.config.max_items:
                cmd.extend(["--playlist-end", str(self.config.max_items)])
            
            if self.config.reverse_order:
                cmd.append("--playlist-reverse")
            
            # Add date filters
            if self.config.date_after:
                cmd.extend(["--dateafter", self.config.date_after])
            
            if self.config.date_before:
                cmd.extend(["--datebefore", self.config.date_before])
            
            # Add authentication
            if self.ytdlp_opts.get("cookiefile"):
                cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise YouTubePlaylistError(
                    f"Failed to get playlist: {result.stderr}",
                    playlist_id=playlist_id
                )
            
            # Parse playlist data
            lines = result.stdout.strip().split('\n')
            entries = []
            playlist_info = None
            
            for line in lines:
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("_type") == "playlist":
                            playlist_info = data
                        else:
                            entries.append(data)
                    except json.JSONDecodeError:
                        continue
            
            # Build playlist object
            if playlist_info:
                playlist_info["entries"] = entries
                return Playlist.from_ytdlp(playlist_info)
            
            # Fallback: create playlist from entries
            playlist = Playlist(
                id=playlist_id,
                title=f"Playlist {playlist_id}",
                description="",
                channel_id="",
                channel_title="",
                video_count=len(entries)
            )
            
            for entry in entries:
                playlist.videos.append(Video.from_ytdlp(entry))
            
            return playlist
            
        except Exception as e:
            if isinstance(e, YouTubePlaylistError):
                raise
            raise YouTubePlaylistError(
                f"Failed to get playlist: {str(e)}",
                playlist_id=playlist_id
            )
    
    def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy: str = "private"
    ) -> str:
        """
        Create a new YouTube playlist.
        
        Args:
            title: Playlist title
            description: Playlist description
            privacy: Privacy status (private, unlisted, public)
            
        Returns:
            Playlist ID
            
        Note: Requires OAuth authentication
        """
        if not self.oauth_token:
            raise YouTubeAuthError("OAuth token required to create playlists")
        
        url = "https://www.googleapis.com/youtube/v3/playlists"
        
        headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "snippet": {
                "title": title,
                "description": description
            },
            "status": {
                "privacyStatus": privacy
            }
        }
        
        params = {
            "part": "snippet,status"
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    headers=headers,
                    params=params,
                    json=data
                )
                
                if response.status_code == 401:
                    raise YouTubeAuthError("Invalid or expired OAuth token")
                
                if response.status_code != 200:
                    raise YouTubeAPIError(
                        f"Failed to create playlist: {response.status_code}",
                        status_code=response.status_code,
                        response_data=response.json()
                    )
                
                result = response.json()
                return result["id"]
                
        except httpx.RequestError as e:
            raise YouTubePlaylistError(f"Request failed: {str(e)}")
    
    def add_video_to_playlist(
        self,
        playlist_id: str,
        video_id: str,
        position: Optional[int] = None
    ) -> bool:
        """
        Add a video to a playlist.
        
        Args:
            playlist_id: Playlist ID
            video_id: Video ID to add
            position: Position in playlist (optional)
            
        Returns:
            True if successful
            
        Note: Requires OAuth authentication
        """
        if not self.oauth_token:
            raise YouTubeAuthError("OAuth token required to modify playlists")
        
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        
        headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        
        if position is not None:
            data["snippet"]["position"] = position
        
        params = {
            "part": "snippet"
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    headers=headers,
                    params=params,
                    json=data
                )
                
                if response.status_code == 401:
                    raise YouTubeAuthError("Invalid or expired OAuth token")
                
                if response.status_code != 200:
                    raise YouTubeAPIError(
                        f"Failed to add video to playlist: {response.status_code}",
                        status_code=response.status_code,
                        response_data=response.json()
                    )
                
                return True
                
        except httpx.RequestError as e:
            raise YouTubePlaylistError(
                f"Request failed: {str(e)}",
                playlist_id=playlist_id
            )
    
    def remove_video_from_playlist(
        self,
        playlist_id: str,
        playlist_item_id: str
    ) -> bool:
        """
        Remove a video from a playlist.
        
        Args:
            playlist_id: Playlist ID
            playlist_item_id: Playlist item ID (not video ID)
            
        Returns:
            True if successful
            
        Note: Requires OAuth authentication
        """
        if not self.oauth_token:
            raise YouTubeAuthError("OAuth token required to modify playlists")
        
        url = f"https://www.googleapis.com/youtube/v3/playlistItems"
        
        headers = {
            "Authorization": f"Bearer {self.oauth_token}"
        }
        
        params = {
            "id": playlist_item_id
        }
        
        try:
            with httpx.Client() as client:
                response = client.delete(
                    url,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 401:
                    raise YouTubeAuthError("Invalid or expired OAuth token")
                
                if response.status_code not in [200, 204]:
                    raise YouTubeAPIError(
                        f"Failed to remove video from playlist: {response.status_code}",
                        status_code=response.status_code
                    )
                
                return True
                
        except httpx.RequestError as e:
            raise YouTubePlaylistError(
                f"Request failed: {str(e)}",
                playlist_id=playlist_id
            )
    
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
        if not self.oauth_token:
            raise YouTubeAuthError("OAuth token required to modify playlists")
        
        # First, get current playlist data
        playlist = self.get_playlist(playlist_id)
        
        url = f"https://www.googleapis.com/youtube/v3/playlists"
        
        headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "id": playlist_id,
            "snippet": {
                "title": title or playlist.title,
                "description": description or playlist.description
            }
        }
        
        parts = ["snippet"]
        
        if privacy:
            data["status"] = {"privacyStatus": privacy}
            parts.append("status")
        
        params = {
            "part": ",".join(parts)
        }
        
        try:
            with httpx.Client() as client:
                response = client.put(
                    url,
                    headers=headers,
                    params=params,
                    json=data
                )
                
                if response.status_code == 401:
                    raise YouTubeAuthError("Invalid or expired OAuth token")
                
                if response.status_code != 200:
                    raise YouTubeAPIError(
                        f"Failed to update playlist: {response.status_code}",
                        status_code=response.status_code,
                        response_data=response.json()
                    )
                
                return True
                
        except httpx.RequestError as e:
            raise YouTubePlaylistError(
                f"Request failed: {str(e)}",
                playlist_id=playlist_id
            )
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            True if successful
            
        Note: Requires OAuth authentication
        """
        if not self.oauth_token:
            raise YouTubeAuthError("OAuth token required to delete playlists")
        
        url = f"https://www.googleapis.com/youtube/v3/playlists"
        
        headers = {
            "Authorization": f"Bearer {self.oauth_token}"
        }
        
        params = {
            "id": playlist_id
        }
        
        try:
            with httpx.Client() as client:
                response = client.delete(
                    url,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 401:
                    raise YouTubeAuthError("Invalid or expired OAuth token")
                
                if response.status_code not in [200, 204]:
                    raise YouTubeAPIError(
                        f"Failed to delete playlist: {response.status_code}",
                        status_code=response.status_code
                    )
                
                return True
                
        except httpx.RequestError as e:
            raise YouTubePlaylistError(
                f"Request failed: {str(e)}",
                playlist_id=playlist_id
            )
    
    def get_user_playlists(self, channel_id: Optional[str] = None) -> List[Playlist]:
        """
        Get playlists for a user/channel.
        
        Args:
            channel_id: Channel ID (uses authenticated user if None)
            
        Returns:
            List of Playlist objects
            
        Note: May require authentication for private playlists
        """
        if not channel_id and not self.oauth_token:
            raise YouTubeAuthError("OAuth token or channel ID required")
        
        if self.api_key:
            return self._get_playlists_via_api(channel_id)
        else:
            return self._get_playlists_via_ytdlp(channel_id)
    
    def _get_playlists_via_api(self, channel_id: Optional[str]) -> List[Playlist]:
        """Get playlists using YouTube Data API."""
        url = "https://www.googleapis.com/youtube/v3/playlists"
        
        params = {
            "part": "snippet,contentDetails",
            "maxResults": 50
        }
        
        if self.oauth_token:
            params["mine"] = "true" if not channel_id else None
            headers = {"Authorization": f"Bearer {self.oauth_token}"}
        else:
            params["key"] = self.api_key
            headers = {}
        
        if channel_id:
            params["channelId"] = channel_id
        
        playlists = []
        
        try:
            with httpx.Client() as client:
                while True:
                    response = client.get(url, headers=headers, params=params)
                    
                    if response.status_code != 200:
                        raise YouTubeAPIError(
                            f"Failed to get playlists: {response.status_code}",
                            status_code=response.status_code
                        )
                    
                    data = response.json()
                    
                    for item in data.get("items", []):
                        playlists.append(Playlist.from_api(item))
                    
                    # Check for next page
                    next_token = data.get("nextPageToken")
                    if not next_token:
                        break
                    
                    params["pageToken"] = next_token
                
        except httpx.RequestError as e:
            raise YouTubePlaylistError(f"Request failed: {str(e)}")
        
        return playlists
    
    def _get_playlists_via_ytdlp(self, channel_id: Optional[str]) -> List[Playlist]:
        """Get playlists using yt-dlp."""
        if not channel_id:
            raise YouTubePlaylistError("Channel ID required for yt-dlp method")
        
        url = f"https://www.youtube.com/channel/{channel_id}/playlists"
        
        cmd = [
            "yt-dlp", url,
            "--dump-json",
            "--no-download",
            "--flat-playlist"
        ]
        
        if self.ytdlp_opts.get("cookiefile"):
            cmd.extend(["--cookies", self.ytdlp_opts["cookiefile"]])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise YouTubePlaylistError(f"Failed to get playlists: {result.stderr}")
            
            playlists = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("_type") == "playlist":
                            playlists.append(Playlist.from_ytdlp(data))
                    except json.JSONDecodeError:
                        continue
            
            return playlists
            
        except Exception as e:
            raise YouTubePlaylistError(f"Failed to get playlists: {str(e)}")