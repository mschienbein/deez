"""
Agent tools for 1001 Tracklists integration.

Provides tools for:
- Fetching DJ set tracklists
- Analyzing DJ mixing styles
- Discovering tracks across sets
- Festival trend analysis
"""

from typing import Optional, List, Dict, Any
import asyncio

from ..integrations.tracklists_1001 import (
    OneThousandOneTracklistsIntegration,
    DJSetInfo,
    DJSetTrack
)

# Initialize integration
tracklists = OneThousandOneTracklistsIntegration()


def get_dj_tracklist(url: str, enhance: bool = True) -> Dict[str, Any]:
    """
    Fetch a DJ set tracklist from 1001 Tracklists.
    
    Args:
        url: 1001 Tracklists URL for the set
        enhance: Whether to enhance tracks with BPM/key/genre data
    
    Returns:
        Complete tracklist with track details, mixing info, and metadata
    
    Example:
        >>> tracklist = get_dj_tracklist("https://www.1001tracklists.com/tracklist/...")
        >>> print(f"DJ: {tracklist['dj_name']}")
        >>> print(f"Tracks: {tracklist['track_count']}")
    """
    async def _fetch():
        dj_set = await tracklists.get_tracklist(url, enhance=enhance)
        return dj_set.to_dict()
    
    return asyncio.run(_fetch())


def analyze_dj_style(dj_name: str, num_sets: int = 10) -> Dict[str, Any]:
    """
    Analyze a DJ's mixing style and track selection patterns.
    
    Args:
        dj_name: Name of the DJ to analyze
        num_sets: Number of recent sets to analyze (default 10)
    
    Returns:
        Analysis including:
        - Average BPM and BPM range
        - Preferred musical keys
        - Genre distribution
        - Signature/frequently played tracks
        - Mixing style characteristics
    
    Example:
        >>> analysis = analyze_dj_style("Carl Cox")
        >>> print(f"Avg BPM: {analysis['avg_bpm']}")
        >>> print(f"Top genres: {analysis['genre_distribution']}")
    """
    async def _analyze():
        return await tracklists.analyze_dj_style(dj_name, num_sets)
    
    return asyncio.run(_analyze())


