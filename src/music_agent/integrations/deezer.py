"""Deezer integration based on deezer-downloader APIs."""

import logging
import re
from typing import Any, Dict, List, Optional

import requests

from ..utils.config import config

logger = logging.getLogger(__name__)


class DeezerIntegration:
    """Deezer API integration for music discovery and download."""
    
    def __init__(self, arl: Optional[str] = None):
        """Initialize Deezer integration."""
        self.arl = arl or config.deezer.arl
        self.session = requests.Session()
        self.api_base = "https://www.deezer.com/ajax/gw-light.php"
        self.csrf_token = None
        self.user_id = None
        self.license_token = None
        
        if self.arl:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate using ARL cookie."""
        try:
            # Set ARL cookie
            self.session.cookies.set("arl", self.arl, domain=".deezer.com")
            
            # Get user info to validate authentication
            response = self._api_call("deezer.getUserData")
            if response.get("results"):
                user_data = response["results"]
                self.user_id = user_data.get("USER", {}).get("USER_ID")
                self.csrf_token = user_data.get("checkForm")
                logger.info(f"Authenticated as Deezer user {self.user_id}")
                return True
            else:
                logger.error("Invalid ARL cookie")
                return False
                
        except Exception as e:
            logger.error(f"Deezer authentication failed: {e}")
            return False
    
    def _api_call(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API call to Deezer gateway."""
        api_token = "null"  # Default for unauthenticated calls
        
        if self.csrf_token:
            api_token = self.csrf_token
        
        url = f"{self.api_base}?method={method}&input=3&api_version=1.0&api_token={api_token}"
        
        response = self.session.post(url, json=params or {})
        response.raise_for_status()
        
        return response.json()
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for music on Deezer."""
        try:
            # Search tracks
            response = self._api_call("search.music", {
                "query": query,
                "start": 0,
                "nb": limit,
                "suggest": True,
                "artist_suggest": True,
                "top_tracks": True,
            })
            
            results = []
            if response.get("results") and response["results"].get("data"):
                for item in response["results"]["data"]:
                    if item.get("__TYPE__") == "song":
                        track_info = self._format_track_info(item)
                        results.append(track_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Deezer search failed: {e}")
            return []
    
    def get_track_info(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed track information."""
        try:
            response = self._api_call("song.getListData", {
                "sng_ids": [int(track_id)]
            })
            
            if response.get("results") and response["results"].get("data"):
                track_data = response["results"]["data"][0]
                return self._format_track_info(track_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get track info {track_id}: {e}")
            return None
    
    def get_album_tracks(self, album_id: str) -> List[Dict[str, Any]]:
        """Get tracks from an album."""
        try:
            response = self._api_call("album.getSongs", {
                "alb_id": album_id,
                "start": 0,
                "nb": 500,
            })
            
            tracks = []
            if response.get("results") and response["results"].get("data"):
                for track in response["results"]["data"]:
                    track_info = self._format_track_info(track)
                    tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get album tracks {album_id}: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get tracks from a playlist."""
        try:
            response = self._api_call("playlist.getSongs", {
                "playlist_id": playlist_id,
                "start": 0,
                "nb": 2000,
            })
            
            tracks = []
            if response.get("results") and response["results"].get("data"):
                for track in response["results"]["data"]:
                    track_info = self._format_track_info(track)
                    tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get playlist tracks {playlist_id}: {e}")
            return []
    
    def get_user_favorites(self) -> List[Dict[str, Any]]:
        """Get user's favorite tracks."""
        if not self.user_id:
            logger.error("User not authenticated")
            return []
        
        try:
            response = self._api_call("song.getFavorites", {
                "user_id": self.user_id,
                "start": 0,
                "nb": 2000,
            })
            
            tracks = []
            if response.get("results") and response["results"].get("data"):
                for track in response["results"]["data"]:
                    track_info = self._format_track_info(track)
                    tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get user favorites: {e}")
            return []
    
    def parse_deezer_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Deezer URL to extract type and ID."""
        patterns = {
            "track": r"deezer\.com/.*?/track/(\d+)",
            "album": r"deezer\.com/.*?/album/(\d+)",
            "playlist": r"deezer\.com/.*?/playlist/(\d+)",
            "artist": r"deezer\.com/.*?/artist/(\d+)",
        }
        
        for media_type, pattern in patterns.items():
            match = re.search(pattern, url)
            if match:
                return {
                    "type": media_type,
                    "id": match.group(1)
                }
        
        return None
    
    def get_download_url(self, track_id: str, quality: str = "MP3_320") -> Optional[str]:
        """Get download URL for a track."""
        if not self.arl:
            logger.error("ARL required for download URLs")
            return None
        
        try:
            # Get track token
            response = self._api_call("song.getListData", {
                "sng_ids": [int(track_id)]
            })
            
            if not response.get("results") or not response["results"].get("data"):
                return None
            
            track_data = response["results"]["data"][0]
            track_token = track_data.get("TRACK_TOKEN")
            
            if not track_token:
                return None
            
            # Get download URL
            url_response = self._api_call("song.getDownloadUrl", {
                "license_token": self.license_token,
                "media": [{
                    "type": "FULL",
                    "formats": [{"cipher": "BF_CBC_STRIPE", "format": quality}]
                }],
                "track_tokens": [track_token]
            })
            
            if url_response.get("results") and url_response["results"].get("data"):
                return url_response["results"]["data"][0].get("media", [{}])[0].get("sources", [{}])[0].get("url")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get download URL for {track_id}: {e}")
            return None
    
    def _format_track_info(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format track data to standardized format."""
        return {
            "id": str(track_data.get("SNG_ID", "")),
            "title": track_data.get("SNG_TITLE", ""),
            "artist": track_data.get("ART_NAME", ""),
            "album": track_data.get("ALB_TITLE", ""),
            "duration": int(track_data.get("DURATION", 0)),
            "track_number": int(track_data.get("TRACK_NUMBER", 0)),
            "disc_number": int(track_data.get("DISK_NUMBER", 1)),
            "release_date": track_data.get("PHYSICAL_RELEASE_DATE", ""),
            "isrc": track_data.get("ISRC", ""),
            "explicit": bool(track_data.get("EXPLICIT_LYRICS", 0)),
            "preview_url": f"https://cdns-preview-{track_data.get('MD5_ORIGIN', '')[:1]}.dzcdn.net/stream/c-{track_data.get('MD5_ORIGIN', '')}-{track_data.get('MEDIA_VERSION', '1')}.mp3",
            "cover_art": self._get_cover_url(track_data.get("ALB_PICTURE", "")),
            "platform": "deezer",
            "platform_url": f"https://deezer.com/track/{track_data.get('SNG_ID', '')}",
            "available": not bool(track_data.get("RIGHTS", {}).get("STREAM_ADS_AVAILABLE") == False),
        }
    
    def _get_cover_url(self, picture_id: str, size: str = "500x500") -> str:
        """Get cover art URL."""
        if not picture_id:
            return ""
        return f"https://e-cdns-images.dzcdn.net/images/cover/{picture_id}/{size}-000000-80-0-0.jpg"


# Convenience functions for use with Strands tools
def deezer_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for music on Deezer."""
    deezer = DeezerIntegration()
    return deezer.search(query, limit)


def get_song_infos_from_deezer_website(track_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed track information from Deezer."""
    deezer = DeezerIntegration()
    return deezer.get_track_info(track_id)


def parse_deezer_playlist(playlist_url: str) -> List[Dict[str, Any]]:
    """Parse Deezer playlist and return tracks."""
    deezer = DeezerIntegration()
    url_info = deezer.parse_deezer_url(playlist_url)
    
    if not url_info:
        return []
    
    if url_info["type"] == "playlist":
        return deezer.get_playlist_tracks(url_info["id"])
    elif url_info["type"] == "album":
        return deezer.get_album_tracks(url_info["id"])
    
    return []


def get_deezer_favorites() -> List[Dict[str, Any]]:
    """Get user's Deezer favorites."""
    deezer = DeezerIntegration()
    return deezer.get_user_favorites()