"""
Metadata Analyst Agent - Merges and analyzes metadata using Strands.

Specializes in combining data from multiple sources and resolving conflicts.
"""

from typing import Dict, Any, List
from strands import Agent

from ..tools.metadata_tools import (
    merge_metadata,
    resolve_conflicts,
    calculate_confidence,
    normalize_key,
    normalize_bpm
)


class MetadataAnalystAgent(Agent):
    """
    Strands agent specialized in metadata analysis and merging.
    
    Combines data from multiple platforms, resolves conflicts,
    and produces clean, unified metadata.
    """
    
    def __init__(
        self,
        model: str = "claude-3-sonnet-20240229",  # Use capable model for analysis
        **kwargs
    ):
        """
        Initialize the metadata analyst agent.
        
        Args:
            model: LLM model to use (default: Claude 3 Sonnet)
            **kwargs: Additional Agent configuration
        """
        instructions = """
        You are a metadata analysis specialist with deep expertise in music data.
        
        Your responsibilities:
        1. Merge metadata from multiple platform sources intelligently
        2. Identify and resolve conflicts between different sources
        3. Normalize data formats (BPM, key notation, duration)
        4. Calculate confidence scores based on source agreement
        5. Produce clean, unified metadata ready for use
        
        Key principles:
        - Prioritize data from more reliable sources (Beatport for electronic, MusicBrainz for credits)
        - Handle half/double time BPM variations correctly
        - Normalize key notations to a standard format
        - Preserve all source information for traceability
        - Document conflicts and resolutions clearly
        
        Always use the merge_metadata tool first, then analyze conflicts if any exist.
        """
        
        super().__init__(
            name="MetadataAnalyst",
            model=model,
            tools=[
                merge_metadata,
                resolve_conflicts,
                calculate_confidence,
                normalize_key,
                normalize_bpm
            ],
            instructions=instructions,
            **kwargs
        )
    
    async def analyze(
        self,
        platform_results: List[Dict[str, Any]],
        strategy: str = "confidence_weighted"
    ) -> Dict[str, Any]:
        """
        Analyze and merge metadata from multiple platforms.
        
        Args:
            platform_results: List of search results from different platforms
            strategy: Merge strategy to use
        
        Returns:
            Merged metadata with conflict reports
        """
        prompt = f"""
        Analyze and merge the following metadata from multiple platforms:
        
        Platform Results:
        {platform_results}
        
        Instructions:
        1. Use merge_metadata with strategy: {strategy}
        2. If conflicts are found, use resolve_conflicts to handle them
        3. Calculate the final confidence score
        4. Ensure BPM and key values are normalized
        
        Return a comprehensive analysis with:
        - Merged metadata
        - List of any conflicts and how they were resolved
        - Confidence score with explanation
        - Data quality assessment
        """
        
        response = await self.run(prompt)
        return response
    
    async def validate_identity(
        self,
        platform_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate that all results refer to the same track.
        
        Args:
            platform_results: Search results to validate
        
        Returns:
            Validation result with confidence
        """
        prompt = f"""
        Validate that these search results all refer to the SAME track:
        
        {platform_results}
        
        Check:
        1. Artist name similarity (handle variations like "feat." vs "ft.")
        2. Title similarity (handle remix/edit variations)
        3. Duration consistency (within reasonable range)
        4. ISRC matching if available
        
        Return:
        - is_same_track: boolean
        - confidence: 0.0-1.0
        - explanation: why you think they match or don't match
        - variations: list any name variations found
        """
        
        response = await self.run(prompt)
        return response
    
    async def enhance_metadata(
        self,
        metadata: Dict[str, Any],
        platform_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enhance metadata with cross-references and derived data.
        
        Args:
            metadata: Base merged metadata
            platform_results: Original platform results for reference
        
        Returns:
            Enhanced metadata
        """
        prompt = f"""
        Enhance this merged metadata with additional insights:
        
        Merged Metadata:
        {metadata}
        
        Original Sources:
        {platform_results}
        
        Tasks:
        1. Add any missing IDs from the platform results
        2. Derive sub-genres from genre and style information
        3. Extract featuring artists from title if present
        4. Identify remix/edit information
        5. Add any credits found in the results
        
        Return enhanced metadata with all improvements.
        """
        
        response = await self.run(prompt)
        return response