def find_track_in_sets(
    artist: str,
    title: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Find all DJ sets that include a specific track.
    
    Args:
        artist: Track artist name
        title: Track title
        limit: Maximum number of results
    
    Returns:
        List of DJ sets containing the track with:
        - DJ name
        - Event/festival name
        - Date played
        - Position in set
        - Mixing context
    
    Example:
        >>> appearances = find_track_in_sets("Bicep", "Glue")
        >>> for appearance in appearances:
        >>>     print(f"{appearance['dj_name']} played it at {appearance['event']}")
    """
    async def _find():
        return await tracklists.find_track_appearances(artist, title, limit)
    
    return asyncio.run(_find())


def get_festival_sets(festival_url: str) -> List[Dict[str, Any]]:
    """
    Get all DJ sets from a festival.
    
    Args:
        festival_url: 1001 Tracklists festival page URL
    
    Returns:
        List of all DJ sets from the festival
    
    Example:
        >>> sets = get_festival_sets("https://www.1001tracklists.com/source/...")
        >>> print(f"Total sets: {len(sets)}")
    """
    async def _fetch():
        sets = await tracklists.get_festival_lineup(festival_url)
        return [s.to_dict() for s in sets]
    
    return asyncio.run(_fetch())


def analyze_festival_trends(
    festival_url: str,
    analyze_type: str = "all"
) -> Dict[str, Any]:
    """
    Analyze music trends from a festival.
    
    Args:
        festival_url: 1001 Tracklists festival page URL
        analyze_type: Type of analysis ("tracks", "genres", "bpm", "all")
    
    Returns:
        Festival analysis including:
        - Most played tracks across all sets
        - Genre distribution
        - BPM progression patterns
        - Peak time tracks
        - Exclusive/rare tracks
    
    Example:
        >>> trends = analyze_festival_trends("https://www.1001tracklists.com/source/...")
        >>> print(f"Top track: {trends['most_played_tracks'][0]}")
    """
    async def _analyze():
        sets = await tracklists.get_festival_lineup(festival_url)
        
        if not sets:
            return {
                'error': 'No sets found for festival',
                'festival_url': festival_url
            }
        
        analysis = {
            'festival_url': festival_url,
            'total_sets': len(sets),
            'total_tracks': sum(s.track_count for s in sets)
        }
        
        if analyze_type in ["tracks", "all"]:
            # Track frequency analysis
            track_counts = {}
            for dj_set in sets:
                for track in dj_set.tracks:
                    key = track.full_title
                    if key not in track_counts:
                        track_counts[key] = {
                            'count': 0,
                            'djs': [],
                            'track': track.to_dict()
                        }
                    track_counts[key]['count'] += 1
                    track_counts[key]['djs'].append(dj_set.dj_name)
            
            # Sort by frequency
            most_played = sorted(
                track_counts.values(),
                key=lambda x: x['count'],
                reverse=True
            )[:20]
            
            analysis['most_played_tracks'] = most_played
        
        if analyze_type in ["genres", "all"]:
            # Genre distribution
            genre_counts = {}
            for dj_set in sets:
                for genre in dj_set.genres:
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            analysis['genre_distribution'] = genre_counts
        
        if analyze_type in ["bpm", "all"]:
            # BPM analysis
            bpms = []
            for dj_set in sets:
                if dj_set.avg_bpm:
                    bpms.append(dj_set.avg_bpm)
            
            if bpms:
                analysis['bpm_stats'] = {
                    'min': min(bpms),
                    'max': max(bpms),
                    'avg': sum(bpms) / len(bpms)
                }
        
        return analysis
    
    return asyncio.run(_analyze())


def discover_underground_tracks(
    genre: Optional[str] = None,
    min_plays: int = 2,
    max_plays: int = 10,
    days_back: int = 30
) -> List[Dict[str, Any]]:
    """
    Discover underground/emerging tracks based on play patterns.
    
    Args:
        genre: Filter by genre (optional)
        min_plays: Minimum number of DJ plays
        max_plays: Maximum number of DJ plays (to find non-mainstream)
        days_back: Look at sets from the last N days
    
    Returns:
        List of emerging tracks that are gaining traction but not mainstream yet
    
    Example:
        >>> underground = discover_underground_tracks(genre="Techno", days_back=14)
        >>> for track in underground:
        >>>     print(f"{track['artist']} - {track['title']}: {track['play_count']} plays")
    """
    # This would require broader data access
    # For now, return a placeholder
    return [
        {
            'message': 'Underground track discovery requires broader data access',
            'genre': genre,
            'criteria': {
                'min_plays': min_plays,
                'max_plays': max_plays,
                'days_back': days_back
            }
        }
    ]


def get_dj_signature_tracks(dj_name: str, min_appearances: int = 3) -> List[Dict[str, Any]]:
    """
    Get tracks frequently played by a specific DJ (their signature tracks).
    
    Args:
        dj_name: Name of the DJ
        min_appearances: Minimum times played to be considered signature
    
    Returns:
        List of signature tracks with play count and contexts
    
    Example:
        >>> signatures = get_dj_signature_tracks("Nina Kraviz")
        >>> for track in signatures:
        >>>     print(f"{track['title']}: played {track['play_count']} times")
    """
    async def _get_signatures():
        # This would analyze multiple sets by the DJ
        # For now, return a placeholder
        return [
            {
                'message': f'Signature track analysis for {dj_name} requires multiple set data',
                'dj_name': dj_name,
                'min_appearances': min_appearances
            }
        ]
    
    return asyncio.run(_get_signatures())


def analyze_track_journey(
    artist: str,
    title: str,
    timeframe_days: int = 365
) -> Dict[str, Any]:
    """
    Analyze how a track has been played over time (from underground to mainstream).
    
    Args:
        artist: Track artist
        title: Track title
        timeframe_days: Number of days to analyze
    
    Returns:
        Journey analysis including:
        - First played date and DJ
        - Play frequency over time
        - Peak popularity period
        - Genre contexts
        - Notable DJs who played it
    
    Example:
        >>> journey = analyze_track_journey("KI/KI", "Jennifer")
        >>> print(f"First played by: {journey['first_played_by']}")
        >>> print(f"Peak period: {journey['peak_period']}")
    """
    async def _analyze():
        appearances = await tracklists.find_track_appearances(artist, title, limit=100)
        
        if not appearances:
            return {
                'error': 'Track not found in database',
                'artist': artist,
                'title': title
            }
        
        return {
            'artist': artist,
            'title': title,
            'total_plays': len(appearances),
            'timeframe_days': timeframe_days,
            'appearances': appearances,
            'message': 'Full journey analysis requires historical data access'
        }
    
    return asyncio.run(_analyze())


def compare_dj_styles(dj1: str, dj2: str) -> Dict[str, Any]:
    """
    Compare mixing styles and track selection between two DJs.
    
    Args:
        dj1: First DJ name
        dj2: Second DJ name
    
    Returns:
        Comparison including:
        - BPM preferences
        - Genre overlap
        - Shared tracks
        - Mixing style differences
    
    Example:
        >>> comparison = compare_dj_styles("Dixon", "Âme")
        >>> print(f"Genre overlap: {comparison['genre_overlap_percent']}%")
    """
    async def _compare():
        style1 = await tracklists.analyze_dj_style(dj1, 5)
        style2 = await tracklists.analyze_dj_style(dj2, 5)
        
        return {
            'dj1': {
                'name': dj1,
                'style': style1
            },
            'dj2': {
                'name': dj2,
                'style': style2
            },
            'comparison': {
                'message': 'Full comparison requires access to multiple sets from both DJs'
            }
        }
    
    return asyncio.run(_compare())


def get_tracklist_audio_links(url: str) -> Dict[str, Any]:
    """
    Get audio streaming/download links for a DJ set if available.
    
    Args:
        url: 1001 Tracklists URL
    
    Returns:
        Available audio links (SoundCloud, Mixcloud, YouTube, etc.)
    
    Example:
        >>> links = get_tracklist_audio_links("https://www.1001tracklists.com/...")
        >>> if links['soundcloud_url']:
        >>>     print(f"Listen on SoundCloud: {links['soundcloud_url']}")
    """
    async def _fetch():
        dj_set = await tracklists.get_tracklist(url, enhance=False)
        return {
            'url': url,
            'recording_url': dj_set.recording_url,
            'download_url': dj_set.download_url,
            'dj_name': dj_set.dj_name,
            'event': dj_set.event_name
        }
    
    return asyncio.run(_fetch())


# Export all tools
__all__ = [
    'get_dj_tracklist',
    'analyze_dj_style',
    'find_track_in_sets',
    'get_festival_sets',
    'analyze_festival_trends',
    'discover_underground_tracks',
    'get_dj_signature_tracks',
    'analyze_track_journey',
    'compare_dj_styles',
    'get_tracklist_audio_links'
]