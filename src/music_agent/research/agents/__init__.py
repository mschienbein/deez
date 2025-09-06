"""
Multi-Agent Research System - Agent Implementations

Specialized agents for music metadata research and track resolution.
"""

from .base import ResearchAgent, AgentRole
from .chief_researcher import ChiefResearcher
from .data_collector import DataCollector
from .metadata_analyst import MetadataAnalyst
from .quality_assessor import QualityAssessor
from .acquisition_scout import AcquisitionScout

__all__ = [
    'ResearchAgent',
    'AgentRole',
    'ChiefResearcher',
    'DataCollector',
    'MetadataAnalyst',
    'QualityAssessor',
    'AcquisitionScout'
]