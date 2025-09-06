"""
Research Context - Shared state for multi-agent music research

Acts as a blackboard for agent communication and task state management.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum

from ...models import UniversalTrackMetadata, TrackStatus, TrackQuality


class ResearchStatus(Enum):
    """Status of research task."""
    PENDING = "pending"
    PLANNING = "planning"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    RESOLVING = "resolving"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ConflictType(Enum):
    """Types of metadata conflicts."""
    BPM_MISMATCH = "bpm_mismatch"
    KEY_MISMATCH = "key_mismatch"
    DURATION_MISMATCH = "duration_mismatch"
    ARTIST_VARIATION = "artist_variation"
    TITLE_VARIATION = "title_variation"
    GENRE_DISAGREEMENT = "genre_disagreement"
    DATE_CONFLICT = "date_conflict"
    QUALITY_DISCREPANCY = "quality_discrepancy"


@dataclass
class PlatformResult:
    """Result from a single platform search."""
    platform: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    search_query: Optional[str] = None
    num_results: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform': self.platform,
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'search_query': self.search_query,
            'num_results': self.num_results
        }


@dataclass
class ConflictReport:
    """Report of a metadata conflict."""
    conflict_type: ConflictType
    field: str
    values: List[Tuple[str, Any]]  # [(source, value), ...]
    resolution: Optional[Any] = None
    resolution_reason: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.conflict_type.value,
            'field': self.field,
            'values': self.values,
            'resolution': self.resolution,
            'reason': self.resolution_reason,
            'confidence': self.confidence
        }


@dataclass
class QualityReport:
    """Quality assessment report."""
    audio_quality: TrackQuality
    metadata_completeness: float  # 0.0-1.0
    confidence_score: float  # 0.0-1.0
    missing_fields: List[str] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    meets_requirements: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'audio_quality': self.audio_quality.value,
            'metadata_completeness': self.metadata_completeness,
            'confidence_score': self.confidence_score,
            'missing_fields': self.missing_fields,
            'quality_issues': self.quality_issues,
            'recommendations': self.recommendations,
            'meets_requirements': self.meets_requirements
        }


@dataclass
class AcquisitionOption:
    """Option for acquiring a track."""
    source: str
    type: str  # 'purchase', 'download', 'stream'
    quality: TrackQuality
    price: Optional[float] = None
    currency: Optional[str] = None
    url: Optional[str] = None
    requires_subscription: bool = False
    region_restricted: bool = False
    availability: str = "available"  # 'available', 'limited', 'unavailable'
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source': self.source,
            'type': self.type,
            'quality': self.quality.value,
            'price': self.price,
            'currency': self.currency,
            'url': self.url,
            'requires_subscription': self.requires_subscription,
            'region_restricted': self.region_restricted,
            'availability': self.availability,
            'notes': self.notes
        }


@dataclass
class ResearchPlan:
    """Execution plan for research task."""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    parallel_tasks: List[List[str]] = field(default_factory=list)
    priority_platforms: List[str] = field(default_factory=list)
    search_strategies: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # seconds
    
    def add_step(self, step_type: str, details: Dict[str, Any]) -> None:
        """Add a step to the plan."""
        self.steps.append({
            'type': step_type,
            'details': details,
            'status': 'pending'
        })
    
    def add_parallel_group(self, platforms: List[str]) -> None:
        """Add a group of platforms to search in parallel."""
        self.parallel_tasks.append(platforms)


@dataclass
class ResearchContext:
    """
    Shared context for multi-agent music research.
    
    Acts as a blackboard pattern for agent communication.
    """
    
    # Request identification
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    parsed_query: Dict[str, Any] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)
    
    # Progress tracking
    status: ResearchStatus = ResearchStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Research plan
    plan: ResearchPlan = field(default_factory=ResearchPlan)
    
    # Platform results
    platform_results: Dict[str, PlatformResult] = field(default_factory=dict)
    platforms_searched: Set[str] = field(default_factory=set)
    platforms_pending: Set[str] = field(default_factory=set)
    platforms_failed: Set[str] = field(default_factory=set)
    
    # Merged results
    merged_metadata: Optional[UniversalTrackMetadata] = None
    conflicts: List[ConflictReport] = field(default_factory=list)
    
    # Quality assessment
    quality_report: Optional[QualityReport] = None
    acquisition_options: List[AcquisitionOption] = field(default_factory=list)
    
    # Final decision
    is_solved: bool = False
    confidence_score: float = 0.0
    solve_reason: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    
    # Agent communication
    agent_messages: List[Dict[str, Any]] = field(default_factory=list)
    active_agents: Set[str] = field(default_factory=set)
    completed_agents: Set[str] = field(default_factory=set)
    
    # Metrics
    total_api_calls: int = 0
    total_cache_hits: int = 0
    total_time_ms: Optional[int] = None
    
    def update_status(self, new_status: ResearchStatus) -> None:
        """Update research status."""
        self.status = new_status
        self.last_updated = datetime.utcnow()
        
        if new_status in [ResearchStatus.COMPLETED, ResearchStatus.FAILED]:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                delta = self.completed_at - self.started_at
                self.total_time_ms = int(delta.total_seconds() * 1000)
    
    def add_platform_result(self, platform: str, result: PlatformResult) -> None:
        """Add result from a platform search."""
        self.platform_results[platform] = result
        self.platforms_searched.add(platform)
        self.platforms_pending.discard(platform)
        
        if not result.success:
            self.platforms_failed.add(platform)
        
        self.last_updated = datetime.utcnow()
    
    def add_conflict(self, conflict: ConflictReport) -> None:
        """Add a metadata conflict."""
        self.conflicts.append(conflict)
        self.last_updated = datetime.utcnow()
    
    def add_acquisition_option(self, option: AcquisitionOption) -> None:
        """Add an acquisition option."""
        self.acquisition_options.append(option)
        # Sort by quality (highest first) then price (lowest first)
        self.acquisition_options.sort(
            key=lambda x: (-x.quality.value if isinstance(x.quality, Enum) else 0, x.price or float('inf'))
        )
        self.last_updated = datetime.utcnow()
    
    def log_agent_message(self, agent_name: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a message from an agent."""
        self.agent_messages.append({
            'timestamp': datetime.utcnow().isoformat(),
            'agent': agent_name,
            'message': message,
            'data': data
        })
        self.last_updated = datetime.utcnow()
    
    def register_agent(self, agent_name: str) -> None:
        """Register an active agent."""
        self.active_agents.add(agent_name)
        self.log_agent_message(agent_name, f"Agent {agent_name} started")
    
    def complete_agent(self, agent_name: str) -> None:
        """Mark an agent as completed."""
        self.active_agents.discard(agent_name)
        self.completed_agents.add(agent_name)
        self.log_agent_message(agent_name, f"Agent {agent_name} completed")
    
    def get_best_acquisition(self) -> Optional[AcquisitionOption]:
        """Get the best acquisition option."""
        if not self.acquisition_options:
            return None
        
        # Prefer purchase over download over stream
        # Prefer highest quality
        # Prefer lowest price
        
        purchase_options = [o for o in self.acquisition_options if o.type == 'purchase']
        download_options = [o for o in self.acquisition_options if o.type == 'download']
        stream_options = [o for o in self.acquisition_options if o.type == 'stream']
        
        for options in [purchase_options, download_options, stream_options]:
            if options:
                return options[0]  # Already sorted by quality and price
        
        return self.acquisition_options[0] if self.acquisition_options else None
    
    def calculate_completeness(self) -> float:
        """Calculate metadata completeness score."""
        if not self.merged_metadata:
            return 0.0
        
        required_fields = [
            'title', 'artist', 'duration_ms', 'bpm', 'key',
            'genre', 'label', 'release_date', 'isrc'
        ]
        
        present = sum(
            1 for field in required_fields
            if getattr(self.merged_metadata, field, None) is not None
        )
        
        return present / len(required_fields)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            'request_id': self.request_id,
            'query': self.query,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'platforms_searched': list(self.platforms_searched),
            'platform_results': {
                k: v.to_dict() for k, v in self.platform_results.items()
            },
            'merged_metadata': self.merged_metadata.to_dict() if self.merged_metadata else None,
            'conflicts': [c.to_dict() for c in self.conflicts],
            'quality_report': self.quality_report.to_dict() if self.quality_report else None,
            'acquisition_options': [o.to_dict() for o in self.acquisition_options],
            'is_solved': self.is_solved,
            'confidence_score': self.confidence_score,
            'solve_reason': self.solve_reason,
            'recommendations': self.recommendations,
            'metrics': {
                'total_api_calls': self.total_api_calls,
                'total_cache_hits': self.total_cache_hits,
                'total_time_ms': self.total_time_ms,
                'completeness': self.calculate_completeness()
            }
        }
    
    def summary(self) -> str:
        """Get a summary of the research context."""
        lines = [
            f"Research ID: {self.request_id[:8]}",
            f"Query: {self.query}",
            f"Status: {self.status.value}",
            f"Platforms searched: {len(self.platforms_searched)}/{len(self.platforms_pending) + len(self.platforms_searched)}",
        ]
        
        if self.merged_metadata:
            lines.append(f"Track: {self.merged_metadata.artist} - {self.merged_metadata.title}")
            lines.append(f"Completeness: {self.calculate_completeness():.1%}")
        
        if self.quality_report:
            lines.append(f"Quality: {self.quality_report.audio_quality.value}")
            lines.append(f"Confidence: {self.quality_report.confidence_score:.1%}")
        
        if self.is_solved:
            lines.append(f"✅ SOLVED: {self.solve_reason}")
        else:
            lines.append("❌ Not solved")
        
        if self.acquisition_options:
            best = self.get_best_acquisition()
            if best:
                lines.append(f"Best source: {best.source} ({best.type}) - {best.quality.value}")
        
        return "\n".join(lines)