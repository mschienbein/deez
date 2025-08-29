"""Spotify integration based on deezer-downloader patterns."""

import logging
import re
from typing import Any, Dict, List, Optional

import pyotp
import requests
from bs4 import BeautifulSoup

from ..utils.config import config

logger = logging.getLogger(__name__)


class SpotifyIntegration:
    """Spotify integration for music discovery."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, totp_secret: Optional[str] = None):
        """Initialize Spotify integration."""
        self.username = username or config.spotify.username
        self.password = password or config.spotify.password
        self.totp_secret = totp_secret or config.spotify.totp_secret
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        self.access_token = None
        self.client_id = None
        self.csrf_token = None
        
        if self.username and self.password:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Spotify using web login."""
        try:
            # Get login page
            login_url = "https://accounts.spotify.com/login"
            response = self.session.get(login_url)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract CSRF token
            csrf_input = soup.find("input", {"name": "csrf_token"})
            if csrf_input:
                self.csrf_token = csrf_input.get("value")
            
            # Login
            login_data = {
                "username": self.username,
                "password": self.password,
                "csrf_token": self.csrf_token,
                "remember": "true"
            }
            
            login_response = self.session.post(
                "https://accounts.spotify.com/api/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # Handle 2FA if required
            if login_response.status_code == 200:
                response_data = login_response.json()
                if response_data.get("status") == 101:  # 2FA required
                    if self.totp_secret:
                        totp = pyotp.TOTP(self.totp_secret)
                        twofa_code = totp.now()
                        
                        twofa_data = {
                            "twofa_code": twofa_code,
                            "csrf_token": self.csrf_token,
                            "remember_device": "true"
                        }
                        
                        twofa_response = self.session.post(
                            "https://accounts.spotify.com/api/login/twofa",
                            data=twofa_data
                        )
                        
                        if twofa_response.status_code != 200:
                            logger.error("2FA authentication failed")
                            return False
                    else:
                        logger.error("2FA required but no TOTP secret provided")
                        return False
            
            # Get access token from web player
            web_player_response = self.session.get("https://open.spotify.com/")
            
            # Extract access token from page
            token_match = re.search(r'"accessToken":"([^"]+)"', web_player_response.text)
            if token_match:
                self.access_token = token_match.group(1)
                
            # Extract client ID
            client_id_match = re.search(r'"clientId":"([^"]+)"', web_player_response.text)
            if client_id_match:
                self.client_id = client_id_match.group(1)
            
            if self.access_token and self.client_id:
                logger.info("Spotify authentication successful")
                return True
            else:
                logger.error("Failed to extract tokens from Spotify")
                return False
                
        except Exception as e:
            logger.error(f"Spotify authentication failed: {e}")
            return False
    
    def _api_call(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API call to Spotify Web API."""
        if not self.access_token:
            logger.error("No access token available")
            return {}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.spotify.com/v1/{endpoint}"
        
        try:
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API call failed: {e}")
            return {}
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for music on Spotify."""
        try:
            params = {
                "q": query,
                "type": "track",
                "limit": limit,
                "market": "US"
            }
            
            response = self._api_call("search", params)
            
            results = []
            if response.get("tracks") and response["tracks"].get("items"):
                for track in response["tracks"]["items"]:
                    track_info = self._format_track_info(track)
                    results.append(track_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Spotify search failed: {e}")
            return []
    
    def get_track_info(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed track information."""
        try:
            response = self._api_call(f"tracks/{track_id}")
            
            if response:
                return self._format_track_info(response)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get track info {track_id}: {e}")
            return None
    
    def get_album_tracks(self, album_id: str) -> List[Dict[str, Any]]:
        """Get tracks from an album."""
        try:
            response = self._api_call(f"albums/{album_id}/tracks", {"limit": 50})
            
            tracks = []
            if response.get("items"):
                for track in response["items"]:
                    # Get full track info (album tracks are simplified)
                    full_track = self.get_track_info(track["id"])
                    if full_track:
                        tracks.append(full_track)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get album tracks {album_id}: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get tracks from a playlist."""
        try:
            response = self._api_call(f"playlists/{playlist_id}/tracks", {"limit": 100})
            
            tracks = []
            if response.get("items"):
                for item in response["items"]:
                    if item.get("track"):
                        track_info = self._format_track_info(item["track"])
                        tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get playlist tracks {playlist_id}: {e}")
            return []
    
    def get_user_saved_tracks(self) -> List[Dict[str, Any]]:
        """Get user's saved tracks."""
        if not self.access_token:
            logger.error("User not authenticated")
            return []
        
        try:
            response = self._api_call("me/tracks", {"limit": 50})
            
            tracks = []
            if response.get("items"):
                for item in response["items"]:
                    if item.get("track"):
                        track_info = self._format_track_info(item["track"])
                        tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get user saved tracks: {e}")
            return []
    
    def get_recommendations(
        self,
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        seed_genres: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on seeds."""
        try:
            params = {"limit": limit}
            
            if seed_tracks:
                params["seed_tracks"] = ",".join(seed_tracks[:5])  # Max 5
            if seed_artists:
                params["seed_artists"] = ",".join(seed_artists[:5])  # Max 5
            if seed_genres:
                params["seed_genres"] = ",".join(seed_genres[:5])  # Max 5
            
            response = self._api_call("recommendations", params)
            
            tracks = []
            if response.get("tracks"):
                for track in response["tracks"]:
                    track_info = self._format_track_info(track)
                    tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []
    
    def parse_spotify_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse Spotify URL to extract type and ID."""
        patterns = {
            "track": r"spotify\.com/track/([a-zA-Z0-9]+)",
            "album": r"spotify\.com/album/([a-zA-Z0-9]+)",
            "playlist": r"spotify\.com/playlist/([a-zA-Z0-9]+)",
            "artist": r"spotify\.com/artist/([a-zA-Z0-9]+)",
        }
        
        for media_type, pattern in patterns.items():
            match = re.search(pattern, url)
            if match:
                return {
                    "type": media_type,
                    "id": match.group(1)
                }
        
        # Also handle spotify: URIs
        uri_pattern = r"spotify:(\w+):([a-zA-Z0-9]+)"
        match = re.search(uri_pattern, url)
        if match:
            return {
                "type": match.group(1),
                "id": match.group(2)
            }
        
        return None
    
    def _format_track_info(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format track data to standardized format."""
        artists = [artist["name"] for artist in track_data.get("artists", [])]
        
        return {
            "id": track_data.get("id", ""),
            "title": track_data.get("name", ""),
            "artist": ", ".join(artists),
            "album": track_data.get("album", {}).get("name", ""),
            "duration": int(track_data.get("duration_ms", 0) / 1000),  # Convert to seconds
            "track_number": track_data.get("track_number", 0),
            "disc_number": track_data.get("disc_number", 1),
            "release_date": track_data.get("album", {}).get("release_date", ""),
            "isrc": track_data.get("external_ids", {}).get("isrc", ""),
            "explicit": track_data.get("explicit", False),
            "preview_url": track_data.get("preview_url", ""),
            "cover_art": self._get_cover_url(track_data.get("album", {})),
            "popularity": track_data.get("popularity", 0),
            "platform": "spotify",
            "platform_url": track_data.get("external_urls", {}).get("spotify", ""),
            "available": track_data.get("is_playable", True),
        }
    
    def _get_cover_url(self, album_data: Dict[str, Any]) -> str:
        """Get cover art URL."""
        images = album_data.get("images", [])
        if images:
            # Return the largest image
            return images[0].get("url", "")
        return ""


# Convenience functions for use with Strands tools
def get_songs_from_spotify_website(url: str) -> List[Dict[str, Any]]:
    """Get songs from Spotify URL."""
    spotify = SpotifyIntegration()
    url_info = spotify.parse_spotify_url(url)
    
    if not url_info:
        return []
    
    if url_info["type"] == "track":
        track = spotify.get_track_info(url_info["id"])
        return [track] if track else []
    elif url_info["type"] == "playlist":
        return spotify.get_playlist_tracks(url_info["id"])
    elif url_info["type"] == "album":
        return spotify.get_album_tracks(url_info["id"])
    
    return []


def parse_track(track_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse track data to standardized format."""
    spotify = SpotifyIntegration()
    return spotify._format_track_info(track_data)


def spotify_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for music on Spotify."""
    spotify = SpotifyIntegration()
    return spotify.search(query, limit)