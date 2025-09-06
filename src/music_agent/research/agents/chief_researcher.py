"""
Chief Researcher - Orchestrator Agent

The lead agent that coordinates the entire research process, spawning and managing
specialized sub-agents to gather, analyze, and synthesize music metadata.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import re

from .base import ResearchAgent, AgentRole
from ..core.research_context import (
    ResearchContext, ResearchStatus, ResearchPlan,
    QualityReport, TrackQuality
)
from ..models import UniversalTrackMetadata, TrackStatus

logger = logging.getLogger(__name__)


class ChiefResearcher(ResearchAgent):
    """
    Orchestrator agent that manages the entire research workflow.
    
    Responsibilities:
    - Parse and analyze research queries
    - Create execution plans
    - Spawn and coordinate sub-agents
    - Monitor progress and handle failures
    - Synthesize results and make final decisions
    """
    
    # Platform priority for different music genres
    PLATFORM_PRIORITIES = {
        'electronic': ['beatport', 'spotify', 'deezer', 'discogs', 'soundcloud'],
        'general': ['spotify', 'deezer', 'youtube', 'discogs', 'musicbrainz'],
        'classical': ['musicbrainz', 'discogs', 'spotify', 'youtube'],
        'underground': ['soundcloud', 'bandcamp', 'soulseek', 'discogs', 'youtube']
    }
    
    # Minimum thresholds for "SOLVED" status
    SOLVE_THRESHOLDS = {
        'metadata_completeness': 0.8,  # 80% of required fields
        'confidence_score': 0.7,        # 70% confidence
        'min_platforms': 2,              # At least 2 platforms confirmed
    }
    
    def __init__(self, context: ResearchContext, config: Optional[Dict[str, Any]] = None):
        """Initialize Chief Researcher."""
        super().__init__(
            name="ChiefResearcher",
            role=AgentRole.ORCHESTRATOR,
            context=context,
            config=config or {}
        )
        
        # Configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.parallel_agents = self.config.get('parallel_agents', 5)
        self.timeout_per_agent = self.config.get('timeout_per_agent', 30)
        
        # State
        self.sub_agents: List[ResearchAgent] = []
        self.retry_counts: Dict[str, int] = {}
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the orchestration workflow.
        
        Returns:
            Final research results
        """
        self.start()
        self.context.update_status(ResearchStatus.PLANNING)
        
        try:
            # Step 1: Analyze query and create plan
            self.log("Analyzing research query")
            await self._analyze_query()
            plan = await self._create_research_plan()
            self.context.plan = plan
            
            # Step 2: Execute parallel search phase
            self.context.update_status(ResearchStatus.SEARCHING)
            self.log("Starting parallel platform searches")
            await self._execute_parallel_search(plan)
            
            # Step 3: Analyze and merge results
            self.context.update_status(ResearchStatus.ANALYZING)
            self.log("Analyzing and merging metadata")
            await self._analyze_and_merge_results()
            
            # Step 4: Validate and assess quality
            self.context.update_status(ResearchStatus.VALIDATING)
            self.log("Validating metadata quality")
            await self._validate_and_assess_quality()
            
            # Step 5: Find acquisition options
            self.context.update_status(ResearchStatus.RESOLVING)
            self.log("Finding acquisition options")
            await self._find_acquisition_options()
            
            # Step 6: Make final decision
            self.log("Making final decision")
            await self._make_final_decision()
            
            # Complete successfully
            self.context.update_status(ResearchStatus.COMPLETED)
            self.complete(success=True)
            
            return {
                'success': True,
                'solved': self.context.is_solved,
                'metadata': self.context.merged_metadata,
                'quality_report': self.context.quality_report,
                'acquisition_options': self.context.acquisition_options,
                'confidence': self.context.confidence_score,
                'reason': self.context.solve_reason
            }
            
        except Exception as e:
            self.log_error(f"Orchestration failed: {str(e)}")
            self.context.update_status(ResearchStatus.FAILED)
            self.complete(success=False)
            
            return {
                'success': False,
                'error': str(e),
                'partial_results': self.context.merged_metadata
            }
    
    async def _analyze_query(self) -> None:
        """Parse and analyze the search query."""
        query = self.context.query
        
        # Basic parsing - extract artist and title
        parsed = {
            'original': query,
            'artist': None,
            'title': None,
            'remixer': None,
            'remix_type': None,
            'features': []
        }
        
        # Try common patterns
        patterns = [
            r'^(.+?)\s*-\s*(.+)$',  # Artist - Title
            r'^(.+?)\s*–\s*(.+)$',  # Artist – Title (em dash)
            r'^(.+?)\s*:\s*(.+)$',  # Artist: Title
        ]
        
        for pattern in patterns:
            match = re.match(pattern, query)
            if match:
                parsed['artist'] = match.group(1).strip()
                parsed['title'] = match.group(2).strip()
                break
        
        # If no pattern matched, treat whole query as title
        if not parsed['artist']:
            parsed['title'] = query
        
        # Extract remix info
        if parsed['title']:
            remix_pattern = r'\(([^)]*(?:remix|mix|edit|bootleg|rework)[^)]*)\)'
            remix_match = re.search(remix_pattern, parsed['title'], re.IGNORECASE)
            if remix_match:
                parsed['remix_type'] = remix_match.group(1)
                # Try to extract remixer
                remixer_pattern = r'(\w+(?:\s+\w+)*)\s+(?:remix|mix)'
                remixer_match = re.search(remixer_pattern, parsed['remix_type'], re.IGNORECASE)
                if remixer_match:
                    parsed['remixer'] = remixer_match.group(1)
        
        # Extract featuring artists
        feat_pattern = r'(?:feat\.|featuring|ft\.)\s+([^()]+)'
        feat_match = re.search(feat_pattern, query, re.IGNORECASE)
        if feat_match:
            parsed['features'] = [a.strip() for a in feat_match.group(1).split(',')]
        
        self.context.parsed_query = parsed
        self.log(f"Parsed query: {parsed}")
    
    async def _create_research_plan(self) -> ResearchPlan:
        """Create an execution plan based on the query."""
        plan = ResearchPlan()
        
        # Determine genre hint from query or context
        genre_hint = self._detect_genre_hint()
        
        # Select platforms based on genre
        platforms = self.PLATFORM_PRIORITIES.get(genre_hint, self.PLATFORM_PRIORITIES['general'])
        
        # Add additional platforms if not in list
        all_platforms = set(platforms)
        for platform_list in self.PLATFORM_PRIORITIES.values():
            all_platforms.update(platform_list)
        
        # Limit to available platforms (would check tool registry in real implementation)
        available_platforms = ['spotify', 'beatport', 'discogs', 'deezer', 'soundcloud', 
                              'youtube', 'musicbrainz', 'genius', 'lastfm']
        platforms = [p for p in platforms if p in available_platforms]
        
        # Create parallel search groups
        # Group 1: High-priority platforms (search in parallel)
        plan.add_parallel_group(platforms[:3])
        
        # Group 2: Secondary platforms (if needed)
        if len(platforms) > 3:
            plan.add_parallel_group(platforms[3:6])
        
        # Group 3: Fallback platforms
        if len(platforms) > 6:
            plan.add_parallel_group(platforms[6:])
        
        plan.priority_platforms = platforms[:3]
        
        # Add search strategies
        plan.search_strategies = [
            'exact_match',      # Try exact artist + title
            'fuzzy_match',      # Allow some variation
            'partial_match',    # Search by title only
            'isrc_lookup'       # If ISRC found, use it
        ]
        
        # Add workflow steps
        plan.add_step('search', {'platforms': platforms[:3], 'strategy': 'exact_match'})
        plan.add_step('merge', {'method': 'confidence_weighted'})
        plan.add_step('validate', {'check_conflicts': True})
        plan.add_step('assess_quality', {'thresholds': self.SOLVE_THRESHOLDS})
        plan.add_step('find_sources', {'types': ['purchase', 'download', 'stream']})
        plan.add_step('decide', {'criteria': 'best_quality_available'})
        
        plan.estimated_duration = 30  # seconds
        
        self.log(f"Created research plan with {len(platforms)} platforms")
        return plan
    
    def _detect_genre_hint(self) -> str:
        """Detect genre hint from query or context."""
        query_lower = self.context.query.lower()
        
        # Simple keyword detection
        electronic_keywords = ['techno', 'house', 'trance', 'dubstep', 'dnb', 'drum and bass']
        classical_keywords = ['symphony', 'concerto', 'sonata', 'opus']
        underground_keywords = ['bootleg', 'unreleased', 'white label', 'promo']
        
        for keyword in electronic_keywords:
            if keyword in query_lower:
                return 'electronic'
        
        for keyword in classical_keywords:
            if keyword in query_lower:
                return 'classical'
        
        for keyword in underground_keywords:
            if keyword in query_lower:
                return 'underground'
        
        return 'general'
    
    async def _execute_parallel_search(self, plan: ResearchPlan) -> None:
        """Execute parallel searches across platforms."""
        # For each parallel group in the plan
        for group_idx, platform_group in enumerate(plan.parallel_tasks):
            self.log(f"Executing parallel search group {group_idx + 1}: {platform_group}")
            
            # Create DataCollector agents for each platform
            tasks = []
            for platform in platform_group:
                if platform not in self.context.platforms_searched:
                    self.context.platforms_pending.add(platform)
                    
                    # Create data collector for this platform
                    collector = await self._create_data_collector(platform)
                    if collector:
                        self.sub_agents.append(collector)
                        tasks.append(self._run_agent_with_timeout(collector))
            
            # Execute all collectors in parallel
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.log_error(f"Platform search failed: {result}")
                    else:
                        self.log(f"Platform search completed: {platform_group[i]}")
            
            # Check if we have enough data to stop early
            if self._has_sufficient_data():
                self.log("Sufficient data collected, skipping remaining searches")
                break
    
    async def _create_data_collector(self, platform: str) -> Optional['DataCollector']:
        """Create a DataCollector agent for a specific platform."""
        # Import here to avoid circular dependency
        from .data_collector import DataCollector
        
        try:
            collector = DataCollector(
                platform=platform,
                context=self.context,
                config={
                    'timeout': self.timeout_per_agent,
                    'max_retries': 3,
                    'cache_enabled': True
                }
            )
            return collector
        except Exception as e:
            self.log_error(f"Failed to create collector for {platform}: {e}")
            return None
    
    async def _run_agent_with_timeout(self, agent: ResearchAgent) -> Any:
        """Run an agent with timeout."""
        try:
            return await asyncio.wait_for(
                agent.execute(),
                timeout=self.timeout_per_agent
            )
        except asyncio.TimeoutError:
            agent.log_error(f"Agent timed out after {self.timeout_per_agent}s")
            agent.complete(success=False)
            return None
    
    def _has_sufficient_data(self) -> bool:
        """Check if we have enough data to proceed."""
        # Need at least 2 successful platform results
        successful_platforms = sum(
            1 for r in self.context.platform_results.values()
            if r.success and r.data
        )
        
        if successful_platforms >= self.SOLVE_THRESHOLDS['min_platforms']:
            # Check if we have critical fields
            has_title = any(
                r.data.get('title') for r in self.context.platform_results.values()
                if r.success and r.data
            )
            has_artist = any(
                r.data.get('artist') for r in self.context.platform_results.values()
                if r.success and r.data
            )
            
            return has_title and has_artist
        
        return False
    
    async def _analyze_and_merge_results(self) -> None:
        """Analyze and merge results from all platforms."""
        # Import here to avoid circular dependency
        from .metadata_analyst import MetadataAnalyst
        
        analyst = MetadataAnalyst(
            context=self.context,
            config={'merge_strategy': 'confidence_weighted'}
        )
        self.sub_agents.append(analyst)
        
        await analyst.execute()
        
        if self.context.merged_metadata:
            self.log(f"Metadata merged successfully: {self.context.merged_metadata.title}")
        else:
            self.log_error("Failed to merge metadata")
    
    async def _validate_and_assess_quality(self) -> None:
        """Validate metadata and assess quality."""
        # Import here to avoid circular dependency
        from .quality_assessor import QualityAssessor
        
        assessor = QualityAssessor(
            context=self.context,
            config={'thresholds': self.SOLVE_THRESHOLDS}
        )
        self.sub_agents.append(assessor)
        
        await assessor.execute()
        
        if self.context.quality_report:
            self.log(f"Quality assessment complete: {self.context.quality_report.confidence_score:.1%}")
    
    async def _find_acquisition_options(self) -> None:
        """Find options for acquiring the track."""
        # Import here to avoid circular dependency
        from .acquisition_scout import AcquisitionScout
        
        scout = AcquisitionScout(
            context=self.context,
            config={'check_all_sources': True}
        )
        self.sub_agents.append(scout)
        
        await scout.execute()
        
        if self.context.acquisition_options:
            self.log(f"Found {len(self.context.acquisition_options)} acquisition options")
    
    async def _make_final_decision(self) -> None:
        """Make final decision on whether track is solved."""
        if not self.context.merged_metadata:
            self.context.is_solved = False
            self.context.solve_reason = "No metadata found"
            return
        
        # Check quality report
        if self.context.quality_report:
            meets_quality = (
                self.context.quality_report.meets_requirements and
                self.context.quality_report.metadata_completeness >= self.SOLVE_THRESHOLDS['metadata_completeness'] and
                self.context.quality_report.confidence_score >= self.SOLVE_THRESHOLDS['confidence_score']
            )
        else:
            meets_quality = False
        
        # Check acquisition options
        has_good_source = False
        if self.context.acquisition_options:
            best = self.context.get_best_acquisition()
            if best and best.quality in [TrackQuality.LOSSLESS, TrackQuality.HIGH]:
                has_good_source = True
        
        # Make decision
        if meets_quality and has_good_source:
            self.context.is_solved = True
            self.context.merged_metadata.status = TrackStatus.SOLVED
            
            best_source = self.context.get_best_acquisition()
            self.context.solve_reason = (
                f"Track resolved with {self.context.quality_report.confidence_score:.0%} confidence. "
                f"Best source: {best_source.source} ({best_source.quality.value})"
            )
            
            self.context.confidence_score = self.context.quality_report.confidence_score
            
        elif meets_quality:
            self.context.is_solved = False
            self.context.merged_metadata.status = TrackStatus.DISCOVERED
            self.context.solve_reason = "Metadata complete but no high-quality source found"
            self.context.confidence_score = self.context.quality_report.confidence_score * 0.8
            
        else:
            self.context.is_solved = False
            self.context.merged_metadata.status = TrackStatus.DISCOVERED
            
            issues = []
            if self.context.quality_report:
                if self.context.quality_report.metadata_completeness < self.SOLVE_THRESHOLDS['metadata_completeness']:
                    issues.append(f"metadata only {self.context.quality_report.metadata_completeness:.0%} complete")
                if self.context.quality_report.confidence_score < self.SOLVE_THRESHOLDS['confidence_score']:
                    issues.append(f"confidence only {self.context.quality_report.confidence_score:.0%}")
            
            self.context.solve_reason = f"Not solved: {', '.join(issues) if issues else 'insufficient data'}"
            self.context.confidence_score = self.context.quality_report.confidence_score if self.context.quality_report else 0.0
        
        self.log(f"Final decision: {'SOLVED' if self.context.is_solved else 'NOT SOLVED'} - {self.context.solve_reason}")