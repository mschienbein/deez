"""
Agent configuration management.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

from ..models.model_config import ModelConfig
from ..tools_manager.tools_manager import ToolsProfile


class AgentMode(Enum):
    """Agent operational modes."""
    INTERACTIVE = "interactive"
    BATCH = "batch"
    API = "api"


@dataclass
class AgentConfig:
    """Configuration for the music agent."""
    
    # Basic settings
    name: str = "MusicAgent"
    mode: AgentMode = AgentMode.INTERACTIVE
    
    # Model configuration
    model_config: Optional[ModelConfig] = None
    
    # Tools configuration
    tools_profile: ToolsProfile = ToolsProfile.STANDARD
    custom_tools_config: Optional[Dict[str, Any]] = None
    
    # Database settings
    database_url: Optional[str] = None
    
    # Behavioral settings
    enable_logging: bool = True
    log_level: str = "INFO"
    max_conversation_turns: int = 50
    response_timeout: int = 30
    
    # Feature flags
    enable_downloads: bool = True
    enable_streaming: bool = True
    enable_analytics: bool = True
    enable_social_features: bool = False
    
    # Integration settings
    enabled_platforms: Optional[List[str]] = None
    platform_priorities: Optional[Dict[str, int]] = None
    
    # Security settings
    require_auth_for_downloads: bool = True
    allow_external_urls: bool = False
    max_file_size_mb: int = 100
    
    def __post_init__(self):
        if self.custom_tools_config is None:
            self.custom_tools_config = {}
        
        if self.enabled_platforms is None:
            self.enabled_platforms = [
                "deezer", "spotify", "youtube", "soundcloud", 
                "bandcamp", "discogs", "tracklists_1001"
            ]
        
        if self.platform_priorities is None:
            self.platform_priorities = {
                "deezer": 1,
                "spotify": 2,
                "youtube": 3,
                "soundcloud": 4,
                "bandcamp": 5,
                "discogs": 6,
                "tracklists_1001": 7
            }
    
    def is_platform_enabled(self, platform: str) -> bool:
        """Check if a platform is enabled."""
        return platform.lower() in [p.lower() for p in self.enabled_platforms]
    
    def get_platform_priority(self, platform: str) -> int:
        """Get priority for a platform (lower number = higher priority)."""
        return self.platform_priorities.get(platform.lower(), 999)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "mode": self.mode.value,
            "model_config": self.model_config.to_dict() if self.model_config else None,
            "tools_profile": self.tools_profile.value,
            "custom_tools_config": self.custom_tools_config,
            "database_url": self.database_url,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "max_conversation_turns": self.max_conversation_turns,
            "response_timeout": self.response_timeout,
            "enable_downloads": self.enable_downloads,
            "enable_streaming": self.enable_streaming,
            "enable_analytics": self.enable_analytics,
            "enable_social_features": self.enable_social_features,
            "enabled_platforms": self.enabled_platforms,
            "platform_priorities": self.platform_priorities,
            "require_auth_for_downloads": self.require_auth_for_downloads,
            "allow_external_urls": self.allow_external_urls,
            "max_file_size_mb": self.max_file_size_mb
        }
    
    @classmethod
    def create_default(cls) -> 'AgentConfig':
        """Create default agent configuration."""
        return cls()
    
    @classmethod
    def create_minimal(cls) -> 'AgentConfig':
        """Create minimal agent configuration."""
        return cls(
            name="MusicAgent-Minimal",
            tools_profile=ToolsProfile.MINIMAL,
            enable_downloads=False,
            enable_streaming=False,
            enable_analytics=False,
            enabled_platforms=["spotify", "youtube"]
        )
    
    @classmethod
    def create_full_featured(cls) -> 'AgentConfig':
        """Create full-featured agent configuration."""
        return cls(
            name="MusicAgent-Full",
            tools_profile=ToolsProfile.FULL,
            enable_downloads=True,
            enable_streaming=True,
            enable_analytics=True,
            enable_social_features=True,
            enabled_platforms=[
                "deezer", "spotify", "youtube", "soundcloud", 
                "bandcamp", "soulseek", "discogs", "tracklists_1001",
                "beatport", "mixcloud"
            ]
        )