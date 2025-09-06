"""
Music Research Core Components

Core functionality for metadata research and management.
"""

from .metadata_merger import MetadataMerger, MergeStrategy
from .research_agent import MusicResearchAgent
from .quality_analyzer import QualityAnalyzer
from .artwork_manager import ArtworkManager

__all__ = [
    'MetadataMerger',
    'MergeStrategy',
    'MusicResearchAgent',
    'QualityAnalyzer',
    'ArtworkManager'
]