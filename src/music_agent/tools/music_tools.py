"""Custom tools for music operations using Strands framework."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from strands_agents import tool

from ..database.schema import (
    ListeningHistory,
    Playlist,
    SearchHistory,
    Track,
    init_database,
)
from ..integrations.deezer import DeezerIntegration
from ..integrations.spotify import SpotifyIntegration
from ..integrations.youtube import YouTubeIntegration
from ..utils.config import config

logger = logging.getLogger(__name__)

# Initialize database connection
db_engine, db_session_maker = init_database(config.database.url)


@tool
def search_music(query: str, platform: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
    """Search for music across platforms with intelligent fallback."""
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
def get_track_info(track_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """Get detailed track information from specific platform."""
    try:
        if platform == "deezer":
            deezer = DeezerIntegration()
            return deezer.get_track_info(track_id)
        elif platform == "spotify":
            spotify = SpotifyIntegration()
            return spotify.get_track_info(track_id)
        elif platform == "youtube":
            youtube = YouTubeIntegration()
            return youtube.get_video_info(track_id)
        else:
            logger.error(f"Unknown platform: {platform}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get track info: {e}")
        return None


@tool
def create_cross_platform_playlist(name: str, tracks: List[str]) -> Dict[str, Any]:
    """Create playlist with tracks from multiple platforms."""
    try:
        session = db_session_maker()
        
        # Create playlist
        playlist = Playlist(
            name=name,
            description=f"Cross-platform playlist created on {datetime.utcnow().strftime('%Y-%m-%d')}",
            source_platform="custom",
            created_at=datetime.utcnow()
        )
        session.add(playlist)
        session.flush()  # Get playlist ID
        
        added_tracks = []
        
        for track_spec in tracks:
            # Parse track specification: "platform:id" or just search query
            if ":" in track_spec:
                platform, track_id = track_spec.split(":", 1)
                track_info = get_track_info(track_id, platform)
            else:
                # Search for track
                search_results = search_music(track_spec, limit=1)
                track_info = search_results[0] if search_results else None
            
            if track_info:
                # Check if track exists in database
                existing_track = session.query(Track).filter_by(
                    title=track_info["title"],
                    artist=track_info["artist"]
                ).first()
                
                if not existing_track:
                    # Create new track
                    track = Track(
                        title=track_info["title"],
                        artist=track_info["artist"],
                        album=track_info.get("album", ""),
                        duration=track_info.get("duration", 0),
                        deezer_id=track_info["id"] if track_info["platform"] == "deezer" else None,
                        spotify_id=track_info["id"] if track_info["platform"] == "spotify" else None,
                        youtube_url=track_info["platform_url"] if track_info["platform"] == "youtube" else None,
                        isrc=track_info.get("isrc", ""),
                        created_at=datetime.utcnow()
                    )
                    session.add(track)
                    session.flush()
                    added_tracks.append(track)
                else:
                    added_tracks.append(existing_track)
                
                # Add track to playlist
                playlist.tracks.append(added_tracks[-1])
        
        session.commit()
        
        result = {
            "id": playlist.id,
            "name": playlist.name,
            "description": playlist.description,
            "tracks_added": len(added_tracks),
            "tracks": [
                {
                    "title": track.title,
                    "artist": track.artist,
                    "album": track.album
                }
                for track in added_tracks
            ]
        }
        
        session.close()
        return result
        
    except Exception as e:
        logger.error(f"Failed to create playlist: {e}")
        return {"error": str(e)}


@tool
def analyze_music_trends(timeframe: str = "month") -> Dict[str, Any]:
    """Analyze listening patterns and trends."""
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


@tool
def export_playlist(playlist_id: str, format: str = "json") -> str:
    """Export playlist in various formats."""
    try:
        session = db_session_maker()
        
        playlist = session.query(Playlist).get(int(playlist_id))
        if not playlist:
            return json.dumps({"error": "Playlist not found"})
        
        playlist_data = {
            "name": playlist.name,
            "description": playlist.description,
            "created_at": playlist.created_at.isoformat(),
            "tracks": []
        }
        
        for track in playlist.tracks:
            track_data = {
                "title": track.title,
                "artist": track.artist,
                "album": track.album,
                "duration": track.duration,
                "platform_ids": {}
            }
            
            if track.deezer_id:
                track_data["platform_ids"]["deezer"] = track.deezer_id
            if track.spotify_id:
                track_data["platform_ids"]["spotify"] = track.spotify_id
            if track.youtube_url:
                track_data["platform_ids"]["youtube"] = track.youtube_url
            
            playlist_data["tracks"].append(track_data)
        
        session.close()
        
        if format.lower() == "json":
            return json.dumps(playlist_data, indent=2)
        elif format.lower() == "m3u":
            return _export_to_m3u(playlist_data)
        elif format.lower() == "csv":
            return _export_to_csv(playlist_data)
        else:
            return json.dumps({"error": f"Unsupported format: {format}"})
            
    except Exception as e:
        logger.error(f"Failed to export playlist: {e}")
        return json.dumps({"error": str(e)})


@tool
def match_track_across_platforms(title: str, artist: str) -> Dict[str, Any]:
    """Find the same track across different platforms."""
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
    from difflib import SequenceMatcher
    
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


def _export_to_m3u(playlist_data: Dict[str, Any]) -> str:
    """Export playlist to M3U format."""
    lines = ["#EXTM3U"]
    lines.append(f"# Playlist: {playlist_data['name']}")
    lines.append("")
    
    for track in playlist_data["tracks"]:
        duration = track.get("duration", 0)
        title = track["title"]
        artist = track["artist"]
        
        lines.append(f"#EXTINF:{duration},{artist} - {title}")
        
        # Add URLs if available
        platform_ids = track.get("platform_ids", {})
        if "youtube" in platform_ids:
            lines.append(platform_ids["youtube"])
        elif "deezer" in platform_ids:
            lines.append(f"https://deezer.com/track/{platform_ids['deezer']}")
        elif "spotify" in platform_ids:
            lines.append(f"https://open.spotify.com/track/{platform_ids['spotify']}")
        else:
            lines.append("")
    
    return "\n".join(lines)


def _export_to_csv(playlist_data: Dict[str, Any]) -> str:
    """Export playlist to CSV format."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Title", "Artist", "Album", "Duration", "Deezer ID", "Spotify ID", "YouTube URL"])
    
    # Write tracks
    for track in playlist_data["tracks"]:
        platform_ids = track.get("platform_ids", {})
        writer.writerow([
            track["title"],
            track["artist"],
            track.get("album", ""),
            track.get("duration", 0),
            platform_ids.get("deezer", ""),
            platform_ids.get("spotify", ""),
            platform_ids.get("youtube", "")
        ])
    
    return output.getvalue()