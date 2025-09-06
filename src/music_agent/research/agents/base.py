"""
Base Research Agent - Foundation for all research agents

Provides common functionality and interface for specialized agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

from ..core.research_context import ResearchContext

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles for research agents."""
    ORCHESTRATOR = "orchestrator"
    DATA_COLLECTOR = "data_collector"
    METADATA_ANALYST = "metadata_analyst"
    QUALITY_ASSESSOR = "quality_assessor"
    ACQUISITION_SCOUT = "acquisition_scout"
    CRITIC = "critic"


class ResearchAgent(ABC):
    """
    Base class for all research agents.
    
    Provides common functionality for agent lifecycle, logging, and context management.
    """
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        context: ResearchContext,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize research agent.
        
        Args:
            name: Agent name/identifier
            role: Agent's role in the system
            context: Shared research context
            config: Optional agent configuration
        """
        self.name = name
        self.role = role
        self.context = context
        self.config = config or {}
        
        # Agent state
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = "initialized"
        self.errors: List[str] = []
        
        # Performance metrics
        self.api_calls = 0
        self.cache_hits = 0
        self.tokens_used = 0
        
        # Register with context
        self.context.register_agent(self.name)
        
        logger.info(f"Initialized {self.role.value} agent: {self.name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main task.
        
        Returns:
            Dictionary with execution results
        """
        pass
    
    def log(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a message to context and logger."""
        self.context.log_agent_message(self.name, message, data)
        logger.info(f"[{self.name}] {message}")
    
    def log_error(self, error: str) -> None:
        """Log an error."""
        self.errors.append(error)
        self.log(f"ERROR: {error}")
        logger.error(f"[{self.name}] {error}")
    
    def start(self) -> None:
        """Mark agent as started."""
        self.started_at = datetime.utcnow()
        self.status = "running"
        self.log("Agent started")
    
    def complete(self, success: bool = True) -> None:
        """Mark agent as completed."""
        self.completed_at = datetime.utcnow()
        self.status = "completed" if success else "failed"
        self.context.complete_agent(self.name)
        
        # Update context metrics
        self.context.total_api_calls += self.api_calls
        self.context.total_cache_hits += self.cache_hits
        
        duration = (self.completed_at - self.started_at).total_seconds() if self.started_at else 0
        self.log(f"Agent completed in {duration:.2f}s", {
            'success': success,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'errors': len(self.errors)
        })
    
    def should_stop(self) -> bool:
        """Check if agent should stop execution."""
        # Check for timeout
        if self.started_at:
            duration = (datetime.utcnow() - self.started_at).total_seconds()
            max_duration = self.config.get('max_duration', 60)  # Default 60s timeout
            if duration > max_duration:
                self.log_error(f"Agent timeout after {duration:.1f}s")
                return True
        
        # Check for max errors
        max_errors = self.config.get('max_errors', 5)
        if len(self.errors) >= max_errors:
            self.log_error(f"Max errors reached: {len(self.errors)}")
            return True
        
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        duration = None
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            duration = (end_time - self.started_at).total_seconds()
        
        return {
            'name': self.name,
            'role': self.role.value,
            'status': self.status,
            'duration': duration,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'tokens_used': self.tokens_used,
            'errors': len(self.errors)
        }