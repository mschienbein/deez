"""Core agent implementation using AWS Strands with OpenAI primary and Bedrock fallback."""

import json
import logging
from typing import Any, Dict, List, Optional

from strands import Agent
from strands.models.openai import OpenAIModel
from strands_agents_tools import (
    calculator,
    current_time,
    file_read,
    file_write,
    http_request,
    python_repl,
    shell,
    use_aws,
)

from ..database.schema import init_database
from ..utils.config import config as app_config

logger = logging.getLogger(__name__)


class MusicAgent:
    """Music discovery and management agent using AWS Strands with OpenAI/Bedrock."""
    
    def __init__(self):
        """Initialize the music agent."""
        self.app_config = app_config
        
        # Initialize database
        self.db_engine, self.db_session = init_database(self.app_config.database.url)
        
        # Configure OpenAI agent
        self.agent = None
        
        self._initialize_agent()
        
        logger.info(f"Music agent '{self.app_config.agent.name}' initialized")
    
    def _initialize_agent(self):
        """Initialize OpenAI agent."""
        if not self.app_config.openai.api_key:
            raise RuntimeError("OpenAI API key is required")
            
        try:
            openai_model = OpenAIModel(
                client_args={
                    "api_key": self.app_config.openai.api_key,
                    "base_url": self.app_config.openai.base_url if self.app_config.openai.base_url else None,
                    "organization": self.app_config.openai.organization if self.app_config.openai.organization else None,
                },
                model_id=self.app_config.openai.model,
                params={
                    "temperature": 0.7,
                    "max_tokens": 4000,
                }
            )
            
            self.agent = Agent(
                model=openai_model,
                tools=self._get_tools(),
                system_prompt=self._get_system_prompt(),
            )
            logger.info(f"OpenAI agent initialized with model: {self.app_config.openai.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI agent: {e}")
            raise RuntimeError(f"Failed to initialize OpenAI agent: {e}")
        
        # Add custom tools
        self._register_custom_tools()
    
    def _get_tools(self):
        """Get the standard Strands tools."""
        return [
            http_request,
            python_repl,
            shell,
            file_read,
            file_write,
            calculator,
            current_time,
            use_aws,
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are an intelligent music discovery and management agent. 
        
        You have access to multiple music platforms:
        - Deezer: Search, stream, and download music with high quality audio
        - Spotify: Browse playlists, discover new music, and track recommendations
        - YouTube: Find music videos, live performances, and rare tracks
        
        Your capabilities include:
        1. Searching for music across all platforms
        2. Creating and managing playlists
        3. Analyzing music trends and user preferences
        4. Downloading music in various formats and qualities
        5. Providing music recommendations based on user taste
        6. Finding rare or unavailable tracks across platforms
        
        You maintain a local database to track:
        - User listening history
        - Saved tracks and playlists
        - Platform-specific IDs for cross-platform matching
        - User preferences and settings
        
        When searching for music:
        - Always try multiple platforms to find the best match
        - Prefer higher quality audio when available
        - Use intelligent fallback if a track isn't available on the preferred platform
        - Match tracks across platforms using metadata like ISRC codes
        
        Be helpful, accurate, and respect user preferences for music quality and platforms.
        """
    
    def _register_custom_tools(self):
        """Register custom tools for music operations."""
        try:
            from ..tools.music_tools import (
                analyze_music_trends,
                create_cross_platform_playlist,
                export_playlist,
                get_track_info,
                search_music,
                match_track_across_platforms,
            )
            
            # Register tools with agent
            self.agent.register_tool(search_music)
            self.agent.register_tool(get_track_info)
            self.agent.register_tool(create_cross_platform_playlist)
            self.agent.register_tool(analyze_music_trends)
            self.agent.register_tool(export_playlist)
            self.agent.register_tool(match_track_across_platforms)
            
            logger.info("Custom music tools registered")
            
        except ImportError as e:
            logger.warning(f"Failed to import custom tools: {e}")
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a chat message and return the response."""
        try:
            # Add context if provided
            if context:
                message = f"Context: {json.dumps(context)}\n\nUser: {message}"
            
            # Process message through agent
            response = self.agent.run(message)
            
            # Log interaction
            logger.info(f"User: {message[:100]}...")
            logger.info(f"Agent: {response[:100]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I encountered an error: {str(e)}. Please try again."
    
    def search(
        self,
        query: str,
        platform: str = "all",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for music across platforms."""
        prompt = f"""Search for music with the following parameters:
        - Query: {query}
        - Platform: {platform}
        - Limit: {limit}
        
        Return the results as a JSON list with track information.
        """
        
        try:
            response = self.agent.run(prompt)
            
            try:
                # Parse JSON response
                results = json.loads(response)
                return results
            except json.JSONDecodeError:
                logger.error(f"Failed to parse search results: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def create_playlist(
        self,
        name: str,
        description: Optional[str] = None,
        tracks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new playlist."""
        prompt = f"""Create a new playlist with:
        - Name: {name}
        - Description: {description or 'No description'}
        - Initial tracks: {json.dumps(tracks) if tracks else 'Empty'}
        
        Return the playlist information as JSON.
        """
        
        try:
            response = self.agent.run(prompt)
            
            try:
                playlist = json.loads(response)
                return playlist
            except json.JSONDecodeError:
                logger.error(f"Failed to parse playlist creation response: {response}")
                return {"error": "Failed to create playlist"}
                
        except Exception as e:
            logger.error(f"Playlist creation error: {e}")
            return {"error": str(e)}
    
    def get_recommendations(
        self,
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get music recommendations based on seeds."""
        prompt = f"""Get music recommendations based on:
        - Seed tracks: {json.dumps(seed_tracks) if seed_tracks else 'None'}
        - Seed artists: {json.dumps(seed_artists) if seed_artists else 'None'}
        - Limit: {limit}
        
        Use listening history and preferences to enhance recommendations.
        Return as JSON list of recommended tracks.
        """
        
        try:
            response = self.agent.run(prompt)
            
            try:
                recommendations = json.loads(response)
                return recommendations
            except json.JSONDecodeError:
                logger.error(f"Failed to parse recommendations: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Recommendations error: {e}")
            return []
    
    def analyze_listening_patterns(self, timeframe: str = "month") -> Dict[str, Any]:
        """Analyze user's listening patterns."""
        prompt = f"""Analyze listening patterns for timeframe: {timeframe}
        
        Include:
        - Top artists and tracks
        - Genre distribution
        - Listening times
        - Platform usage
        - Trend analysis
        
        Return analysis as JSON.
        """
        
        try:
            response = self.agent.run(prompt)
            
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                logger.error(f"Failed to parse analysis: {response}")
                return {"error": "Failed to analyze patterns"}
                
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"error": str(e)}
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent": {
                "available": self.agent is not None,
                "provider": "openai",
                "model": self.app_config.openai.model,
            },
            "configuration": {
                "api_key": "Set" if self.app_config.openai.api_key else "Not set",
                "base_url": self.app_config.openai.base_url,
                "organization": self.app_config.openai.organization,
            }
        }
    
    def close(self):
        """Close the agent and cleanup resources."""
        if hasattr(self, 'db_session'):
            self.db_session.close()
        logger.info("Music agent closed")