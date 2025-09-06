"""
Quality Assessor Agent - Evaluates metadata quality using Strands.

Determines if metadata meets requirements for track resolution.
"""

from typing import Dict, Any, List, Optional
from strands import Agent

from ..tools.quality_tools import (
    assess_quality,
    check_completeness,
    validate_metadata,
    generate_recommendations
)


class QualityAssessorAgent(Agent):
    """
    Strands agent specialized in quality assessment.
    
    Evaluates metadata completeness, accuracy, and reliability
    to determine if a track can be marked as "SOLVED".
    """
    
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",  # Fast model for assessment
        **kwargs
    ):
        """
        Initialize the quality assessor agent.
        
        Args:
            model: LLM model to use
            **kwargs: Additional Agent configuration
        """
        instructions = """
        You are a quality assessment specialist for music metadata.
        
        Your responsibilities:
        1. Evaluate metadata completeness against requirements
        2. Validate data quality and check for errors
        3. Assess confidence based on sources and agreement
        4. Generate actionable recommendations for improvement
        5. Determine if track meets "SOLVED" criteria
        
        SOLVED criteria:
        - Metadata completeness >= 80%
        - Confidence score >= 70%
        - At least 2 platform sources
        - No critical validation errors
        - High-quality acquisition option available
        
        Be thorough but efficient. Focus on actionable insights.
        """
        
        super().__init__(
            name="QualityAssessor",
            model=model,
            tools=[
                assess_quality,
                check_completeness,
                validate_metadata,
                generate_recommendations
            ],
            instructions=instructions,
            **kwargs
        )
    
    async def assess(
        self,
        metadata: Dict[str, Any],
        sources: List[str],
        acquisition_options: Optional[List[Dict[str, Any]]] = None,
        thresholds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Assess metadata quality and completeness.
        
        Args:
            metadata: Merged metadata to assess
            sources: List of platforms that provided data
            acquisition_options: Available acquisition options
            thresholds: Custom quality thresholds
        
        Returns:
            Quality assessment report
        """
        prompt = f"""
        Assess the quality of this track metadata:
        
        Metadata:
        {metadata}
        
        Sources: {sources}
        Acquisition Options: {acquisition_options or 'None found yet'}
        
        Custom Thresholds: {thresholds or 'Use defaults (80% completeness, 70% confidence)'}
        
        Steps:
        1. Use check_completeness to evaluate field coverage
        2. Use validate_metadata to check for errors
        3. Use assess_quality to get overall assessment
        4. Use generate_recommendations for improvements
        
        Return a comprehensive quality report including:
        - Overall quality score
        - Completeness percentage
        - Confidence score
        - List of issues found
        - Recommendations for improvement
        - Whether track meets SOLVED criteria
        """
        
        response = await self.run(prompt)
        return response
    
    async def quick_check(
        self,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform a quick quality check.
        
        Args:
            metadata: Metadata to check
        
        Returns:
            Quick assessment result
        """
        prompt = f"""
        Perform a quick quality check on this metadata:
        
        {metadata}
        
        Use check_completeness to get a fast assessment.
        
        Return:
        - completeness_score: 0.0-1.0
        - missing_critical_fields: list of critical missing fields
        - quick_verdict: "good", "needs_work", or "poor"
        """
        
        response = await self.run(prompt)
        return response
    
    async def compare_sources(
        self,
        platform_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare quality across different sources.
        
        Args:
            platform_results: Results from different platforms
        
        Returns:
            Comparison of source quality
        """
        prompt = f"""
        Compare the quality of data from these sources:
        
        {platform_results}
        
        For each source, evaluate:
        1. Data completeness
        2. Field coverage
        3. Unique valuable data provided
        4. Reliability for this type of music
        
        Return:
        - best_source: platform with highest quality data
        - source_rankings: ranked list with scores
        - unique_contributions: what each source uniquely provides
        """
        
        response = await self.run(prompt)
        return response