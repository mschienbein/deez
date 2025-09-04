"""
Download module for Mixcloud integration.

Handles downloading cloudcasts with metadata and artwork.
"""

from .manager import DownloadManager
from .stream_extractor import StreamExtractor
from .metadata import MetadataWriter
from .m3u8 import M3U8Downloader

__all__ = [
    "DownloadManager",
    "StreamExtractor",
    "MetadataWriter",
    "M3U8Downloader",
]