"""
Generic operation templates for music integrations.

Provides base classes and abstract interfaces that all integrations can inherit from
to ensure consistent behavior and prevent code duplication.
"""

from .search import SearchOperation
from .download import DownloadOperation
from .playlist import PlaylistOperation
from .metadata import MetadataOperation
from .streaming import StreamingOperation

__all__ = [
    'SearchOperation',
    'DownloadOperation', 
    'PlaylistOperation',
    'MetadataOperation',
    'StreamingOperation'
]