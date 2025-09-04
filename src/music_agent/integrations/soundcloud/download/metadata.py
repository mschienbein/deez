"""
Metadata writer for downloaded tracks.

Writes ID3 tags and embeds artwork.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import (
        ID3, TIT2, TPE1, TALB, TDRC, TCON, TPE2, TRCK,
        COMM, APIC, TPOS, TPUB, WOAR, TXXX, USLT
    )
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("mutagen not available - metadata writing disabled")

logger = logging.getLogger(__name__)


class MetadataWriter:
    """Writes metadata tags to downloaded audio files."""
    
    def __init__(self):
        """Initialize metadata writer."""
        self.enabled = MUTAGEN_AVAILABLE
    
    async def write_metadata(
        self,
        file_path: Path,
        track,
        artwork_data: Optional[bytes] = None
    ) -> bool:
        """
        Write metadata to audio file.
        
        Args:
            file_path: Path to audio file
            track: Track model instance
            artwork_data: Optional artwork bytes
            
        Returns:
            True if successful
        """
        if not self.enabled:
            logger.warning("Metadata writing disabled - mutagen not available")
            return False
        
        try:
            # Load or create ID3 tags
            audio = MP3(file_path)
            
            if audio.tags is None:
                audio.add_tags()
            
            tags = audio.tags
            
            # Clear existing tags
            tags.delete()
            
            # Title
            if track.title:
                tags.add(TIT2(encoding=3, text=track.title))
            
            # Artist
            if track.artist:
                tags.add(TPE1(encoding=3, text=track.artist))
            
            # Album
            if track.album:
                tags.add(TALB(encoding=3, text=track.album))
            
            # Album artist
            if hasattr(track, "album_artist") and track.album_artist:
                tags.add(TPE2(encoding=3, text=track.album_artist))
            
            # Year
            if track.created_at:
                year = track.created_at.year
                tags.add(TDRC(encoding=3, text=str(year)))
            elif hasattr(track, "release_date") and track.release_date:
                year = track.release_date.year
                tags.add(TDRC(encoding=3, text=str(year)))
            
            # Genre
            if track.genre:
                tags.add(TCON(encoding=3, text=track.genre))
            
            # Track number
            if track.track_number:
                track_str = str(track.track_number)
                if hasattr(track, "total_tracks") and track.total_tracks:
                    track_str = f"{track.track_number}/{track.total_tracks}"
                tags.add(TRCK(encoding=3, text=track_str))
            
            # Disc number
            if hasattr(track, "disc_number") and track.disc_number:
                disc_str = str(track.disc_number)
                if hasattr(track, "total_discs") and track.total_discs:
                    disc_str = f"{track.disc_number}/{track.total_discs}"
                tags.add(TPOS(encoding=3, text=disc_str))
            
            # Description/Comment
            if track.description:
                # Add as comment
                tags.add(COMM(
                    encoding=3,
                    lang="eng",
                    desc="Description",
                    text=track.description
                ))
                
                # Also add as lyrics (for some players)
                tags.add(USLT(
                    encoding=3,
                    lang="eng",
                    desc="",
                    text=track.description
                ))
            
            # Label
            if track.label_name:
                tags.add(TPUB(encoding=3, text=track.label_name))
            
            # URL
            if track.permalink_url:
                tags.add(WOAR(url=track.permalink_url))
            
            # Custom tags
            self._add_custom_tags(tags, track)
            
            # Artwork
            if artwork_data:
                self._embed_artwork(tags, artwork_data)
            
            # Save tags
            audio.save()
            
            logger.info(f"Wrote metadata to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
            return False
    
    def _add_custom_tags(self, tags: ID3, track):
        """Add custom SoundCloud-specific tags."""
        # SoundCloud ID
        tags.add(TXXX(
            encoding=3,
            desc="SOUNDCLOUD_ID",
            text=str(track.id)
        ))
        
        # SoundCloud URL
        if track.permalink_url:
            tags.add(TXXX(
                encoding=3,
                desc="SOUNDCLOUD_URL",
                text=track.permalink_url
            ))
        
        # License
        if track.license:
            tags.add(TXXX(
                encoding=3,
                desc="LICENSE",
                text=track.license
            ))
        
        # BPM
        if hasattr(track, "bpm") and track.bpm:
            tags.add(TXXX(
                encoding=3,
                desc="BPM",
                text=str(track.bpm)
            ))
        
        # Key signature
        if hasattr(track, "key_signature") and track.key_signature:
            tags.add(TXXX(
                encoding=3,
                desc="KEY",
                text=track.key_signature
            ))
        
        # Tags
        if track.tags:
            tags.add(TXXX(
                encoding=3,
                desc="TAGS",
                text=", ".join(track.tags)
            ))
        
        # Statistics
        if track.playback_count:
            tags.add(TXXX(
                encoding=3,
                desc="PLAYBACK_COUNT",
                text=str(track.playback_count)
            ))
        
        if track.likes_count:
            tags.add(TXXX(
                encoding=3,
                desc="LIKES_COUNT",
                text=str(track.likes_count)
            ))
        
        if track.reposts_count:
            tags.add(TXXX(
                encoding=3,
                desc="REPOSTS_COUNT",
                text=str(track.reposts_count)
            ))
        
        # User info
        if track.username:
            tags.add(TXXX(
                encoding=3,
                desc="UPLOADER",
                text=track.username
            ))
    
    def _embed_artwork(self, tags: ID3, artwork_data: bytes):
        """Embed artwork in tags."""
        # Detect image type
        mime_type = self._detect_image_type(artwork_data)
        
        # Determine picture type (3 = Cover front)
        tags.add(APIC(
            encoding=3,
            mime=mime_type,
            type=3,
            desc="Cover",
            data=artwork_data
        ))
    
    def _detect_image_type(self, data: bytes) -> str:
        """Detect image MIME type from data."""
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif data[:3] == b'\xff\xd8\xff':
            return "image/jpeg"
        elif data[:4] == b'GIF8':
            return "image/gif"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "image/webp"
        else:
            # Default to JPEG
            return "image/jpeg"
    
    async def read_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Read metadata from audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary of metadata
        """
        if not self.enabled:
            return {}
        
        try:
            audio = MP3(file_path)
            
            if audio.tags is None:
                return {}
            
            tags = audio.tags
            metadata = {}
            
            # Basic tags
            if "TIT2" in tags:
                metadata["title"] = str(tags["TIT2"].text[0])
            
            if "TPE1" in tags:
                metadata["artist"] = str(tags["TPE1"].text[0])
            
            if "TALB" in tags:
                metadata["album"] = str(tags["TALB"].text[0])
            
            if "TDRC" in tags:
                metadata["year"] = str(tags["TDRC"].text[0])
            
            if "TCON" in tags:
                metadata["genre"] = str(tags["TCON"].text[0])
            
            if "TRCK" in tags:
                metadata["track_number"] = str(tags["TRCK"].text[0])
            
            # Custom tags
            custom = {}
            for frame in tags.values():
                if isinstance(frame, TXXX):
                    custom[frame.desc] = str(frame.text[0])
            
            if custom:
                metadata["custom"] = custom
            
            # Audio properties
            metadata["duration"] = audio.info.length
            metadata["bitrate"] = audio.info.bitrate
            metadata["sample_rate"] = audio.info.sample_rate
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to read metadata: {e}")
            return {}
    
    def strip_metadata(self, file_path: Path) -> bool:
        """
        Remove all metadata from audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            audio = MP3(file_path)
            audio.delete()
            audio.save()
            return True
        except Exception as e:
            logger.error(f"Failed to strip metadata: {e}")
            return False


class PlaylistMetadata:
    """Handles playlist metadata operations."""
    
    @staticmethod
    def generate_m3u(playlist, tracks: list) -> str:
        """
        Generate M3U playlist content.
        
        Args:
            playlist: Playlist model instance
            tracks: List of track instances
            
        Returns:
            M3U formatted string
        """
        lines = ["#EXTM3U"]
        
        # Playlist info
        if playlist.title:
            lines.append(f"#PLAYLIST:{playlist.title}")
        
        if hasattr(playlist, "username") and playlist.username:
            lines.append(f"#EXTART:{playlist.username}")
        
        # Add tracks
        for track in tracks:
            # Extended info
            duration = int(track.duration_seconds) if hasattr(track, "duration_seconds") else -1
            artist_title = f"{track.artist} - {track.title}"
            lines.append(f"#EXTINF:{duration},{artist_title}")
            
            # Use filename or URL
            if hasattr(track, "file_path") and track.file_path:
                lines.append(str(track.file_path))
            else:
                lines.append(track.permalink_url)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_pls(playlist, tracks: list) -> str:
        """
        Generate PLS playlist content.
        
        Args:
            playlist: Playlist model instance
            tracks: List of track instances
            
        Returns:
            PLS formatted string
        """
        lines = ["[playlist]"]
        
        for idx, track in enumerate(tracks, 1):
            # File entry
            if hasattr(track, "file_path") and track.file_path:
                lines.append(f"File{idx}={track.file_path}")
            else:
                lines.append(f"File{idx}={track.permalink_url}")
            
            # Title entry
            lines.append(f"Title{idx}={track.artist} - {track.title}")
            
            # Length entry
            if hasattr(track, "duration_seconds"):
                lines.append(f"Length{idx}={int(track.duration_seconds)}")
            else:
                lines.append(f"Length{idx}=-1")
        
        # Footer
        lines.append(f"NumberOfEntries={len(tracks)}")
        lines.append("Version=2")
        
        return "\n".join(lines)


__all__ = ["MetadataWriter", "PlaylistMetadata"]