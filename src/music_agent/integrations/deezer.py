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
        self.sound_quality = None  # Will be set based on user subscription
        self.prefer_flac = True  # Default to preferring FLAC when available
        
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
                # Get license token and sound quality from user options
                options = user_data.get("USER", {}).get("OPTIONS", {})
                self.license_token = options.get("license_token")
                
                # Check if user has FLAC support (lossless subscription)
                web_sound_quality = options.get("web_sound_quality", {})
                self.has_flac = web_sound_quality.get("lossless", False)
                
                # Set preferred quality
                if self.has_flac and self.prefer_flac:
                    self.sound_quality = "FLAC"
                elif self.has_flac or web_sound_quality.get("high", False):
                    self.sound_quality = "MP3_320"
                else:
                    self.sound_quality = "MP3_128"
                
                logger.info(f"Authenticated as Deezer user {self.user_id} with {self.sound_quality} quality")
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
        """Search for music on Deezer using public API."""
        try:
            # Use public Deezer API for search (more reliable)
            import urllib.parse
            search_query = urllib.parse.quote_plus(query)
            url = f"https://api.deezer.com/search/track?q={search_query}&limit={limit}"
            
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if data.get("data"):
                for item in data["data"]:
                    # Format the public API response
                    track_info = {
                        "id": str(item.get("id", "")),
                        "title": item.get("title", ""),
                        "artist": item.get("artist", {}).get("name", ""),
                        "album": item.get("album", {}).get("title", ""),
                        "duration": item.get("duration", 0),
                        "track_number": item.get("track_position", 0),
                        "disc_number": item.get("disk_number", 1),
                        "release_date": "",  # Not in public API response
                        "isrc": "",  # Not in public API response
                        "explicit": bool(item.get("explicit_lyrics", False)),
                        "preview_url": item.get("preview", ""),
                        "cover_art": item.get("album", {}).get("cover_medium", ""),
                        "platform": "deezer",
                        "platform_url": item.get("link", f"https://deezer.com/track/{item.get('id', '')}"),
                        "available": True,
                    }
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
    
    def download_track(self, track_id: str, output_path: str, quality: Optional[str] = None) -> bool:
        """Download and decrypt a track from Deezer.
        
        Args:
            track_id: Deezer track ID
            output_path: Path to save the downloaded file
            quality: Override quality (FLAC, MP3_320, MP3_128)
        
        Returns:
            True if download successful, False otherwise
        """
        if not self.arl:
            logger.error("ARL required for downloads")
            return False
        
        if not self.license_token:
            logger.error("License token not available")
            return False
        
        try:
            # Import crypto utilities
            from ..utils.crypto import calculate_blowfish_key, decrypt_track_stream
            
            # Use specified quality or default
            use_quality = quality or self.sound_quality
            
            # Get track data
            response = self._api_call("song.getListData", {
                "sng_ids": [int(track_id)]
            })
            
            if not response.get("results") or not response["results"].get("data"):
                logger.error(f"No track data found for ID {track_id}")
                return False
            
            track_data = response["results"]["data"][0]
            track_token = track_data.get("TRACK_TOKEN")
            
            if not track_token:
                logger.error(f"No track token found for ID {track_id}")
                return False
            
            # Check available formats in track data
            available_formats = []
            if track_data.get("FILESIZE_FLAC") and int(track_data["FILESIZE_FLAC"]) > 0:
                available_formats.append("FLAC")
            if track_data.get("FILESIZE_MP3_320") and int(track_data["FILESIZE_MP3_320"]) > 0:
                available_formats.append("MP3_320")
            if track_data.get("FILESIZE_MP3_256") and int(track_data["FILESIZE_MP3_256"]) > 0:
                available_formats.append("MP3_256")
            if track_data.get("FILESIZE_MP3_128") and int(track_data["FILESIZE_MP3_128"]) > 0:
                available_formats.append("MP3_128")
            
            # Determine best available quality
            if use_quality not in available_formats:
                # Fallback to best available
                if "FLAC" in available_formats:
                    use_quality = "FLAC"
                elif "MP3_320" in available_formats:
                    use_quality = "MP3_320"
                elif "MP3_256" in available_formats:
                    use_quality = "MP3_256"
                elif "MP3_128" in available_formats:
                    use_quality = "MP3_128"
                else:
                    logger.error(f"No formats available for track {track_id}")
                    return False
                    
                logger.info(f"Using {use_quality} (best available)")
            
            # Get download URL from media API
            media_response = self.session.post(
                "https://media.deezer.com/v1/get_url",
                json={
                    'license_token': self.license_token,
                    'media': [{
                        'type': "FULL",
                        'formats': [{'cipher': 'BF_CBC_STRIPE', 'format': use_quality}]
                    }],
                    'track_tokens': [track_token]
                }
            )
            media_response.raise_for_status()
            media_data = media_response.json()
            
            if not media_data.get("data") or not media_data["data"]:
                logger.error(f"No data in media response for track {track_id}")
                return False
                
            media_list = media_data["data"][0].get("media", [])
            if not media_list:
                logger.error(f"No download URL available for track {track_id} in {use_quality}")
                return False
            
            # Get the first source URL
            sources = media_list[0].get("sources", [])
            if not sources:
                logger.error(f"No sources available for track {track_id}")
                return False
                
            url = sources[0].get("url")
            if not url:
                logger.error(f"No URL in sources for track {track_id}")
                return False
            
            # Calculate decryption key
            decrypt_key = calculate_blowfish_key(track_id)
            
            # Download and decrypt the track
            logger.info(f"Downloading track {track_id} in {use_quality} quality...")
            download_response = self.session.get(url, stream=True)
            download_response.raise_for_status()
            
            # Write decrypted data to file
            with open(output_path, "wb") as output_file:
                decrypt_track_stream(download_response, output_file, decrypt_key)
            
            # Add metadata
            self._write_track_metadata(output_path, track_data, use_quality == "FLAC")
            
            logger.info(f"Successfully downloaded track {track_id} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download track {track_id}: {e}")
            return False
    
    def _write_track_metadata(self, file_path: str, track_data: Dict[str, Any], is_flac: bool) -> None:
        """Write metadata to downloaded track file.
        
        Args:
            file_path: Path to the audio file
            track_data: Track metadata from Deezer API
            is_flac: Whether the file is FLAC format
        """
        try:
            from mutagen.flac import FLAC, Picture
            from mutagen.mp3 import MP3
            from mutagen.id3 import TIT2, TALB, TPE1, TRCK, TDRC, TPOS, APIC, TPE2, PictureType
            import requests
            
            if is_flac:
                audio = FLAC(file_path)
                audio["title"] = track_data.get("SNG_TITLE", "")
                audio["artist"] = track_data.get("ART_NAME", "")
                audio["album"] = track_data.get("ALB_TITLE", "")
                audio["tracknumber"] = str(track_data.get("TRACK_NUMBER", ""))
                audio["discnumber"] = str(track_data.get("DISK_NUMBER", ""))
                audio["date"] = track_data.get("PHYSICAL_RELEASE_DATE", "")[:4] if track_data.get("PHYSICAL_RELEASE_DATE") else ""
                
                # Add album art if available
                if track_data.get("ALB_PICTURE"):
                    cover_url = self._get_cover_url(track_data["ALB_PICTURE"], "1000x1000")
                    cover_data = requests.get(cover_url).content
                    picture = Picture()
                    picture.type = PictureType.COVER_FRONT
                    picture.mime = "image/jpeg"
                    picture.data = cover_data
                    audio.add_picture(picture)
            else:
                audio = MP3(file_path)
                audio["TIT2"] = TIT2(encoding=3, text=track_data.get("SNG_TITLE", ""))
                audio["TPE1"] = TPE1(encoding=3, text=track_data.get("ART_NAME", ""))
                audio["TALB"] = TALB(encoding=3, text=track_data.get("ALB_TITLE", ""))
                audio["TRCK"] = TRCK(encoding=3, text=str(track_data.get("TRACK_NUMBER", "")))
                audio["TPOS"] = TPOS(encoding=3, text=str(track_data.get("DISK_NUMBER", "")))
                date = track_data.get("PHYSICAL_RELEASE_DATE", "")[:4] if track_data.get("PHYSICAL_RELEASE_DATE") else ""
                if date:
                    audio["TDRC"] = TDRC(encoding=3, text=date)
                
                # Add album art
                if track_data.get("ALB_PICTURE"):
                    cover_url = self._get_cover_url(track_data["ALB_PICTURE"], "1000x1000")
                    cover_data = requests.get(cover_url).content
                    audio["APIC"] = APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=PictureType.COVER_FRONT,
                        desc="Cover",
                        data=cover_data
                    )
            
            audio.save()
            logger.info(f"Metadata written to {file_path}")
            
        except Exception as e:
            logger.warning(f"Could not write metadata: {e}")
    
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