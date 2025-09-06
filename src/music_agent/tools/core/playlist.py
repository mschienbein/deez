"""
Core multi-platform playlist tools.

Provides playlist creation and export functionality across platforms.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from strands import tool

from ...database.schema import (
    Playlist,
    Track,
    init_database,
)
from ...utils.config import config
from .search import search_music
from .metadata import get_track_info

logger = logging.getLogger(__name__)

# Initialize database connection
db_engine, db_session_maker = init_database(config.database.url)


@tool
def create_cross_platform_playlist(name: str, tracks: List[str]) -> Dict[str, Any]:
    """
    Create playlist with tracks from multiple platforms.
    
    Args:
        name: Playlist name
        tracks: List of track specifications (can be "platform:id" or search queries)
    
    Returns:
        Playlist information with added tracks
    
    Example:
        >>> playlist = create_cross_platform_playlist(
        >>>     "My Mix", 
        >>>     ["deezer:123456", "Daft Punk Get Lucky", "spotify:4iV5W9uYEdYUVa79Axb7Rh"]
        >>> )
        >>> print(f"Created playlist with {playlist['tracks_added']} tracks")
    """
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
def export_playlist(playlist_id: str, format: str = "json") -> str:
    """
    Export playlist in various formats.
    
    Args:
        playlist_id: Database playlist ID
        format: Export format ("json", "m3u", "csv")
    
    Returns:
        Formatted playlist data as string
    
    Example:
        >>> json_data = export_playlist("123", format="json")
        >>> m3u_data = export_playlist("123", format="m3u")
    """
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