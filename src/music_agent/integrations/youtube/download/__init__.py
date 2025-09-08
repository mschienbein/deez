"""
YouTube download manager.
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp

from ..config import DownloadConfig
from ..models import Video, DownloadProgress
from ..exceptions import YouTubeDownloadError, YouTubeFormatNotFoundError

logger = logging.getLogger(__name__)


class YouTubeDownloadManager:
    """Manage YouTube downloads with yt-dlp."""
    
    def __init__(self, config: DownloadConfig, ytdlp_opts: Dict[str, Any] = None):
        """Initialize download manager."""
        self.config = config
        self.base_opts = ytdlp_opts or {}
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_ytdlp_options(
        self,
        extract_audio: bool = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Build yt-dlp options."""
        opts = self.base_opts.copy()
        
        # Output options
        opts['outtmpl'] = os.path.join(
            self.config.output_dir,
            '%(title)s-%(id)s.%(ext)s'
        )
        
        # Audio extraction
        if extract_audio or (extract_audio is None and self.config.extract_audio):
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.config.audio_format,
                'preferredquality': self.config.audio_quality,
            }]
        else:
            opts['format'] = self.config.video_quality
        
        # Metadata
        if self.config.embed_metadata:
            if 'postprocessors' not in opts:
                opts['postprocessors'] = []
            opts['postprocessors'].append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            })
        
        # Thumbnail
        if self.config.embed_thumbnail:
            opts['writethumbnail'] = True
            if 'postprocessors' not in opts:
                opts['postprocessors'] = []
            opts['postprocessors'].append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            })
        
        # Info JSON
        opts['writeinfojson'] = self.config.write_info_json
        
        # Subtitles
        if self.config.write_subtitles:
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = self.config.subtitle_langs
        
        # Rate limiting
        if self.config.rate_limit:
            opts['ratelimit'] = self._parse_rate_limit(self.config.rate_limit)
        
        # Retries
        opts['retries'] = self.config.retries
        opts['fragment_retries'] = self.config.retries
        
        # Progress hook
        if progress_callback:
            opts['progress_hooks'] = [progress_callback]
        
        # General options
        opts['quiet'] = False
        opts['no_warnings'] = False
        opts['ignoreerrors'] = False
        
        return opts
    
    def download_video(
        self,
        video_id: str,
        extract_audio: bool = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Download a video.
        
        Args:
            video_id: YouTube video ID
            extract_audio: Extract audio only
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded file
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        return self.download_url(url, extract_audio, progress_callback)
    
    def download_url(
        self,
        url: str,
        extract_audio: bool = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Download from URL.
        
        Args:
            url: YouTube URL
            extract_audio: Extract audio only
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded file
        """
        opts = self._get_ytdlp_options(extract_audio, progress_callback)
        
        # Track downloaded file
        downloaded_file = None
        
        def file_hook(d):
            nonlocal downloaded_file
            if d['status'] == 'finished':
                downloaded_file = d['filename']
            if progress_callback:
                progress_callback(d)
        
        opts['progress_hooks'] = [file_hook]
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    raise YouTubeDownloadError("Failed to download video")
                
                # Get the final filename
                if downloaded_file:
                    # If audio was extracted, update extension
                    if extract_audio or (extract_audio is None and self.config.extract_audio):
                        base = os.path.splitext(downloaded_file)[0]
                        downloaded_file = f"{base}.{self.config.audio_format}"
                    
                    if os.path.exists(downloaded_file):
                        return downloaded_file
                
                # Fallback: try to find the file
                video_id = info.get('id', '')
                title = info.get('title', '')
                
                for ext in [self.config.audio_format, 'mp4', 'webm', 'mkv']:
                    potential_file = os.path.join(
                        self.config.output_dir,
                        f"{title}-{video_id}.{ext}"
                    )
                    if os.path.exists(potential_file):
                        return potential_file
                
                raise YouTubeDownloadError("Downloaded file not found")
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "format" in error_msg.lower():
                raise YouTubeFormatNotFoundError(
                    self.config.video_quality,
                    video_id=url.split('v=')[-1] if 'v=' in url else None
                )
            raise YouTubeDownloadError(f"Download failed: {error_msg}")
        except Exception as e:
            raise YouTubeDownloadError(f"Download failed: {str(e)}")
    
    def download_audio(
        self,
        video_id: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Download audio from video.
        
        Args:
            video_id: YouTube video ID
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded audio file
        """
        return self.download_video(video_id, extract_audio=True, progress_callback=progress_callback)
    
    def download_playlist(
        self,
        playlist_id: str,
        extract_audio: bool = None,
        progress_callback: Optional[Callable] = None,
        start_index: int = None,
        end_index: int = None
    ) -> List[str]:
        """
        Download playlist videos.
        
        Args:
            playlist_id: YouTube playlist ID
            extract_audio: Extract audio only
            progress_callback: Progress callback function
            start_index: Start index (1-based)
            end_index: End index (1-based)
            
        Returns:
            List of downloaded file paths
        """
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        opts = self._get_ytdlp_options(extract_audio, progress_callback)
        
        # Playlist options
        opts['playlistreverse'] = self.config.playlist.reverse_order
        
        if start_index or self.config.playlist.start_index:
            opts['playliststart'] = start_index or self.config.playlist.start_index
        
        if end_index or self.config.playlist.end_index:
            opts['playlistend'] = end_index or self.config.playlist.end_index
        
        if self.config.playlist.max_items:
            opts['max_downloads'] = self.config.playlist.max_items
        
        # Date filters
        if self.config.playlist.date_after:
            opts['dateafter'] = self.config.playlist.date_after
        
        if self.config.playlist.date_before:
            opts['datebefore'] = self.config.playlist.date_before
        
        # Match filters
        if self.config.playlist.match_filter:
            opts['match_filter'] = self.config.playlist.match_filter
        
        downloaded_files = []
        
        def file_hook(d):
            if d['status'] == 'finished':
                downloaded_files.append(d['filename'])
            if progress_callback:
                progress_callback(d)
        
        opts['progress_hooks'] = [file_hook]
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            
            # Convert to final filenames if audio extracted
            if extract_audio or (extract_audio is None and self.config.extract_audio):
                final_files = []
                for file in downloaded_files:
                    base = os.path.splitext(file)[0]
                    audio_file = f"{base}.{self.config.audio_format}"
                    if os.path.exists(audio_file):
                        final_files.append(audio_file)
                    elif os.path.exists(file):
                        final_files.append(file)
                return final_files
            
            return downloaded_files
            
        except Exception as e:
            raise YouTubeDownloadError(f"Playlist download failed: {str(e)}")
    
    def download_multiple(
        self,
        video_ids: List[str],
        extract_audio: bool = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, str]:
        """
        Download multiple videos concurrently.
        
        Args:
            video_ids: List of video IDs
            extract_audio: Extract audio only
            progress_callback: Progress callback function
            
        Returns:
            Dictionary mapping video IDs to file paths
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.concurrent_downloads) as executor:
            # Submit download tasks
            future_to_id = {
                executor.submit(
                    self.download_video,
                    video_id,
                    extract_audio,
                    progress_callback
                ): video_id
                for video_id in video_ids
            }
            
            # Collect results
            for future in as_completed(future_to_id):
                video_id = future_to_id[future]
                try:
                    file_path = future.result()
                    results[video_id] = file_path
                    logger.info(f"Downloaded {video_id} to {file_path}")
                except Exception as e:
                    logger.error(f"Failed to download {video_id}: {e}")
                    results[video_id] = None
        
        return results
    
    def get_download_info(self, url: str) -> Dict[str, Any]:
        """
        Get information about what would be downloaded.
        
        Args:
            url: YouTube URL
            
        Returns:
            Download information
        """
        opts = self._get_ytdlp_options()
        opts['simulate'] = True
        opts['quiet'] = True
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'filesize': info.get('filesize'),
                    'format': info.get('format'),
                    'ext': info.get('ext'),
                    'resolution': info.get('resolution'),
                    'fps': info.get('fps'),
                    'vcodec': info.get('vcodec'),
                    'acodec': info.get('acodec'),
                    'abr': info.get('abr'),
                    'vbr': info.get('vbr')
                }
                
        except Exception as e:
            raise YouTubeDownloadError(f"Failed to get download info: {str(e)}")
    
    def _parse_rate_limit(self, rate_limit: str) -> int:
        """Parse rate limit string to bytes per second."""
        rate_limit = rate_limit.upper()
        
        if rate_limit.endswith('K'):
            return int(float(rate_limit[:-1]) * 1024)
        elif rate_limit.endswith('M'):
            return int(float(rate_limit[:-1]) * 1024 * 1024)
        else:
            return int(rate_limit)