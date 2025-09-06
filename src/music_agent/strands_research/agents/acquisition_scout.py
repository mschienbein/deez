"""
Acquisition Scout Agent - Finds track sources using Strands.

Locates where to purchase, stream, or download identified tracks.
"""

from typing import Dict, Any, List, Optional
from strands import Agent

from ..tools.acquisition_tools import (
    find_purchase_options,
    find_streaming_options,
    check_availability,
    get_best_source
)


class AcquisitionScoutAgent(Agent):
    """
    Strands agent specialized in finding acquisition sources.
    
    Searches for the best places to purchase, stream, or download tracks
    based on quality, price, and availability.
    """
    
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",  # Fast model for scouting
        **kwargs
    ):
        """
        Initialize the acquisition scout agent.
        
        Args:
            model: LLM model to use
            **kwargs: Additional Agent configuration
        """
        instructions = """
        You are an acquisition scout specializing in finding music sources.
        
        Your responsibilities:
        1. Find all available purchase options (prioritize lossless formats)
        2. Identify streaming services with the track
        3. Check regional availability
        4. Compare prices and quality across sources
        5. Recommend the best acquisition option
        
        Priority order:
        1. Lossless purchase (WAV, FLAC, AIFF)
        2. High-quality purchase (320kbps MP3)
        3. Lossless streaming (Tidal, Deezer HiFi)
        4. Standard streaming (Spotify, Apple Music)
        5. Free streaming (YouTube, SoundCloud)
        
        Consider:
        - DJ/professional use requires high quality files
        - Regional restrictions may apply
        - Some sources require subscriptions
        - Bandcamp supports artists directly
        """
        
        super().__init__(
            name="AcquisitionScout",
            model=model,
            tools=[
                find_purchase_options,
                find_streaming_options,
                check_availability,
                get_best_source
            ],
            instructions=instructions,
            **kwargs
        )
    
    async def scout(
        self,
        metadata: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Scout for acquisition options.
        
        Args:
            metadata: Track metadata with platform IDs
            preferences: User preferences (quality, price, type)
        
        Returns:
            Acquisition options and recommendations
        """
        prompt = f"""
        Find acquisition options for this track:
        
        Metadata:
        {metadata}
        
        User Preferences:
        {preferences or 'Default: prefer lossless purchase, max $5'}
        
        Steps:
        1. Use find_purchase_options to get purchase sources
        2. Use find_streaming_options to get streaming services
        3. Use get_best_source to determine the best option
        
        Return:
        - purchase_options: list of purchase sources
        - streaming_options: list of streaming services
        - best_option: recommended source with reason
        - total_options: count of all options found
        """
        
        response = await self.run(prompt)
        return response
    
    async def check_platform_availability(
        self,
        metadata: Dict[str, Any],
        platforms: List[str]
    ) -> Dict[str, Any]:
        """
        Check availability on specific platforms.
        
        Args:
            metadata: Track metadata
            platforms: List of platforms to check
        
        Returns:
            Availability status for each platform
        """
        prompt = f"""
        Check if this track is available on these platforms:
        
        Track: {metadata.get('artist')} - {metadata.get('title')}
        Platforms to check: {platforms}
        
        Use check_availability to verify each platform.
        
        Return availability status with confidence scores.
        """
        
        response = await self.run(prompt)
        return response
    
    async def find_dj_sources(
        self,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Find sources specifically suitable for DJs.
        
        Args:
            metadata: Track metadata
        
        Returns:
            DJ-friendly acquisition options
        """
        prompt = f"""
        Find DJ-friendly sources for this track:
        
        {metadata}
        
        DJ Requirements:
        - Lossless or 320kbps minimum
        - No DRM restrictions
        - Full-length versions (not radio edits)
        - Reliable/professional sources
        
        Focus on:
        1. Beatport (best for electronic)
        2. Bandcamp (supports artists)
        3. Juno Download
        4. Traxsource
        
        Use find_purchase_options with preferred_format="lossless"
        
        Return only sources meeting DJ requirements.
        """
        
        response = await self.run(prompt)
        return response