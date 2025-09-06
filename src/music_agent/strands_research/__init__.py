"""
Music Research System - AWS Strands Implementation

A proper multi-agent research system using AWS Strands framework for
orchestrating specialized agents to research and resolve music metadata.
"""

from .core.orchestrator import MusicResearchOrchestrator
from .agents.chief_researcher import ChiefResearcherSupervisor
from .models.metadata import TrackMetadata, ResearchResult

__all__ = [
    'MusicResearchOrchestrator',
    'ChiefResearcherSupervisor',
    'TrackMetadata',
    'ResearchResult'
]

__version__ = '1.0.0'