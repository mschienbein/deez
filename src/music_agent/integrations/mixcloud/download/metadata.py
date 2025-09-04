"""
Metadata writer for downloaded Mixcloud files.

Writes ID3 tags and embeds artwork.
"""

import logging
import os
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class MetadataWriter:
    """Writes metadata to audio files."""
    
    def __init__(self, config):
        """
        Initialize metadata writer.
        
        Args:
            config: Download configuration
        """
        self.config = config
        self._mutagen_available = False
        
        try:
            import mutagen
            self._mutagen_available = True
            logger.debug("Mutagen available for metadata writing")
        except ImportError:
            logger.warning("Mutagen not available - metadata writing disabled")
    
    async def write(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        artwork_path: Optional[str] = None
    ) -> bool:
        """
        Write metadata to file.
        
        Args:
            file_path: Path to audio file
            metadata: Metadata dictionary
            artwork_path: Optional path to artwork image
            
        Returns:
            True if successful
        """
        if not self._mutagen_available:
            return False
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._write_sync,
            file_path,
            metadata,
            artwork_path
        )
    
    def _write_sync(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        artwork_path: Optional[str] = None
    ) -> bool:
        """
        Synchronously write metadata.
        
        Args:
            file_path: Path to audio file
            metadata: Metadata dictionary
            artwork_path: Optional path to artwork image
            
        Returns:
            True if successful
        """
        try:
            from mutagen.mp3 import MP3
            from mutagen.mp4 import MP4
            from mutagen.id3 import (
                ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM, APIC, TXXX
            )
            
            # Determine file type
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == ".mp3":
                # Handle MP3 files
                audio = MP3(file_path)
                
                # Create ID3 tags if needed
                if audio.tags is None:
                    audio.add_tags()
                
                # Write basic tags
                if metadata.get("title"):
                    audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
                
                if metadata.get("artist"):
                    audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))
                
                if metadata.get("album"):
                    audio.tags.add(TALB(encoding=3, text=metadata["album"]))
                
                if metadata.get("date"):
                    audio.tags.add(TDRC(encoding=3, text=metadata["date"]))
                
                if metadata.get("genre"):
                    audio.tags.add(TCON(encoding=3, text=metadata["genre"]))
                
                if metadata.get("comment"):
                    audio.tags.add(COMM(encoding=3, lang="eng", text=metadata["comment"]))
                
                if metadata.get("url"):
                    audio.tags.add(TXXX(encoding=3, desc="URL", text=metadata["url"]))
                
                # Add artwork if available
                if artwork_path and os.path.exists(artwork_path):
                    with open(artwork_path, "rb") as f:
                        audio.tags.add(
                            APIC(
                                encoding=3,
                                mime="image/jpeg",
                                type=3,  # Cover (front)
                                desc="Cover",
                                data=f.read()
                            )
                        )
                
                audio.save()
                
            elif ext in [".m4a", ".mp4"]:
                # Handle M4A/MP4 files
                audio = MP4(file_path)
                
                # Write tags using MP4 atoms
                if metadata.get("title"):
                    audio["\xa9nam"] = metadata["title"]
                
                if metadata.get("artist"):
                    audio["\xa9ART"] = metadata["artist"]
                
                if metadata.get("album"):
                    audio["\xa9alb"] = metadata["album"]
                
                if metadata.get("date"):
                    audio["\xa9day"] = metadata["date"]
                
                if metadata.get("genre"):
                    audio["\xa9gen"] = metadata["genre"]
                
                if metadata.get("comment"):
                    audio["\xa9cmt"] = metadata["comment"]
                
                # Add artwork if available
                if artwork_path and os.path.exists(artwork_path):
                    with open(artwork_path, "rb") as f:
                        audio["covr"] = [
                            MP4.Cover(f.read(), imageformat=MP4.Cover.FORMAT_JPEG)
                        ]
                
                audio.save()
            
            else:
                logger.warning(f"Unsupported file format for metadata: {ext}")
                return False
            
            logger.debug(f"Metadata written to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
            return False
    
    async def read(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Read metadata from file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Metadata dictionary or None
        """
        if not self._mutagen_available:
            return None
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._read_sync,
            file_path
        )
    
    def _read_sync(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Synchronously read metadata.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Metadata dictionary or None
        """
        try:
            from mutagen import File
            
            audio = File(file_path)
            if not audio:
                return None
            
            metadata = {}
            
            # Extract common tags
            tag_mapping = {
                "TIT2": "title",
                "TPE1": "artist",
                "TALB": "album",
                "TDRC": "date",
                "TCON": "genre",
                "COMM": "comment",
                "\xa9nam": "title",
                "\xa9ART": "artist",
                "\xa9alb": "album",
                "\xa9day": "date",
                "\xa9gen": "genre",
                "\xa9cmt": "comment",
            }
            
            for tag, key in tag_mapping.items():
                if tag in audio:
                    value = audio[tag]
                    if isinstance(value, list) and value:
                        metadata[key] = str(value[0])
                    else:
                        metadata[key] = str(value)
            
            # Get duration
            if hasattr(audio.info, "length"):
                metadata["duration"] = int(audio.info.length)
            
            # Get bitrate
            if hasattr(audio.info, "bitrate"):
                metadata["bitrate"] = audio.info.bitrate
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to read metadata: {e}")
            return None


__all__ = ["MetadataWriter"]