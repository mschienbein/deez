"""
Data Collector Agent - Platform search specialists using Strands.

Each instance specializes in searching a specific music platform.
"""

from typing import Dict, Any, Optional
from strands import Agent

from ..tools.search_tools import (
    search_spotify,
    search_beatport,
    search_discogs,
    search_deezer,
    search_musicbrainz,
    search_soundcloud
)


class DataCollectorAgent(Agent):
    """
    Strands agent specialized in collecting data from music platforms.
    
    Each instance is configured for a specific platform with appropriate
    tools and search strategies.
    """
    
    # Platform-specific tool mappings
    PLATFORM_TOOLS = {
        "spotify": [search_spotify],
        "beatport": [search_beatport],
        "discogs": [search_discogs],
        "deezer": [search_deezer],
        "musicbrainz": [search_musicbrainz],
        "soundcloud": [search_soundcloud]
    }
    
    # Platform-specific search strategies
    PLATFORM_INSTRUCTIONS = {
        "spotify": """
        You are a Spotify search specialist. Your job is to:
        1. Search for tracks using the provided query
        2. Retrieve comprehensive metadata including audio features
        3. Focus on getting ISRC codes and popularity metrics
        4. Return structured results with high confidence
        
        Spotify excels at mainstream music and provides detailed audio analysis.
        """,
        
        "beatport": """
        You are a Beatport search specialist focused on electronic music. Your job is to:
        1. Search for electronic/dance music tracks
        2. Retrieve DJ-relevant metadata (BPM, key, genre)
        3. Get pricing and format information
        4. Focus on remix and mix name accuracy
        
        Beatport is the authority for electronic music metadata.
        """,
        
        "discogs": """
        You are a Discogs search specialist. Your job is to:
        1. Search for detailed release information
        2. Find catalog numbers and pressing details
        3. Get label and discography data
        4. Check marketplace availability
        
        Discogs provides comprehensive discography and physical release data.
        """,
        
        "deezer": """
        You are a Deezer search specialist. Your job is to:
        1. Search for tracks across diverse catalogs
        2. Get ISRC codes and basic metadata
        3. Find preview URLs and streaming links
        4. Verify track availability in different regions
        
        Deezer has a large catalog with good international coverage.
        """,
        
        "musicbrainz": """
        You are a MusicBrainz search specialist. Your job is to:
        1. Search for authoritative music metadata
        2. Find recording and release identifiers
        3. Get detailed credits and relationships
        4. Retrieve ISRC codes and catalog data
        
        MusicBrainz is an open encyclopedia with detailed, crowd-sourced metadata.
        """,
        
        "soundcloud": """
        You are a SoundCloud search specialist. Your job is to:
        1. Search for tracks including remixes and bootlegs
        2. Find user-generated content and underground tracks
        3. Get play counts and engagement metrics
        4. Identify unofficial releases and DJ edits
        
        SoundCloud often has exclusive remixes and unreleased tracks.
        """
    }
    
    def __init__(
        self,
        platform: str,
        model: str = "claude-3-haiku-20240307",  # Use fast model for data collection
        **kwargs
    ):
        """
        Initialize a platform-specific data collector.
        
        Args:
            platform: Music platform to specialize in
            model: LLM model to use (default: Claude 3 Haiku for speed)
            **kwargs: Additional Agent configuration
        """
        if platform not in self.PLATFORM_TOOLS:
            raise ValueError(f"Unsupported platform: {platform}. Choose from {list(self.PLATFORM_TOOLS.keys())}")
        
        self.platform = platform
        
        # Get platform-specific configuration
        tools = self.PLATFORM_TOOLS[platform]
        instructions = self.PLATFORM_INSTRUCTIONS.get(
            platform,
            f"You are a {platform} search specialist. Search for tracks and return structured metadata."
        )
        
        # Initialize Strands Agent
        super().__init__(
            name=f"DataCollector_{platform}",
            model=model,
            tools=tools,
            instructions=instructions,
            **kwargs
        )
    
    async def search(self, query: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Search for a track on this platform.
        
        Args:
            query: Search query (usually "Artist - Title")
            use_cache: Whether to use cached results
        
        Returns:
            Platform search results
        """
        prompt = f"""
        Search for this track: {query}
        
        Use the search tool for {self.platform} to find the best match.
        Return comprehensive metadata including all available fields.
        If multiple results are found, return the most relevant one.
        
        Use cache: {use_cache}
        """
        
        response = await self.run(prompt)
        return response
    
    async def search_with_context(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search with additional context for better matching.
        
        Args:
            query: Search query
            context: Additional context (genre hints, year, etc.)
        
        Returns:
            Platform search results
        """
        context_str = ""
        if context:
            if context.get("genre"):
                context_str += f"\nGenre hint: {context['genre']}"
            if context.get("year"):
                context_str += f"\nRelease year: {context['year']}"
            if context.get("label"):
                context_str += f"\nLabel: {context['label']}"
        
        prompt = f"""
        Search for this track: {query}
        {context_str}
        
        Use this additional context to refine your search on {self.platform}.
        Prioritize results that match the context information.
        """
        
        response = await self.run(prompt)
        return response