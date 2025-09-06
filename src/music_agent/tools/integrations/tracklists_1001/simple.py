"""
1001 Tracklists simple tools.

Provides basic tracklist functionality using the simple integration.
"""

from typing import Dict, Any, List, Optional
from strands import tool

from ....integrations.tracklists_simple import OneThousandOneTracklists


# Initialize integration
tracklists = OneThousandOneTracklists()


@tool
def get_tracklist(url: str) -> Dict[str, Any]:
    """
    Fetch a DJ set tracklist from 1001 Tracklists.
    
    Args:
        url: 1001 Tracklists URL
    
    Returns:
        Raw tracklist data including:
        - DJ name
        - Event/venue
        - Date
        - Track list with timestamps
        - Recording links
        - View statistics
    
    Example:
        >>> data = get_tracklist("https://www.1001tracklists.com/tracklist/...")
        >>> print(f"DJ: {data['dj']}")
        >>> print(f"Tracks: {len(data['tracks'])}")
    """
    return tracklists.get_tracklist(url)


@tool
def search_tracklists(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for tracks on 1001 Tracklists.
    
    Args:
        query: Search query (track name, DJ, etc.)
        limit: Maximum results
    
    Returns:
        List of search results
    
    Example:
        >>> results = search_tracklists("Bicep Glue")
        >>> for result in results:
        >>>     print(result['title'])
    """
    return tracklists.search(query, limit)


@tool
def get_dj_recent_sets(dj_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent sets by a specific DJ.
    
    Args:
        dj_name: Name of the DJ
        limit: Maximum number of sets
    
    Returns:
        List of recent sets with metadata
    
    Example:
        >>> sets = get_dj_recent_sets("Carl Cox")
        >>> for set_info in sets:
        >>>     print(f"{set_info['event']} - {set_info['date']}")
    """
    return tracklists.get_dj_sets(dj_name, limit)


@tool
def extract_track_list(tracklist_data: Dict[str, Any]) -> List[str]:
    """
    Extract clean track list from tracklist data.
    
    Args:
        tracklist_data: Raw tracklist data from get_tracklist()
    
    Returns:
        List of track names in "Artist - Title" format
    
    Example:
        >>> data = get_tracklist(url)
        >>> tracks = extract_track_list(data)
        >>> for track in tracks:
        >>>     print(track)
    """
    tracks = []
    
    for track in tracklist_data.get('tracks', []):
        if track.get('is_id'):
            tracks.append("ID - ID")
        else:
            artist = track.get('artist', 'Unknown')
            title = track.get('title', 'Unknown')
            remix = track.get('remix')
            
            if remix:
                track_str = f"{artist} - {title} ({remix})"
            else:
                track_str = f"{artist} - {title}"
            
            tracks.append(track_str)
    
    return tracks


@tool
def find_common_tracks(tracklist_urls: List[str]) -> Dict[str, int]:
    """
    Find tracks that appear in multiple tracklists.
    
    Args:
        tracklist_urls: List of 1001 Tracklists URLs
    
    Returns:
        Dictionary of tracks and their occurrence count
    
    Example:
        >>> urls = ["url1", "url2", "url3"]
        >>> common = find_common_tracks(urls)
        >>> for track, count in common.items():
        >>>     if count > 1:
        >>>         print(f"{track}: played {count} times")
    """
    track_counts = {}
    
    for url in tracklist_urls:
        data = tracklists.get_tracklist(url)
        tracks = extract_track_list(data)
        
        for track in tracks:
            if track != "ID - ID":  # Skip unknown tracks
                track_counts[track] = track_counts.get(track, 0) + 1
    
    # Sort by frequency
    return dict(sorted(track_counts.items(), key=lambda x: x[1], reverse=True))


@tool
def export_as_playlist(tracklist_data: Dict[str, Any]) -> str:
    """
    Export tracklist as a simple text playlist.
    
    Args:
        tracklist_data: Raw tracklist data
    
    Returns:
        Formatted playlist string
    
    Example:
        >>> data = get_tracklist(url)
        >>> playlist = export_as_playlist(data)
        >>> print(playlist)
    """
    lines = []
    
    # Header
    lines.append(f"# {tracklist_data.get('title', 'Tracklist')}")
    lines.append(f"# DJ: {tracklist_data.get('dj', 'Unknown')}")
    
    if tracklist_data.get('event'):
        lines.append(f"# Event: {tracklist_data['event']}")
    
    if tracklist_data.get('date'):
        lines.append(f"# Date: {tracklist_data['date']}")
    
    lines.append("")
    
    # Tracks
    for track in tracklist_data.get('tracks', []):
        position = track.get('position', '')
        cue = track.get('cue', '')
        
        if track.get('is_id'):
            track_str = "ID - ID"
        else:
            artist = track.get('artist', 'Unknown')
            title = track.get('title', 'Unknown')
            remix = track.get('remix')
            
            if remix:
                track_str = f"{artist} - {title} ({remix})"
            else:
                track_str = f"{artist} - {title}"
        
        if cue:
            lines.append(f"{position:3}. [{cue}] {track_str}")
        else:
            lines.append(f"{position:3}. {track_str}")
    
    return "\n".join(lines)