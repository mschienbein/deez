"""
Metadata writer for Bandcamp downloads.
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
            artwork_path: Optional path to artwork
            
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
            artwork_path: Optional path to artwork
            
        Returns:
            True if successful
        """
        try:
            from mutagen.mp3 import MP3
            from mutagen.flac import FLAC
            from mutagen.id3 import (
                ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM, 
                APIC, TRCK, USLT, TXXX
            )
            
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == ".mp3":
                # Handle MP3 files
                audio = MP3(file_path)
                
                if audio.tags is None:
                    audio.add_tags()
                
                # Basic tags
                if metadata.get("title"):
                    audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
                
                if metadata.get("artist"):
                    audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))
                
                if metadata.get("album"):
                    audio.tags.add(TALB(encoding=3, text=metadata["album"]))
                
                if metadata.get("date"):
                    audio.tags.add(TDRC(encoding=3, text=str(metadata["date"])))
                
                if metadata.get("genre"):
                    audio.tags.add(TCON(encoding=3, text=metadata["genre"]))
                
                if metadata.get("track"):
                    audio.tags.add(TRCK(encoding=3, text=str(metadata["track"])))
                
                if metadata.get("comment"):
                    audio.tags.add(COMM(encoding=3, lang="eng", text=metadata["comment"]))
                
                # Lyrics
                if metadata.get("lyrics"):
                    audio.tags.add(USLT(encoding=3, lang="eng", text=metadata["lyrics"]))
                
                # Custom tags
                if metadata.get("url"):
                    audio.tags.add(TXXX(encoding=3, desc="URL", text=metadata["url"]))
                
                # Artwork
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
                
            elif ext == ".flac":
                # Handle FLAC files
                audio = FLAC(file_path)
                
                # Basic tags
                if metadata.get("title"):
                    audio["title"] = metadata["title"]
                
                if metadata.get("artist"):
                    audio["artist"] = metadata["artist"]
                
                if metadata.get("album"):
                    audio["album"] = metadata["album"]
                
                if metadata.get("date"):
                    audio["date"] = str(metadata["date"])
                
                if metadata.get("genre"):
                    audio["genre"] = metadata["genre"]
                
                if metadata.get("track"):
                    audio["tracknumber"] = str(metadata["track"])
                
                if metadata.get("comment"):
                    audio["comment"] = metadata["comment"]
                
                # Lyrics
                if metadata.get("lyrics"):
                    audio["lyrics"] = metadata["lyrics"]
                
                # Artwork
                if artwork_path and os.path.exists(artwork_path):
                    from mutagen.flac import Picture
                    
                    pic = Picture()
                    pic.type = 3  # Cover (front)
                    pic.mime = "image/jpeg"
                    pic.desc = "Cover"
                    
                    with open(artwork_path, "rb") as f:
                        pic.data = f.read()
                    
                    audio.add_picture(pic)
                
                audio.save()
            
            else:
                logger.warning(f"Unsupported file format for metadata: {ext}")
                return False
            
            logger.debug(f"Metadata written to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
            return False


__all__ = ["MetadataWriter"]