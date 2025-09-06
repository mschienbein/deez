"""
Core multi-platform search tools.

Orchestrates search operations across multiple music platforms.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher
from strands import tool

from ...database.schema import (
    SearchHistory,
    init_database,
)
from ...integrations.deezer import DeezerIntegration
from ...integrations.spotify import SpotifyIntegration
from ...integrations.youtube import YouTubeIntegration
from ...utils.config import config

logger = logging.getLogger(__name__)

# Initialize database connection
db_engine, db_session_maker = init_database(config.database.url)


@tool
def search_music(query: str, platform: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for music across platforms with intelligent fallback.
    
    Args:
        query: Search query (artist, track name, etc.)
        platform: Platform to search ("all", "deezer", "spotify", "youtube")
        limit: Maximum number of results to return
    
    Returns:
        List of standardized track results from specified platform(s)
    
    Example:
        >>> results = search_music("Daft Punk Get Lucky", platform="all", limit=5)
        >>> for track in results:
        >>>     print(f"{track['artist']} - {track['title']} ({track['platform']})")
    """
    results = []
    
    try:
        session = db_session_maker()
        
        # Log search
        search_entry = SearchHistory(
            query=query,
            platform=platform,
            timestamp=datetime.utcnow()
        )
        session.add(search_entry)
        
        if platform in ["all", "deezer"]:
            try:
                deezer = DeezerIntegration()
                deezer_results = deezer.search(query, limit)
                results.extend(deezer_results)
                logger.info(f"Found {len(deezer_results)} results from Deezer")
            except Exception as e:
                logger.error(f"Deezer search failed: {e}")
        
        if platform in ["all", "spotify"]:
            try:
                spotify = SpotifyIntegration()
                spotify_results = spotify.search(query, limit)
                results.extend(spotify_results)
                logger.info(f"Found {len(spotify_results)} results from Spotify")
            except Exception as e:
                logger.error(f"Spotify search failed: {e}")
        
        if platform in ["all", "youtube"]:
            try:
                youtube = YouTubeIntegration()
                youtube_results = youtube.search(query, limit)
                results.extend(youtube_results)
                logger.info(f"Found {len(youtube_results)} results from YouTube")
            except Exception as e:
                logger.error(f"YouTube search failed: {e}")
        
        # Update search result count
        search_entry.result_count = len(results)
        session.commit()
        session.close()
        
        # Remove duplicates and sort by relevance
        results = _deduplicate_tracks(results)
        
        return results[:limit]
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []


@tool
def match_track_across_platforms(title: str, artist: str) -> Dict[str, Any]:
    """
    Find the same track across different platforms using intelligent matching.
    
    Args:
        title: Track title
        artist: Artist name
    
    Returns:
        Dictionary with matches found across platforms
    
    Example:
        >>> matches = match_track_across_platforms("Get Lucky", "Daft Punk")
        >>> for platform, match in matches["matches"].items():
        >>>     print(f"{platform}: {match['url']} (confidence: {match['confidence']:.2f})")
    """
    results = {
        "title": title,
        "artist": artist,
        "matches": {}
    }
    
    query = f"{artist} {title}"
    
    # Search each platform
    platforms = ["deezer", "spotify", "youtube"]
    
    for platform in platforms:
        try:
            search_results = search_music(query, platform, limit=3)
            
            # Find best match using fuzzy matching
            best_match = None
            best_score = 0
            
            for result in search_results:
                score = _calculate_match_score(title, artist, result)
                if score > best_score:
                    best_score = score
                    best_match = result
            
            if best_match and best_score > 0.7:  # Minimum confidence threshold
                results["matches"][platform] = {
                    "id": best_match["id"],
                    "url": best_match["platform_url"],
                    "confidence": best_score,
                    "title": best_match["title"],
                    "artist": best_match["artist"]
                }
                
        except Exception as e:
            logger.error(f"Failed to search {platform}: {e}")
    
    return results


def _deduplicate_tracks(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate tracks based on title and artist similarity."""
    unique_tracks = []
    seen = set()
    
    for track in tracks:
        # Create a normalized key for comparison
        key = f"{track.get('artist', '').lower().strip()} - {track.get('title', '').lower().strip()}"
        
        if key not in seen:
            seen.add(key)
            unique_tracks.append(track)
    
    return unique_tracks


def _calculate_match_score(target_title: str, target_artist: str, candidate: Dict[str, Any]) -> float:
    """Calculate similarity score between target and candidate track."""
    # Normalize strings
    target_title = target_title.lower().strip()
    target_artist = target_artist.lower().strip()
    candidate_title = candidate.get("title", "").lower().strip()
    candidate_artist = candidate.get("artist", "").lower().strip()
    
    # Calculate title similarity
    title_similarity = SequenceMatcher(None, target_title, candidate_title).ratio()
    
    # Calculate artist similarity
    artist_similarity = SequenceMatcher(None, target_artist, candidate_artist).ratio()
    
    # Weight title higher than artist
    score = (title_similarity * 0.7) + (artist_similarity * 0.3)
    
    return score