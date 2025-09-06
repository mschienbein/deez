"""
1001 Tracklists advanced tools.

Provides comprehensive tracklist analysis and DJ discovery functionality.
"""

import asyncio
from typing import Optional, List, Dict, Any
from strands import tool

from ....integrations.tracklists_1001 import (
    OneThousandOneTracklistsIntegration,
    DJSetInfo,
    DJSetTrack
)


# Initialize integration
tracklists = OneThousandOneTracklistsIntegration()


@tool
def get_1001_tracklist(url: str, enhance: bool = True) -> Dict[str, Any]:
    """
    Fetch a DJ set tracklist from 1001 Tracklists with advanced analysis.
    
    Args:
        url: 1001 Tracklists URL for the set
        enhance: Whether to enhance tracks with BPM/key/genre data
    
    Returns:
        Complete tracklist with track details, mixing info, and metadata
    
    Example:
        >>> tracklist = get_1001_tracklist("https://www.1001tracklists.com/tracklist/...")
        >>> print(f"DJ: {tracklist['dj_name']}")
        >>> print(f"Tracks: {tracklist['track_count']}")
    """
    async def _fetch():
        dj_set = await tracklists.get_tracklist(url, enhance=enhance)
        return dj_set.to_dict()
    
    return asyncio.run(_fetch())


@tool
def analyze_dj_style(dj_name: str, num_sets: int = 10) -> Dict[str, Any]:
    """
    Analyze a DJ's mixing style and track selection patterns.
    
    Args:
        dj_name: Name of the DJ to analyze
        num_sets: Number of recent sets to analyze
    
    Returns:
        Analysis of DJ's style including:
        - Genre preferences
        - BPM ranges and patterns
        - Key preferences and harmonic mixing
        - Track selection diversity
        - Mixing techniques
    
    Example:
        >>> analysis = analyze_dj_style("Carl Cox", num_sets=15)
        >>> print(f"Primary genre: {analysis['top_genre']}")
        >>> print(f"Average BPM: {analysis['avg_bpm']}")
    """
    async def _analyze():
        analysis = await tracklists.analyze_dj_style(dj_name, num_sets)
        return analysis.to_dict()
    
    return asyncio.run(_analyze())


@tool
def discover_festival_tracks(
    festival_name: str, 
    year: Optional[int] = None,
    stage_filter: Optional[str] = None,
    min_plays: int = 3
) -> List[Dict[str, Any]]:
    """
    Discover trending tracks from festival sets.
    
    Args:
        festival_name: Name of the festival
        year: Year to analyze (defaults to current year)
        stage_filter: Optional stage name filter
        min_plays: Minimum plays across sets to be considered trending
    
    Returns:
        List of trending tracks with play counts and DJ info
    
    Example:
        >>> tracks = discover_festival_tracks("Tomorrowland", year=2023, min_plays=5)
        >>> for track in tracks:
        >>>     print(f"{track['artist']} - {track['title']} ({track['play_count']} plays)")
    """
    async def _discover():
        trends = await tracklists.discover_festival_tracks(
            festival_name, 
            year=year,
            stage_filter=stage_filter,
            min_plays=min_plays
        )
        return [track.to_dict() for track in trends]
    
    return asyncio.run(_discover())