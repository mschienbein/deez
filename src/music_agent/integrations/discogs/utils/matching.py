"""
Matching and scoring utilities for Discogs data.
"""

from typing import Optional, List, Dict, Any


def calculate_match_score(
    query: str,
    artist: str,
    title: str,
    remixer: Optional[str] = None
) -> float:
    """
    Calculate match score between query and result.
    
    Args:
        query: Search query
        artist: Result artist name
        title: Result title
        remixer: Optional remixer name
        
    Returns:
        Match score between 0 and 1
    """
    query_lower = query.lower()
    artist_lower = artist.lower()
    title_lower = title.lower()
    
    score = 0.0
    
    # Check artist match
    if artist_lower in query_lower or query_lower in artist_lower:
        score += 0.4
    
    # Check title match
    if title_lower in query_lower or query_lower in title_lower:
        score += 0.4
    
    # Check remixer match if present
    if remixer:
        remixer_lower = remixer.lower()
        if remixer_lower in query_lower:
            score += 0.2
    
    # Bonus for exact matches
    if query_lower == f"{artist_lower} {title_lower}":
        score = 1.0
    elif query_lower == title_lower:
        score = max(score, 0.8)
    
    return min(score, 1.0)


def merge_track_artists(
    track_artists: List[Dict[str, Any]],
    extra_artists: List[Dict[str, Any]]
) -> str:
    """
    Merge track artists and extra artists into a single string.
    
    Args:
        track_artists: Main track artists
        extra_artists: Extra artists (remixers, featuring, etc.)
        
    Returns:
        Formatted artist string
    """
    artists = []
    
    # Add main artists
    for artist in track_artists:
        name = artist.get('name', '')
        if name:
            artists.append(name)
    
    # Add featuring artists
    for artist in extra_artists:
        role = artist.get('role', '').lower()
        name = artist.get('name', '')
        
        if name and any(r in role for r in ['featuring', 'feat', 'ft']):
            artists.append(f"feat. {name}")
        elif name and 'remix' in role:
            artists.append(f"({name} Remix)")
    
    return " ".join(artists) if artists else "Unknown Artist"