"""
Core multi-platform recommendations and analytics tools.

Provides music trend analysis and listening pattern insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from strands import tool

from ...database.schema import (
    ListeningHistory,
    SearchHistory,
    Track,
    init_database,
)
from ...utils.config import config

logger = logging.getLogger(__name__)

# Initialize database connection
db_engine, db_session_maker = init_database(config.database.url)


@tool
def analyze_music_trends(timeframe: str = "month") -> Dict[str, Any]:
    """
    Analyze listening patterns and trends across all platforms.
    
    Args:
        timeframe: Time period to analyze ("week", "month", "year")
    
    Returns:
        Comprehensive analysis including:
        - Platform usage statistics
        - Popular search queries
        - Top tracks and artists
        - Listening patterns
    
    Example:
        >>> analysis = analyze_music_trends("month")
        >>> print(f"Total searches: {analysis['total_searches']}")
        >>> print(f"Top platform: {max(analysis['platform_usage'], key=analysis['platform_usage'].get)}")
    """
    try:
        session = db_session_maker()
        
        # Calculate date range
        now = datetime.utcnow()
        if timeframe == "week":
            start_date = now - timedelta(weeks=1)
        elif timeframe == "month":
            start_date = now - timedelta(days=30)
        elif timeframe == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        # Get listening history
        listening_data = session.query(ListeningHistory).filter(
            ListeningHistory.played_at >= start_date
        ).all()
        
        # Get search history
        search_data = session.query(SearchHistory).filter(
            SearchHistory.timestamp >= start_date
        ).all()
        
        # Analyze trends
        analysis = {
            "timeframe": timeframe,
            "period": f"{start_date.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
            "total_searches": len(search_data),
            "total_plays": sum(entry.play_count for entry in listening_data),
            "unique_tracks": len(set(entry.track_id for entry in listening_data)),
            "platform_usage": {},
            "popular_searches": [],
            "top_tracks": []
        }
        
        # Platform usage analysis
        platform_counts = {}
        for entry in listening_data:
            platform = entry.platform
            platform_counts[platform] = platform_counts.get(platform, 0) + entry.play_count
        
        analysis["platform_usage"] = platform_counts
        
        # Popular search queries
        search_queries = {}
        for entry in search_data:
            query = entry.query.lower()
            search_queries[query] = search_queries.get(query, 0) + 1
        
        analysis["popular_searches"] = sorted(
            search_queries.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Top tracks
        track_plays = {}
        for entry in listening_data:
            track_plays[entry.track_id] = track_plays.get(entry.track_id, 0) + entry.play_count
        
        top_track_ids = sorted(track_plays.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for track_id, play_count in top_track_ids:
            track = session.query(Track).get(track_id)
            if track:
                analysis["top_tracks"].append({
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album,
                    "play_count": play_count
                })
        
        session.close()
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze trends: {e}")
        return {"error": str(e)}