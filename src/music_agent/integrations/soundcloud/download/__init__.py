"""
Download functionality for SoundCloud tracks.

Handles MP3 downloads, HLS stream assembly, and metadata writing.
"""

from .manager import DownloadManager
from .stream_handler import StreamHandler
from .metadata import MetadataWriter
from .hls import HLSDownloader

__all__ = [
    "DownloadManager",
    "StreamHandler",
    "MetadataWriter",
    "HLSDownloader",
]