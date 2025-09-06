"""
Chief Researcher Supervisor Agent - Orchestrates research using Strands.

This demonstrates the Supervisor pattern where one agent coordinates others.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from strands import Agent

from .data_collector import DataCollectorAgent
from .metadata_analyst import MetadataAnalystAgent
from .quality_assessor import QualityAssessorAgent
from .acquisition_scout import AcquisitionScoutAgent


class ChiefResearcherSupervisor(Agent):
    """
    Chief Researcher as a Strands Supervisor Agent.
    
    This agent orchestrates the entire research workflow by coordinating
    specialized sub-agents. It demonstrates the Supervisor pattern in Strands.
    """
    
    def __init__(
        self,
        model: str = "claude-3-opus-20240229",  # Use most capable model for orchestration
        platforms: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the Chief Researcher supervisor.
        
        Args:
            model: LLM model to use for orchestration
            platforms: List of platforms to search (default: major platforms)
            **kwargs: Additional Agent configuration
        """
        # Default platforms if not specified
        if platforms is None:
            platforms = ["spotify", "beatport", "discogs", "musicbrainz"]
        
        self.platforms = platforms
        
        # Create sub-agents for the supervisor to coordinate
        self.sub_agents = {}
        
        # Create data collectors for each platform
        for platform in platforms:
            self.sub_agents[f"{platform}_collector"] = DataCollectorAgent(platform)
        
        # Create specialist agents
        self.sub_agents["analyst"] = MetadataAnalystAgent()
        self.sub_agents["assessor"] = QualityAssessorAgent()
        self.sub_agents["scout"] = AcquisitionScoutAgent()
        
        # Build dynamic instructions based on available platforms
        platform_list = "\n".join([f"- {p}_collector: Searches {p}" for p in platforms])
        
        instructions = f"""
        You are the Chief Music Researcher, supervising a team of specialized agents.
        
        Your team consists of:
        {platform_list}
        - analyst: Merges and analyzes metadata
        - assessor: Evaluates quality and completeness
        - scout: Finds acquisition sources
        
        Research Workflow:
        1. Parse the query to understand what track is being researched
        2. Search platforms in parallel using the collectors
        3. Send all results to the analyst for merging
        4. Have the assessor evaluate the merged metadata
        5. Use the scout to find acquisition options
        6. Make a final decision on whether the track is "SOLVED"
        
        A track is SOLVED when:
        - Metadata completeness >= 80%
        - Confidence score >= 70%
        - At least 2 platforms confirmed the data
        - High-quality acquisition source is available
        
        Coordinate your team efficiently. Run parallel searches when possible.
        Be decisive about whether a track is solved or needs more research.
        """
        
        # Initialize as supervisor agent
        super().__init__(
            name="ChiefResearcher",
            model=model,
            tools=[],  # Supervisor doesn't need direct tools
            instructions=instructions,
            supervisor=True,  # Enable supervisor mode
            sub_agents=self.sub_agents,
            **kwargs
        )
    
    async def research_track(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Research a track using the full agent team.
        
        Args:
            query: Track search query (e.g., "Artist - Title")
            context: Optional context (genre hints, year, etc.)
        
        Returns:
            Complete research results
        """
        context_str = ""
        if context:
            context_str = f"\nAdditional context: {context}"
        
        prompt = f"""
        Research this track thoroughly: {query}
        {context_str}
        
        Execute the complete workflow:
        
        1. SEARCH PHASE (parallel):
           - Use all {len(self.platforms)} platform collectors simultaneously
           - Search for: {query}
           - Gather comprehensive metadata from each platform
        
        2. ANALYSIS PHASE:
           - Send all platform results to the analyst
           - Merge metadata using confidence_weighted strategy
           - Resolve any conflicts found
        
        3. QUALITY PHASE:
           - Send merged metadata to the assessor
           - Get quality report and recommendations
           - Check if it meets SOLVED criteria
        
        4. ACQUISITION PHASE:
           - Send metadata to the scout
           - Find purchase and streaming options
           - Identify best source for DJs
        
        5. DECISION PHASE:
           - Determine if track is SOLVED
           - Provide clear reasoning
           - List any remaining issues
        
        Return a comprehensive research report with:
        - Final merged metadata
        - Quality assessment
        - Acquisition options
        - SOLVED status with explanation
        - Confidence score
        - Recommendations if not solved
        """
        
        start_time = datetime.utcnow()
        response = await self.run(prompt)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Add metadata about the research process
        if isinstance(response, dict):
            response["research_duration"] = duration
            response["platforms_searched"] = self.platforms
            response["query"] = query
        
        return response
    
    async def quick_research(
        self,
        query: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform quick research using fewer platforms.
        
        Args:
            query: Track search query
            platforms: Specific platforms to use (default: spotify, beatport)
        
        Returns:
            Quick research results
        """
        if platforms is None:
            platforms = ["spotify", "beatport"]
        
        # Build collector list
        collectors = [f"{p}_collector" for p in platforms if p in self.platforms]
        
        prompt = f"""
        Perform QUICK research on: {query}
        
        Use only these collectors: {collectors}
        
        Simplified workflow:
        1. Search the specified platforms
        2. Use analyst to merge results
        3. Use assessor for quick quality check
        4. Skip acquisition scouting
        
        Return:
        - Basic merged metadata
        - Completeness score
        - Quick verdict: "found", "partial", or "not_found"
        """
        
        response = await self.run(prompt)
        return response
    
    async def find_rare_track(
        self,
        query: str,
        deep_search: bool = True
    ) -> Dict[str, Any]:
        """
        Special workflow for finding rare or underground tracks.
        
        Args:
            query: Track search query
            deep_search: Whether to search all available platforms
        
        Returns:
            Research results optimized for rare tracks
        """
        prompt = f"""
        Search for this potentially RARE track: {query}
        
        This might be:
        - An underground/unreleased track
        - A bootleg or white label
        - An old/obscure release
        - A regional exclusive
        
        Adjusted strategy:
        1. Search ALL platforms, especially:
           - SoundCloud (for bootlegs/remixes)
           - Discogs (for vinyl/rare releases)
           - MusicBrainz (for obscure metadata)
        
        2. Be more flexible with matching:
           - Accept partial matches
           - Look for alternate versions
           - Check for similar titles
        
        3. Focus the scout on:
           - Bandcamp (independent releases)
           - Discogs marketplace (physical media)
           - P2P networks as last resort
        
        Return findings even if incomplete.
        """
        
        response = await self.run(prompt)
        return response