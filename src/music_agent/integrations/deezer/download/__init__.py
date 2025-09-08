"""
Deezer download functionality.
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
try:
    from Crypto.Cipher import AES
    from Crypto.Util import Counter
except ImportError:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Util import Counter
    except ImportError:
        # Fallback - download won't work without crypto
        AES = None
        Counter = None
import aiohttp
from aiohttp import ClientSession

from ..config import DownloadConfig
from ..models import Track, TrackFormat
from ..exceptions import DownloadError, DecryptionError, QualityNotAvailableError

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages downloading and decryption of Deezer tracks."""
    
    # Deezer's track encryption key
    TRACK_KEY = bytes.fromhex('6a4b6d3938716432646e7572374e5872')
    
    def __init__(
        self,
        session: ClientSession,
        config: DownloadConfig,
        auth_manager: Optional[Any] = None
    ):
        """
        Initialize download manager.
        
        Args:
            session: aiohttp session
            config: Download configuration
            auth_manager: Authentication manager for quality access
        """
        self.session = session
        self.config = config
        self.auth_manager = auth_manager
        self._download_semaphore = asyncio.Semaphore(config.parallel_downloads)
    
    def _get_blowfish_key(self, track_id: str) -> bytes:
        """
        Generate Blowfish key for track decryption.
        
        Args:
            track_id: Track ID
            
        Returns:
            Blowfish key
        """
        secret = 'g4el58wc0zvf9na1'
        
        track_hash = hashlib.md5(track_id.encode()).hexdigest()
        
        key = ''
        for i in range(16):
            key += chr(ord(track_hash[i]) ^ ord(track_hash[i + 16]) ^ ord(secret[i]))
        
        return key.encode('latin-1')
    
    def _decrypt_chunk(self, chunk: bytes, blowfish_key: bytes, chunk_index: int) -> bytes:
        """
        Decrypt a chunk of track data.
        
        Args:
            chunk: Encrypted chunk
            blowfish_key: Blowfish key
            chunk_index: Chunk index for counter
            
        Returns:
            Decrypted chunk
        """
        if not AES or not Counter:
            # Crypto not available, return chunk as-is
            logger.warning("Crypto library not available, cannot decrypt")
            return chunk
            
        if chunk_index % 3 == 0 and len(chunk) == 2048:
            # Create AES cipher with counter mode
            counter = Counter.new(64, prefix=b'\x00' * 8, initial_value=chunk_index // 3)
            cipher = AES.new(blowfish_key, AES.MODE_CTR, counter=counter)
            return cipher.decrypt(chunk)
        return chunk
    
    async def get_track_download_info(
        self,
        track: Track,
        quality: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get download information for a track.
        
        Args:
            track: Track to download
            quality: Desired quality (FLAC, MP3_320, MP3_128)
            
        Returns:
            Download information including URL and format
            
        Raises:
            QualityNotAvailableError: If requested quality not available
        """
        if not self.auth_manager or not self.auth_manager.is_authenticated:
            raise DownloadError("Authentication required for downloads")
        
        # Determine quality
        if quality is None:
            quality = self.config.quality
        
        # Check if quality is available
        available_qualities = self.auth_manager.available_qualities
        if quality not in available_qualities:
            # Try fallback quality
            if self.config.fallback_quality in available_qualities:
                quality = self.config.fallback_quality
            else:
                # Use best available
                if "FLAC" in available_qualities:
                    quality = "FLAC"
                elif "MP3_320" in available_qualities:
                    quality = "MP3_320"
                else:
                    quality = "MP3_128"
        
        # Get track token for download
        track_token = await self._get_track_token(track.id, quality)
        
        # Build download URL
        download_url = self._build_download_url(track.id, track_token, quality)
        
        return {
            "url": download_url,
            "quality": quality,
            "format": self._get_format_from_quality(quality),
            "track_token": track_token,
            "requires_decryption": quality != "MP3_128",  # Only MP3_128 is unencrypted
        }
    
    async def _get_track_token(self, track_id: str, quality: str) -> str:
        """
        Get track token for download URL.
        
        Args:
            track_id: Track ID
            quality: Quality format
            
        Returns:
            Track token
        """
        # Use gateway API to get track token
        from ..api.base import BaseAPI
        from ..config import APIConfig
        
        api_config = APIConfig()
        api = BaseAPI(self.session, api_config, self.auth_manager)
        
        response = await api.gateway_call(
            "song.getListData",
            {"sng_ids": [track_id]}
        )
        
        if not response.get("results") or not response["results"].get("data"):
            raise DownloadError(f"Failed to get track token for {track_id}")
        
        track_data = response["results"]["data"][0]
        
        # Get appropriate token based on quality
        if quality == "FLAC":
            token = track_data.get("TRACK_TOKEN_FLAC") or track_data.get("TRACK_TOKEN")
        else:
            token = track_data.get("TRACK_TOKEN")
        
        if not token:
            raise DownloadError(f"No track token available for {track_id}")
        
        return token
    
    def _build_download_url(self, track_id: str, track_token: str, quality: str) -> str:
        """
        Build download URL for track.
        
        Args:
            track_id: Track ID
            track_token: Track token
            quality: Quality format
            
        Returns:
            Download URL
        """
        # Map quality to format code
        format_map = {
            "FLAC": "9",
            "MP3_320": "3",
            "MP3_128": "1",
            "MP3_64": "10",
            "MP3_32": "0",
        }
        
        format_code = format_map.get(quality, "1")
        
        # Build CDN URL
        cdn_template = "https://e-cdns-proxy-{}.dzcdn.net/mobile/1/{}"
        
        # Use track token to build path
        track_hash = hashlib.md5(
            f"{format_code}{track_id}{track_token}".encode()
        ).hexdigest()
        
        # Select CDN server (can be randomized)
        cdn_server = track_hash[0]
        
        return cdn_template.format(cdn_server, track_hash)
    
    def _get_format_from_quality(self, quality: str) -> str:
        """Get file format from quality."""
        if quality == "FLAC":
            return "flac"
        return "mp3"
    
    async def download_track(
        self,
        track: Track,
        output_path: Optional[Path] = None,
        quality: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Path:
        """
        Download and decrypt a track.
        
        Args:
            track: Track to download
            output_path: Output file path (auto-generated if not provided)
            quality: Desired quality
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
        """
        async with self._download_semaphore:
            # Get download info
            download_info = await self.get_track_download_info(track, quality)
            
            # Determine output path
            if output_path is None:
                output_path = self._generate_output_path(track, download_info["format"])
            
            # Create parent directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and overwrite setting
            if output_path.exists() and not self.config.overwrite:
                logger.info(f"File already exists: {output_path}")
                return output_path
            
            # Download the track
            try:
                async with self.session.get(download_info["url"]) as response:
                    if response.status != 200:
                        raise DownloadError(f"Download failed with status {response.status}")
                    
                    # Get total size
                    total_size = int(response.headers.get("Content-Length", 0))
                    
                    # Download and decrypt if needed
                    if download_info["requires_decryption"]:
                        decrypted_data = await self._download_and_decrypt(
                            response,
                            track.id,
                            total_size,
                            progress_callback
                        )
                        
                        # Write decrypted data
                        with open(output_path, "wb") as f:
                            f.write(decrypted_data)
                    else:
                        # Direct download without decryption
                        downloaded = 0
                        with open(output_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(self.config.chunk_size):
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if progress_callback:
                                    progress_callback(downloaded, total_size)
                
                # Write metadata if configured
                if self.config.write_metadata:
                    await self._write_metadata(output_path, track)
                
                logger.info(f"Downloaded: {output_path}")
                return output_path
                
            except Exception as e:
                # Clean up partial download
                if output_path.exists():
                    output_path.unlink()
                raise DownloadError(f"Download failed: {e}")
    
    async def _download_and_decrypt(
        self,
        response: aiohttp.ClientResponse,
        track_id: str,
        total_size: int,
        progress_callback: Optional[callable] = None
    ) -> bytes:
        """
        Download and decrypt track data.
        
        Args:
            response: HTTP response
            track_id: Track ID for decryption
            total_size: Total file size
            progress_callback: Progress callback
            
        Returns:
            Decrypted data
        """
        blowfish_key = self._get_blowfish_key(track_id)
        
        decrypted_chunks = []
        downloaded = 0
        chunk_index = 0
        
        async for chunk in response.content.iter_chunked(2048):
            # Decrypt chunk if needed
            decrypted_chunk = self._decrypt_chunk(chunk, blowfish_key, chunk_index)
            decrypted_chunks.append(decrypted_chunk)
            
            downloaded += len(chunk)
            chunk_index += 1
            
            if progress_callback:
                progress_callback(downloaded, total_size)
        
        return b''.join(decrypted_chunks)
    
    def _generate_output_path(self, track: Track, format: str) -> Path:
        """
        Generate output path for track.
        
        Args:
            track: Track object
            format: File format
            
        Returns:
            Output path
        """
        # Build filename from template
        filename = self.config.filename_template.format(
            artist=track.artist_name or "Unknown Artist",
            title=track.title or "Unknown Title",
            album=track.album_title or "Unknown Album",
            track_number=track.track_position or 1,
        )
        
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
        filename = filename.strip()
        
        # Add extension
        filename = f"{filename}.{format}"
        
        # Build full path
        base_dir = Path(self.config.download_dir)
        
        if self.config.create_folders and track.artist_name:
            # Create artist/album folder structure
            artist_dir = "".join(c for c in track.artist_name if c.isalnum() or c in (' ', '-', '_'))
            base_dir = base_dir / artist_dir
            
            if track.album_title:
                album_dir = "".join(c for c in track.album_title if c.isalnum() or c in (' ', '-', '_'))
                base_dir = base_dir / album_dir
        
        return base_dir / filename
    
    async def _write_metadata(self, file_path: Path, track: Track):
        """
        Write metadata to downloaded file.
        
        Args:
            file_path: Path to file
            track: Track object
        """
        try:
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC
            from mutagen.flac import FLAC
            
            if file_path.suffix.lower() == '.mp3':
                # MP3 metadata
                audio = ID3(file_path)
                audio.add(TIT2(encoding=3, text=track.title))
                if track.artist_name:
                    audio.add(TPE1(encoding=3, text=track.artist_name))
                if track.album_title:
                    audio.add(TALB(encoding=3, text=track.album_title))
                if track.release_date:
                    audio.add(TDRC(encoding=3, text=str(track.release_date.year)))
                if track.track_position:
                    audio.add(TRCK(encoding=3, text=str(track.track_position)))
                
                # Add cover art if configured
                if self.config.embed_artwork and track.cover_xl:
                    await self._add_cover_art(audio, track.cover_xl)
                
                audio.save(file_path)
                
            elif file_path.suffix.lower() == '.flac':
                # FLAC metadata
                audio = FLAC(file_path)
                audio["title"] = track.title
                if track.artist_name:
                    audio["artist"] = track.artist_name
                if track.album_title:
                    audio["album"] = track.album_title
                if track.release_date:
                    audio["date"] = str(track.release_date.year)
                if track.track_position:
                    audio["tracknumber"] = str(track.track_position)
                
                # Add cover art if configured
                if self.config.embed_artwork and track.cover_xl:
                    await self._add_cover_art_flac(audio, track.cover_xl)
                
                audio.save()
                
        except Exception as e:
            logger.warning(f"Failed to write metadata: {e}")
    
    async def _add_cover_art(self, audio: Any, cover_url: str):
        """Add cover art to MP3."""
        try:
            from mutagen.id3 import APIC
            async with self.session.get(cover_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    audio.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=image_data
                    ))
        except Exception as e:
            logger.warning(f"Failed to add cover art: {e}")
    
    async def _add_cover_art_flac(self, audio: Any, cover_url: str):
        """Add cover art to FLAC."""
        try:
            from mutagen.flac import Picture
            
            async with self.session.get(cover_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    
                    picture = Picture()
                    picture.type = 3  # Cover (front)
                    picture.mime = 'image/jpeg'
                    picture.desc = 'Cover'
                    picture.data = image_data
                    
                    audio.add_picture(picture)
        except Exception as e:
            logger.warning(f"Failed to add cover art: {e}")