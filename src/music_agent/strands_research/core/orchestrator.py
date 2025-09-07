"""
Music Research Orchestrator using AWS Strands MultiAgentOrchestrator.

This is the PROPER implementation using Strands' built-in orchestration.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from strands.multiagent import Swarm
from strands import Agent
import logging

# Configure logging
logger = logging.getLogger(__name__)

from ..agents import (
    DataCollectorAgent,
    MetadataAnalystAgent,
    QualityAssessorAgent,
    AcquisitionScoutAgent
)
from ..models import ResearchResult, TrackMetadata

# Configure logging
logger = Logger()


class MusicResearchOrchestrator:
    """
    Orchestrates multiple agents using AWS Strands Swarm.
    
    This demonstrates the proper way to implement multi-agent systems
    with Strands, using the framework's built-in orchestration capabilities
    instead of building custom coordination logic.
    """
    
    def __init__(
        self,
        platforms: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the music research orchestrator.
        
        Args:
            platforms: List of platforms to search (default: major platforms)
            config: Optional configuration for agents and orchestration
        """
        self.config = config or {}
        
        # Default platforms
        if platforms is None:
            platforms = ["spotify", "beatport", "discogs", "musicbrainz", "deezer"]
        self.platforms = platforms
        
        # Create and register specialized agents
        self._setup_agents()
        
        # Create the Strands Swarm with our agents
        self.swarm = Swarm(
            agents=list(self.all_agents.values()),
            max_workers=self.config.get("max_workers", 5)
        )
    
    def _setup_agents(self):
        """Create and register all specialized agents."""
        # Create data collector for each platform
        self.data_collectors = {}
        for platform in self.platforms:
            try:
                agent = DataCollectorAgent(platform)
                self.data_collectors[platform] = agent
                self.orchestrator.add_agent(agent)
                logger.info(f"Registered DataCollector for {platform}")
            except Exception as e:
                logger.error(f"Failed to create collector for {platform}: {e}")
        
        # Create analysis agents
        self.metadata_analyst = MetadataAnalystAgent()
        self.quality_assessor = QualityAssessorAgent()
        self.acquisition_scout = AcquisitionScoutAgent()
        
        # Register with orchestrator
        self.orchestrator.add_agent(self.metadata_analyst)
        self.orchestrator.add_agent(self.quality_assessor)
        self.orchestrator.add_agent(self.acquisition_scout)
        
        logger.info(f"Registered {len(self.data_collectors) + 3} agents total")
    
    def _configure_orchestrator(self):
        """Configure the orchestrator's behavior and routing rules."""
        # Set system prompt for the orchestrator
        self.orchestrator.system_prompt = """
        You are coordinating a music research system with specialized agents.
        
        Agent Capabilities:
        - DataCollector agents: Search specific platforms for track metadata
        - MetadataAnalyst: Merges and analyzes data from multiple sources
        - QualityAssessor: Evaluates metadata quality and completeness
        - AcquisitionScout: Finds where to buy/stream tracks
        
        Routing Rules:
        1. Route platform searches to appropriate DataCollector_{platform} agents
        2. Route merging tasks to MetadataAnalyst
        3. Route quality checks to QualityAssessor
        4. Route acquisition searches to AcquisitionScout
        
        Optimize for parallel execution when possible.
        """
        
        # Configure agent selection strategy
        self.orchestrator.set_selection_strategy("MOST_SPECIFIC")
    
    async def research_track(
        self,
        query: str,
        parallel_search: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> ResearchResult:
        """
        Research a track using the multi-agent system.
        
        This method demonstrates proper Strands orchestration:
        - Uses MultiAgentOrchestrator for coordination
        - Leverages built-in parallel execution
        - Maintains session context across agents
        - Returns structured results
        
        Args:
            query: Track search query (e.g., "Artist - Title")
            parallel_search: Whether to search platforms in parallel
            context: Optional context (genre hints, etc.)
        
        Returns:
            Complete research results as ResearchResult model
        """
        # Create session for this research task
        session_id = f"research_{uuid.uuid4().hex[:8]}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting research for: {query} (session: {session_id})")
        
        try:
            # Step 1: Parallel platform searches
            platform_results = await self._search_platforms(
                query, session_id, parallel_search, context
            )
            
            # Step 2: Merge metadata
            merged_metadata = await self._merge_metadata(
                platform_results, session_id
            )
            
            # Step 3: Assess quality
            quality_report = await self._assess_quality(
                merged_metadata, list(platform_results.keys()), session_id
            )
            
            # Step 4: Find acquisition sources
            acquisition_options = await self._find_sources(
                merged_metadata, session_id
            )
            
            # Step 5: Create final result
            result = ResearchResult(
                query=query,
                success=True,
                metadata=TrackMetadata(**merged_metadata) if merged_metadata else None,
                quality_report=quality_report,
                acquisition_options=acquisition_options,
                platform_results=platform_results,
                session_id=session_id,
                duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )
            
            # Determine if solved
            result.is_solved()
            
            logger.info(f"Research complete: {result.solved} (confidence: {result.confidence:.1%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return ResearchResult(
                query=query,
                success=False,
                solved=False,
                solve_reason=f"Research failed: {str(e)}",
                session_id=session_id
            )
    
    async def _search_platforms(
        self,
        query: str,
        session_id: str,
        parallel: bool,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Search platforms using DataCollector agents."""
        platform_results = {}
        
        if parallel:
            # Create search tasks for parallel execution
            tasks = []
            for platform in self.platforms:
                if platform in self.data_collectors:
                    prompt = f"Search for this track on {platform}: {query}"
                    if context:
                        prompt += f"\nContext: {context}"
                    
                    # Route to specific collector via orchestrator
                    task = self.orchestrator.route_request(
                        prompt,
                        session_id=session_id,
                        agent=self.data_collectors[platform]
                    )
                    tasks.append((platform, task))
            
            # Execute all searches in parallel
            for platform, task in tasks:
                try:
                    result = await task
                    platform_results[platform] = result
                    logger.info(f"Got results from {platform}")
                except Exception as e:
                    logger.error(f"Search failed for {platform}: {e}")
                    platform_results[platform] = {"success": False, "error": str(e)}
        
        else:
            # Sequential search
            for platform in self.platforms:
                if platform in self.data_collectors:
                    try:
                        prompt = f"Search for this track on {platform}: {query}"
                        result = await self.orchestrator.route_request(
                            prompt,
                            session_id=session_id,
                            agent=self.data_collectors[platform]
                        )
                        platform_results[platform] = result
                    except Exception as e:
                        logger.error(f"Search failed for {platform}: {e}")
                        platform_results[platform] = {"success": False, "error": str(e)}
        
        return platform_results
    
    async def _merge_metadata(
        self,
        platform_results: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Merge metadata using the analyst agent."""
        # Prepare results for merging
        valid_results = [
            result for result in platform_results.values()
            if result.get("success", False)
        ]
        
        if not valid_results:
            logger.warning("No valid results to merge")
            return {}
        
        prompt = f"""
        Merge metadata from these platform search results:
        {valid_results}
        
        Use confidence_weighted strategy and resolve any conflicts.
        Return the merged metadata with confidence score.
        """
        
        merged = await self.orchestrator.route_request(
            prompt,
            session_id=session_id,
            agent=self.metadata_analyst
        )
        
        return merged
    
    async def _assess_quality(
        self,
        metadata: Dict[str, Any],
        sources: List[str],
        session_id: str
    ) -> Dict[str, Any]:
        """Assess quality using the assessor agent."""
        if not metadata:
            return {
                "meets_requirements": False,
                "confidence_score": 0.0,
                "metadata_completeness": 0.0
            }
        
        prompt = f"""
        Assess the quality of this merged metadata:
        {metadata}
        
        Sources: {sources}
        
        Check completeness, validate data, and determine if it meets SOLVED criteria.
        """
        
        report = await self.orchestrator.route_request(
            prompt,
            session_id=session_id,
            agent=self.quality_assessor
        )
        
        return report
    
    async def _find_sources(
        self,
        metadata: Dict[str, Any],
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Find acquisition sources using the scout agent."""
        if not metadata:
            return []
        
        prompt = f"""
        Find acquisition sources for this track:
        {metadata}
        
        Find both purchase and streaming options.
        Prioritize high-quality sources suitable for DJs.
        """
        
        sources = await self.orchestrator.route_request(
            prompt,
            session_id=session_id,
            agent=self.acquisition_scout
        )
        
        # Ensure we return a list
        if isinstance(sources, dict):
            # Extract options from response
            options = sources.get("purchase_options", []) + sources.get("streaming_options", [])
            return options
        elif isinstance(sources, list):
            return sources
        else:
            return []
    
    async def quick_search(
        self,
        query: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a quick search on specific platforms.
        
        Args:
            query: Track search query
            platforms: Platforms to search (default: spotify, beatport)
        
        Returns:
            Quick search results
        """
        if platforms is None:
            platforms = ["spotify", "beatport"]
        
        # Filter to available platforms
        available = [p for p in platforms if p in self.data_collectors]
        
        if not available:
            return {"error": "No available platforms specified"}
        
        session_id = f"quick_{uuid.uuid4().hex[:8]}"
        
        # Search platforms
        results = {}
        for platform in available:
            try:
                prompt = f"Quick search on {platform}: {query}"
                result = await self.orchestrator.route_request(
                    prompt,
                    session_id=session_id,
                    agent=self.data_collectors[platform]
                )
                results[platform] = result
            except Exception as e:
                logger.error(f"Quick search failed for {platform}: {e}")
        
        return {
            "query": query,
            "platforms_searched": available,
            "results": results,
            "session_id": session_id
        }