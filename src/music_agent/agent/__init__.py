"""
Music Agent - Refactored Architecture

Provides a comprehensive music discovery and management agent with modular design,
multiple AI model support, and intelligent tool management.
"""

# Main agent class
from .music_agent import MusicAgent

# Configuration classes
from .config import AgentConfig, SystemPromptManager, PromptTemplate

# Model management
from .models import ModelConfig, ModelProvider, ModelManager

# Tools management
from .tools_manager import ToolsManager, ToolsProfile, StandardToolsProvider

# Legacy compatibility (will be deprecated)
try:
    from .core import MusicAgent as LegacyMusicAgent
except ImportError:
    LegacyMusicAgent = None

__all__ = [
    # Main agent
    'MusicAgent',
    
    # Configuration
    'AgentConfig',
    'SystemPromptManager', 
    'PromptTemplate',
    
    # Models
    'ModelConfig',
    'ModelProvider',
    'ModelManager',
    
    # Tools
    'ToolsManager',
    'ToolsProfile',
    'StandardToolsProvider',
    
    # Legacy (deprecated)
    'LegacyMusicAgent'
]


def create_agent(
    name: str = "MusicAgent",
    tools_profile: ToolsProfile = ToolsProfile.STANDARD,
    openai_api_key: str = None,
    openai_model: str = "gpt-4",
    **kwargs
) -> MusicAgent:
    """
    Convenience function to create a music agent with common settings.
    
    Args:
        name: Agent name
        tools_profile: Tools profile to use
        openai_api_key: OpenAI API key
        openai_model: OpenAI model to use
        **kwargs: Additional configuration options
    
    Returns:
        Configured MusicAgent instance
    
    Example:
        >>> agent = create_agent(
        >>>     name="MyMusicAgent",
        >>>     tools_profile=ToolsProfile.FULL,
        >>>     openai_api_key="your-api-key"
        >>> )
        >>> response = agent.chat("Find me some techno music")
    """
    # Create model configuration
    if openai_api_key:
        model_config = ModelConfig.from_openai_config(
            model_id=openai_model,
            api_key=openai_api_key
        )
    else:
        model_config = None  # Will use app config defaults
    
    # Create agent configuration
    agent_config = AgentConfig(
        name=name,
        tools_profile=tools_profile,
        model_config=model_config,
        **kwargs
    )
    
    # Create and return agent
    return MusicAgent(agent_config)


def create_minimal_agent(**kwargs) -> MusicAgent:
    """Create agent with minimal tools and features."""
    return create_agent(
        name="MusicAgent-Minimal",
        tools_profile=ToolsProfile.MINIMAL,
        **kwargs
    )


def create_full_agent(**kwargs) -> MusicAgent:
    """Create agent with all available tools and features."""
    return create_agent(
        name="MusicAgent-Full", 
        tools_profile=ToolsProfile.FULL,
        **kwargs
    )