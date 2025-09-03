"""
Graphiti Memory Integration for Music Agent
Manages temporal knowledge graph for music discovery and preferences
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.nodes import EntityNode, EpisodicNode
from graphiti_core.edges import EntityEdge, EpisodicEdge
from graphiti_core.llm_client import OpenAIClient, LLMConfig
from graphiti_core.embedder import OpenAIEmbedder
from graphiti_core.embedder.openai import OpenAIEmbedderConfig

# Import our request handler
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.music_agent.utils.request_handler import RequestHandler

# from ..database.schema import Track, Playlist  # TODO: Add when schema is ready
# from ..utils.config import config  # Not needed with env vars

logger = logging.getLogger(__name__)


class MusicMemory:
    """Graphiti-based memory system for music agent"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "deezmusic123")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "music")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.graphiti: Optional[Graphiti] = None
        self.initialized = False
        self.session_id = None  # Will be set during initialize
        
    async def initialize(self, session_id: Optional[str] = None):
        """Initialize Graphiti connection and indices"""
        
        if self.initialized:
            return
            
        # Generate or use provided session ID
        import uuid
        self.session_id = session_id or f"music_session_{uuid.uuid4().hex[:8]}"
            
        logger.info(f"Initializing Graphiti memory system for session {self.session_id}...")
        
        try:
            # Create Neo4j driver with the correct database
            neo4j_driver = Neo4jDriver(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password,
                database=self.neo4j_database
            )
            
            # Configure LLM (using gpt-5-nano like in sim)
            llm_config = LLMConfig(
                api_key=self.openai_api_key,
                model="gpt-5-nano",  # Using gpt-5-nano
                max_tokens=200000
                # Note: temperature not supported on gpt-5-nano
            )
            
            # Configure embedder
            embedder_config = OpenAIEmbedderConfig(
                api_key=self.openai_api_key,
                model="text-embedding-3-small"  # Latest small embeddings model
            )
            
            # Initialize Graphiti with the driver and AI clients
            self.graphiti = Graphiti(
                graph_driver=neo4j_driver,
                llm_client=OpenAIClient(config=llm_config),
                embedder=OpenAIEmbedder(config=embedder_config),
                # Optimize for performance (matching sim settings)
                max_coroutines=20,  # Allow more parallel processing
                store_raw_episode_content=False,  # Don't store raw content to save space
                ensure_ascii=False  # Allow unicode without escaping
            )
            
            # Build indices & constraints once (idempotent)
            try:
                await self.graphiti.build_indices_and_constraints()
                logger.info("Graphiti indices and constraints ensured")
            except Exception as e:
                logger.warning(f"Skipping build_indices_and_constraints: {e}")
            
            # Build music-specific indices
            await self._build_indices()
            
            self.initialized = True
            logger.info(f"✅ Graphiti memory system initialized for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise
    
    async def _build_indices(self):
        """Create Neo4j indices for music data"""
        
        await self.graphiti.build_indices_and_constraints()
        
        # Music-specific indices
        music_indices = [
            "CREATE INDEX track_isrc IF NOT EXISTS FOR (n:Track) ON (n.isrc)",
            "CREATE INDEX track_spotify IF NOT EXISTS FOR (n:Track) ON (n.spotify_id)",
            "CREATE INDEX track_deezer IF NOT EXISTS FOR (n:Track) ON (n.deezer_id)",
            "CREATE INDEX track_bpm IF NOT EXISTS FOR (n:Track) ON (n.bpm)",
            "CREATE INDEX track_key IF NOT EXISTS FOR (n:Track) ON (n.key)",
            "CREATE FULLTEXT INDEX track_search IF NOT EXISTS FOR (n:Track) ON EACH [n.title, n.artist, n.album]"
        ]
        
        for index in music_indices:
            try:
                await self.graphiti.driver.execute_query(index)
            except Exception:
                pass  # Index might already exist
    
    async def _add_episode_safe(
        self,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: datetime,
        max_length: int = 2000,
        timeout_seconds: int = 30
    ):
        """
        Safely add episode with truncation and timeout handling.
        Prevents JSON parsing errors from oversized responses.
        """
        # Ensure episode_body is not empty
        if not episode_body or not episode_body.strip():
            logger.warning(f"Empty episode body for {name}, using placeholder")
            episode_body = f"[Episode: {name} at {reference_time}]"
        
        # Truncate episode body if too long
        original_length = len(episode_body)
        if original_length > max_length:
            episode_body = episode_body[:max_length - 3] + "..."
            logger.debug(f"Truncated episode body from {original_length} to {max_length}")
        
        try:
            # Use timeout handler
            result = await RequestHandler.with_timeout(
                self.graphiti.add_episode(
                    name=name,
                    episode_body=episode_body,
                    source_description=source_description,
                    reference_time=reference_time,
                    group_id=self.session_id
                ),
                timeout_seconds=timeout_seconds
            )
            
            if result is None:
                logger.warning(f"Episode add timed out for {name}")
                return None
                
            return result
            
        except Exception as e:
            # Handle JSON parsing errors specifically
            if "Invalid JSON" in str(e) or "EOF while parsing" in str(e):
                logger.warning(f"JSON parsing error, retrying with shorter content: {e}")
                # Retry with even shorter content
                if max_length > 500:
                    return await self._add_episode_safe(
                        name=name,
                        episode_body=episode_body[:500],
                        source_description=source_description,
                        reference_time=reference_time,
                        max_length=500,
                        timeout_seconds=timeout_seconds
                    )
            logger.error(f"Failed to add episode {name}: {e}")
            return None
    
    async def add_conversation(
        self,
        user_message: str,
        agent_response: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record a conversation turn in memory"""
        
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        episode_body = f"""User: {user_message}
Assistant: {agent_response}{context_str}
Type: conversation
Timestamp: {datetime.now().isoformat()}"""
        
        result = await self.graphiti.add_episode(
            name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            episode_body=episode_body.strip(),
            source_description="User conversation with music agent",
            reference_time=datetime.now(),
            group_id=self.session_id
        )
        return result
    
    async def add_track_discovery(
        self,
        track: Dict[str, Any],
        source: str,
        action: Optional[str] = None
    ):
        """Record track discovery or interaction"""
        
        # Clean the track title for the name (remove special chars, limit length)
        import re
        title = track.get('title', 'unknown')
        clean_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)[:30]
        
        episode_body = f"""Discovered track: {track.get('title', 'Unknown')} by {track.get('artist', 'Unknown')}
Album: {track.get('album', 'N/A')}
Source: {source}
BPM: {track.get('bpm', 'N/A')}, Key: {track.get('key', 'N/A')}
Track ID: {track.get('id', 'N/A')}
Type: track_discovery
Timestamp: {datetime.now().isoformat()}"""
        
        if action:
            episode_body += f"\nAction: {action}"
        
        # Use safe add method
        result = await self._add_episode_safe(
            name=f"track_{clean_title}_{datetime.now().strftime('%H%M%S')}",
            episode_body=episode_body.strip(),
            source_description=f"Track discovered from {source}",
            reference_time=datetime.now(),
            timeout_seconds=10  # Shorter timeout for track additions
        )
        
        return result
    
    async def add_preference(
        self,
        entity_type: str,
        entity_name: str,
        preference_type: str,
        score: float,
        reason: Optional[str] = None
    ):
        """Record user preference"""
        
        episode_body = f"""User preference recorded:
Type: {preference_type} {entity_type}
Entity: {entity_name}
Score: {score}
Preference Type: preference
Entity Type: {entity_type}
Timestamp: {datetime.now().isoformat()}"""
        
        if reason:
            episode_body += f"\nReason: {reason}"
        
        result = await self.graphiti.add_episode(
            name=f"preference_{entity_type}_{preference_type}_{datetime.now().strftime('%H%M%S')}",
            episode_body=episode_body.strip(),
            source_description="User preference captured by agent",
            reference_time=datetime.now(),
            group_id=self.session_id
        )
        return result
    
    async def search_memory(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search memory for relevant information"""
        
        try:
            results = await self.graphiti.search(
                query=query,
                num_results=limit,
                group_ids=[self.session_id] if self.session_id else None
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": getattr(result, 'content', str(result)),
                "score": getattr(result, 'score', 0.0),
                "timestamp": getattr(result, 'created_at', None)
            })
        
        return formatted_results
    
    async def get_track_relationships(
        self,
        track_id: str,
        relationship_types: Optional[List[str]] = None
    ) -> Dict[str, List]:
        """Get relationships for a specific track"""
        
        if not relationship_types:
            relationship_types = ["SIMILAR_TO", "MIXED_WITH", "REMIX_OF", "PERFORMED_BY"]
        
        query = """
        MATCH (t:Track {id: $track_id})
        OPTIONAL MATCH (t)-[r]-(related)
        WHERE type(r) IN $rel_types
        RETURN type(r) as relationship, collect(related) as nodes
        """
        
        results = await self.graphiti.driver.execute_query(
            query,
            track_id=track_id,
            rel_types=relationship_types
        )
        
        relationships = {}
        for record in results:
            rel_type = record["relationship"]
            if rel_type:
                relationships[rel_type] = record["nodes"]
        
        return relationships
    
    async def get_user_preferences(
        self,
        user_id: Optional[str] = None,
        preference_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve user preferences from memory"""
        
        # Use Graphiti search to find preference episodes
        search_query = "preference"
        if preference_type:
            search_query = f"{preference_type} preference"
        
        try:
            # Search for preference episodes
            results = await self.graphiti.search(
                query=search_query,
                num_results=100,
                group_ids=[self.session_id] if self.session_id else None
            )
            
            preferences = []
            for result in results:
                # Parse preference data from the content
                content = getattr(result, 'content', str(result))
                if 'preference' in content.lower():
                    # Extract basic info from content
                    preferences.append({
                        "content": content,
                        "score": getattr(result, 'score', 0.0),
                        "timestamp": getattr(result, 'created_at', None)
                    })
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return []
    
    async def analyze_listening_patterns(
        self,
        time_range: str = "week"
    ) -> Dict[str, Any]:
        """Analyze listening patterns over time"""
        
        # Calculate time range
        if time_range == "week":
            days = 7
        elif time_range == "month":
            days = 30
        else:
            days = 365
        
        query = """
        MATCH (e:Episode)
        WHERE e.metadata.type = 'track_discovery'
        AND e.created_at > datetime() - duration({days: $days})
        RETURN 
            count(e) as total_discoveries,
            collect(DISTINCT e.metadata.source) as sources,
            avg(toFloat(e.metadata.bpm)) as avg_bpm
        """
        
        results = await self.graphiti.driver.execute_query(
            query,
            days=days
        )
        
        if results:
            result = results[0]
            return {
                "time_range": time_range,
                "total_discoveries": result["total_discoveries"],
                "sources_used": result["sources"],
                "average_bpm": result["avg_bpm"],
                "analysis_date": datetime.now().isoformat()
            }
        
        return {}
    
    async def get_recent_context(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        
        # Use search to get recent episodes
        try:
            episodes = await self.graphiti.search(
                query="*",
                num_results=limit,
                group_ids=[self.session_id] if self.session_id else None
            )
        except Exception as e:
            logger.error(f"Failed to get recent context: {e}")
            episodes = []
        
        context = []
        for episode in episodes:
            context.append({
                "content": getattr(episode, 'content', str(episode)),
                "type": getattr(episode, 'type', 'unknown'),
                "timestamp": getattr(episode, 'created_at', None),
                "source": getattr(episode, 'source', 'unknown')
            })
        
        return context
    
    async def close(self):
        """Close Graphiti connection"""
        
        if self.graphiti:
            # Graphiti doesn't have explicit close, but we can clean up
            self.graphiti = None
            self.initialized = False
            logger.info("Graphiti memory system closed")