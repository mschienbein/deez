"""
Refactored Music Agent - Main Agent Class

A comprehensive music discovery and management agent with modular architecture.
Supports multiple AI models, intelligent tool management, and extensive platform integrations.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..database.schema import init_database
from ..utils.config import config as app_config

from .models import ModelConfig, ModelProvider, ModelManager
from .tools_manager import ToolsManager, ToolsProfile
from .config import AgentConfig, SystemPromptManager, PromptTemplate

logger = logging.getLogger(__name__)


class MusicAgent:
    """
    Advanced music discovery and management agent.
    
    Features:
    - Multi-model support (OpenAI, Bedrock)
    - Intelligent tool management with profiles
    - Comprehensive platform integrations
    - Advanced conversation handling
    - Database integration for persistence
    """
    
    def __init__(self, agent_config: Optional[AgentConfig] = None):
        """
        Initialize the music agent.
        
        Args:
            agent_config: Agent configuration (uses default if not provided)
        """
        # Configuration
        self.config = agent_config or AgentConfig.create_default()
        self.app_config = app_config
        
        # Initialize logging
        if self.config.enable_logging:
            self._setup_logging()
        
        # Core components
        self.model_manager = None
        self.tools_manager = ToolsManager()
        self.prompt_manager = SystemPromptManager()
        self.agent = None
        
        # Database connection
        self.db_engine = None
        self.db_session = None
        
        # State tracking
        self.conversation_turns = 0
        self.initialized = False
        
        # Initialize components
        self._initialize()
        
        logger.info(f"Music agent '{self.config.name}' initialized successfully")
    
    def _setup_logging(self):
        """Configure logging based on agent config."""
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Configure logger for this specific agent
        agent_logger = logging.getLogger(f"music_agent.{self.config.name}")
        agent_logger.setLevel(level)
        
        if not agent_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            agent_logger.addHandler(handler)
    
    def _initialize(self):
        """Initialize all agent components."""
        try:
            # Initialize database
            self._initialize_database()
            
            # Initialize model manager
            self._initialize_model()
            
            # Initialize agent with tools
            self._initialize_agent()
            
            self.initialized = True
            logger.info("All agent components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise RuntimeError(f"Agent initialization failed: {e}")
    
    def _initialize_database(self):
        """Initialize database connection."""
        try:
            database_url = self.config.database_url or self.app_config.database.url
            self.db_engine, self.db_session = init_database(database_url)
            logger.info("Database connection established")
            
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            # Continue without database - some features will be limited
    
    def _initialize_model(self):
        """Initialize AI model manager."""
        if not self.config.model_config:
            # Create default model config from app config
            self.config.model_config = ModelConfig.from_openai_config(
                model_id=self.app_config.openai.model,
                api_key=self.app_config.openai.api_key,
                base_url=self.app_config.openai.base_url,
                organization=self.app_config.openai.organization
            )
        
        self.model_manager = ModelManager(self.config.model_config)
        
        if not self.model_manager.initialize():
            raise RuntimeError("Failed to initialize AI model")
    
    def _initialize_agent(self):
        """Initialize the Strands agent with tools and prompt."""
        # Get tools based on configuration
        tools = self._get_configured_tools()
        
        # Get system prompt
        system_prompt = self._get_system_prompt()
        
        # Create agent
        self.agent = self.model_manager.create_agent(tools, system_prompt)
        
        if not self.agent:
            raise RuntimeError("Failed to create Strands agent")
        
        logger.info(f"Agent initialized with {len(tools)} tools")
    
    def _get_configured_tools(self) -> List[Any]:
        """Get tools based on agent configuration."""
        if self.config.custom_tools_config:
            # Use custom tool configuration
            return self.tools_manager.get_custom_tools(**self.config.custom_tools_config)
        else:
            # Use profile-based tool selection
            tools = self.tools_manager.get_tools_by_profile(self.config.tools_profile)
            
            # Apply feature-based filtering
            if not self.config.enable_downloads:
                # Filter out download tools
                from ..tools.registry import ToolCategory
                download_tools = set(self.tools_manager.tool_registry.get_tools_by_category(ToolCategory.DOWNLOAD))
                tools = [tool for tool in tools if tool not in download_tools]
            
            if not self.config.enable_social_features:
                # Filter out social tools
                from ..tools.registry import ToolCategory
                social_tools = set(self.tools_manager.tool_registry.get_tools_by_category(ToolCategory.SOCIAL))
                tools = [tool for tool in tools if tool not in social_tools]
            
            return tools
    
    def _get_system_prompt(self) -> str:
        """Generate system prompt based on configuration."""
        # Determine prompt template based on tools profile
        template_mapping = {
            ToolsProfile.MINIMAL: PromptTemplate.MINIMAL,
            ToolsProfile.STANDARD: PromptTemplate.DEFAULT,
            ToolsProfile.FULL: PromptTemplate.DEFAULT,
            ToolsProfile.SEARCH_FOCUSED: PromptTemplate.SEARCH_FOCUSED,
            ToolsProfile.DOWNLOAD_FOCUSED: PromptTemplate.DOWNLOAD_FOCUSED,
            ToolsProfile.ANALYTICS_FOCUSED: PromptTemplate.ANALYTICS_FOCUSED
        }
        
        template = template_mapping.get(self.config.tools_profile, PromptTemplate.DEFAULT)
        
        return self.prompt_manager.get_prompt(
            template=template,
            enabled_platforms=self.config.enabled_platforms,
            tools_profile=self.config.tools_profile
        )
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a chat message and return the response.
        
        Args:
            message: User message
            context: Optional conversation context
        
        Returns:
            Agent response
        """
        if not self.initialized:
            return "Agent not properly initialized. Please check configuration and try again."
        
        # Check conversation limits
        if self.conversation_turns >= self.config.max_conversation_turns:
            logger.warning(f"Maximum conversation turns ({self.config.max_conversation_turns}) reached")
            return "Maximum conversation length reached. Please start a new conversation."
        
        try:
            # Prepare message with context
            if context:
                enhanced_message = f"Context: {json.dumps(context, indent=2)}\\n\\nUser: {message}"
            else:
                enhanced_message = message
            
            # Process message
            start_time = datetime.now()
            result = self.agent(enhanced_message)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract response
            response = self._extract_response(result)
            
            # Update conversation state
            self.conversation_turns += 1
            
            # Log interaction
            if self.config.enable_logging:
                logger.info(f"Conversation turn {self.conversation_turns} - Processing time: {processing_time:.2f}s")
                logger.debug(f"User: {message[:100]}...")
                logger.debug(f"Agent: {response[:100]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question."
    
    def _extract_response(self, result) -> str:
        """Extract text response from agent result."""
        if hasattr(result, 'output'):
            return result.output
        elif hasattr(result, 'text'):
            return result.text
        elif isinstance(result, str):
            return result
        else:
            return str(result)
    
    def search(
        self,
        query: str,
        platform: str = "all",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Direct search interface for music content.
        
        Args:
            query: Search query
            platform: Platform to search ("all" for multi-platform)
            limit: Maximum results
        
        Returns:
            List of search results
        """
        try:
            # Use the core search tool directly
            from ..tools.core.search import search_music
            results = search_music(query, platform, limit)
            return results if results else []
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def create_playlist(
        self,
        name: str,
        description: Optional[str] = None,
        tracks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Direct playlist creation interface.
        
        Args:
            name: Playlist name
            description: Optional description
            tracks: Optional list of track specifications
        
        Returns:
            Playlist creation result
        """
        try:
            # Use the core playlist tool directly
            from ..tools.core.playlist import create_cross_platform_playlist
            
            track_list = tracks or []
            result = create_cross_platform_playlist(name, track_list)
            return result
            
        except Exception as e:
            logger.error(f"Playlist creation error: {e}")
            return {"error": str(e)}
    
    def get_recommendations(
        self,
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get music recommendations.
        
        Args:
            seed_tracks: Optional seed tracks
            seed_artists: Optional seed artists
            limit: Maximum recommendations
        
        Returns:
            List of recommended tracks
        """
        prompt = f"""Get music recommendations based on:
- Seed tracks: {json.dumps(seed_tracks) if seed_tracks else 'None'}
- Seed artists: {json.dumps(seed_artists) if seed_artists else 'None'}
- Limit: {limit}

Use listening history and preferences to enhance recommendations.
Return as JSON list of recommended tracks."""
        
        try:
            response = self.chat(prompt)
            
            # Try to parse as JSON
            try:
                recommendations = json.loads(response)
                return recommendations if isinstance(recommendations, list) else []
            except json.JSONDecodeError:
                logger.error(f"Failed to parse recommendations: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            return []
    
    def analyze_patterns(self, timeframe: str = "month") -> Dict[str, Any]:
        """
        Analyze listening patterns and trends.
        
        Args:
            timeframe: Analysis timeframe
        
        Returns:
            Analysis results
        """
        try:
            # Use the core analytics tool directly
            from ..tools.core.recommendations import analyze_music_trends
            return analyze_music_trends(timeframe)
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"error": str(e)}
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status information."""
        status = {
            "agent": {
                "name": self.config.name,
                "mode": self.config.mode.value,
                "initialized": self.initialized,
                "conversation_turns": self.conversation_turns,
                "max_turns": self.config.max_conversation_turns
            },
            "model": self.model_manager.get_model_info() if self.model_manager else None,
            "tools": self.tools_manager.get_tools_summary(),
            "database": {
                "connected": self.db_engine is not None,
                "url": self.config.database_url or "default"
            },
            "configuration": {
                "tools_profile": self.config.tools_profile.value,
                "enabled_platforms": self.config.enabled_platforms,
                "features": {
                    "downloads": self.config.enable_downloads,
                    "streaming": self.config.enable_streaming,
                    "analytics": self.config.enable_analytics,
                    "social": self.config.enable_social_features
                }
            }
        }
        
        return status
    
    def reset_conversation(self):
        """Reset conversation state."""
        self.conversation_turns = 0
        logger.info("Conversation state reset")
    
    def update_configuration(self, new_config: AgentConfig):
        """
        Update agent configuration (requires reinitialization).
        
        Args:
            new_config: New agent configuration
        """
        self.config = new_config
        self.initialized = False
        
        try:
            self._initialize()
            logger.info("Agent configuration updated successfully")
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise
    
    def close(self):
        """Close the agent and cleanup resources."""
        if hasattr(self, 'db_session') and self.db_session:
            self.db_session.close()
        
        self.conversation_turns = 0
        self.initialized = False
        
        logger.info(f"Music agent '{self.config.name}' closed")