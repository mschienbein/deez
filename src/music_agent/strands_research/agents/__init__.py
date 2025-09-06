"""
Strands-based agents for music research.

These agents use the AWS Strands framework for orchestration and coordination.
"""

from .data_collector import DataCollectorAgent
from .metadata_analyst import MetadataAnalystAgent
from .quality_assessor import QualityAssessorAgent
from .acquisition_scout import AcquisitionScoutAgent
from .chief_researcher import ChiefResearcherSupervisor

__all__ = [
    'DataCollectorAgent',
    'MetadataAnalystAgent',
    'QualityAssessorAgent',
    'AcquisitionScoutAgent',
    'ChiefResearcherSupervisor'
]