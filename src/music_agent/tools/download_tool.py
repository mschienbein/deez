"""Download tool for music using Deezer integration."""

import logging
import os
from pathlib import Path
from typing import Optional

from strands import tool

from ..integrations.deezer import DeezerIntegration
from .music_tools import search_music

logger = logging.getLogger(__name__)


@tool
def download_track(track_id: str, platform: str = "deezer", output_dir: str = None) -> str:
    """Download a track by ID from the specified platform.
    
    Args:
        track_id: The platform-specific track ID
        platform: The platform to download from (currently only 'deezer' supported)
        output_dir: Output directory for the downloaded file (defaults to ~/Music/downloads)
    
    Returns:
        Path to the downloaded file or error message
    """
    if platform != "deezer":
        return f"Error: Platform '{platform}' not supported for downloads yet"
    
    if not output_dir:
        output_dir = os.path.expanduser("~/Music/downloads")
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        deezer = DeezerIntegration()
        
        # Get track info
        track_info = deezer.get_track_info(track_id)
        if not track_info:
            return f"Error: Could not find track with ID {track_id}"
        
        # Create filename
        safe_artist = "".join(c for c in track_info["artist"] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in track_info["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
        
        # Use temporary path first, will rename based on actual format
        temp_path = os.path.join(output_dir, f"{safe_artist} - {safe_title}.tmp")
        
        # Download the track
        logger.info(f"Starting download of track {track_id}")
        success = deezer.download_track(track_id, temp_path)
        
        # Determine actual format and rename
        if success and os.path.exists(temp_path):
            # Check if it's FLAC or MP3
            with open(temp_path, 'rb') as f:
                header = f.read(4)
            
            if header == b'fLaC':
                file_extension = 'flac'
                actual_quality = 'FLAC'
            else:
                file_extension = 'mp3'
                actual_quality = 'MP3'
            
            # Rename to proper extension
            output_path = os.path.join(output_dir, f"{safe_artist} - {safe_title}.{file_extension}")
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)
        
        if success:
            # Check file size
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            file_size_mb = file_size / (1024 * 1024)
            
            return f"""✅ Download Complete!
  
  Title: {track_info['title']}
  Artist: {track_info['artist']}  
  Album: {track_info.get('album', 'Unknown')}
  Duration: {track_info.get('duration', 0)} seconds
  Quality: {actual_quality}
  
  Output: {output_path}
  File Size: {file_size_mb:.2f} MB
  Track URL: {track_info.get('platform_url', '')}"""
        else:
            return f"""❌ Download Failed
            
  Track: {track_info['title']} by {track_info['artist']}
  Error: Could not download track. Check logs for details."""
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return f"Error: Download failed - {str(e)}"


@tool 
def search_and_download(query: str, platform: str = "deezer", output_dir: str = None) -> str:
    """Search for a track and download the first result.
    
    Args:
        query: Search query (e.g., "artist - song title")
        platform: Platform to search and download from
        output_dir: Output directory for downloaded files
    
    Returns:
        Status message about the download
    """
    try:
        # Search for the track
        results = search_music(query, platform, limit=1)
        
        if not results:
            return f"No results found for: {query}"
        
        track = results[0]
        track_id = track["id"]
        
        logger.info(f"Found track: {track['title']} by {track['artist']} (ID: {track_id})")
        
        # Download the track
        return download_track(track_id, platform, output_dir)
        
    except Exception as e:
        logger.error(f"Search and download failed: {e}")
        return f"Error: {str(e)}"