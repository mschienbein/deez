"""
Download module for Bandcamp.
"""

from .manager import DownloadManager
from .metadata import MetadataWriter

__all__ = [
    "DownloadManager",
    "MetadataWriter",
]