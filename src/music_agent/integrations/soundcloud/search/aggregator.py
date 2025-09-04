"""
Search result aggregation for SoundCloud.

Provides statistics and insights from search results.
"""

import logging
from typing import List, Dict, Any, Union, Optional
from datetime import datetime
from collections import Counter, defaultdict

from ..models.track import Track
from ..models.playlist import Playlist
from ..models.user import User

logger = logging.getLogger(__name__)


class SearchAggregator:
    """Aggregates and analyzes search results."""
    
    def aggregate(self, results: Union[List, Dict]) -> Dict[str, Any]:
        """
        Aggregate search results with statistics.
        
        Args:
            results: Search results (list or dict)
            
        Returns:
            Aggregation statistics
        """
        if isinstance(results, dict):
            # Multi-type results
            return self._aggregate_multi(results)
        elif isinstance(results, list):
            # Single-type results
            return self._aggregate_list(results)
        else:
            return {}
    
    def _aggregate_multi(self, results: Dict[str, List]) -> Dict[str, Any]:
        """Aggregate multi-type search results."""
        aggregation = {
            "total_count": 0,
            "type_counts": {},
            "type_stats": {},
        }
        
        for result_type, items in results.items():
            if items:
                aggregation["type_counts"][result_type] = len(items)
                aggregation["total_count"] += len(items)
                aggregation["type_stats"][result_type] = self._aggregate_list(items)
        
        return aggregation
    
    def _aggregate_list(self, results: List) -> Dict[str, Any]:
        """Aggregate single-type search results."""
        if not results:
            return {"count": 0}
        
        # Determine result type
        first_item = results[0]
        
        if isinstance(first_item, Track):
            return self._aggregate_tracks(results)
        elif isinstance(first_item, Playlist):
            return self._aggregate_playlists(results)
        elif isinstance(first_item, User):
            return self._aggregate_users(results)
        else:
            return {"count": len(results)}
    
    def _aggregate_tracks(self, tracks: List[Track]) -> Dict[str, Any]:
        """Aggregate track search results."""
        stats = {
            "count": len(tracks),
            "total_duration": 0,
            "average_duration": 0,
            "total_plays": 0,
            "total_likes": 0,
            "total_reposts": 0,
            "total_comments": 0,
            "genres": Counter(),
            "artists": Counter(),
            "years": Counter(),
            "licenses": Counter(),
            "tags": Counter(),
            "downloadable_count": 0,
            "streamable_count": 0,
            "monetized_count": 0,
            "most_played": None,
            "most_liked": None,
            "longest": None,
            "shortest": None,
        }
        
        durations = []
        plays = []
        likes = []
        
        for track in tracks:
            # Duration stats
            if track.duration:
                stats["total_duration"] += track.duration
                durations.append(track.duration)
            
            # Engagement stats
            if track.playback_count:
                stats["total_plays"] += track.playback_count
                plays.append(track.playback_count)
            
            if track.likes_count:
                stats["total_likes"] += track.likes_count
                likes.append(track.likes_count)
            
            if track.reposts_count:
                stats["total_reposts"] += track.reposts_count
            
            if track.comment_count:
                stats["total_comments"] += track.comment_count
            
            # Categorization
            if track.genre:
                stats["genres"][track.genre] += 1
            
            if track.artist:
                stats["artists"][track.artist] += 1
            
            if track.created_at:
                year = track.created_at.year
                stats["years"][year] += 1
            
            if track.license:
                stats["licenses"][track.license] += 1
            
            # Tags
            for tag in track.tags:
                stats["tags"][tag] += 1
            
            # Availability
            if track.downloadable:
                stats["downloadable_count"] += 1
            
            if track.streamable:
                stats["streamable_count"] += 1
            
            if track.monetization_model:
                stats["monetized_count"] += 1
        
        # Calculate averages
        if durations:
            stats["average_duration"] = sum(durations) / len(durations)
        
        # Find extremes
        if plays:
            max_plays_idx = plays.index(max(plays))
            stats["most_played"] = {
                "track": tracks[max_plays_idx].title,
                "artist": tracks[max_plays_idx].artist,
                "plays": plays[max_plays_idx],
            }
        
        if likes:
            max_likes_idx = likes.index(max(likes))
            stats["most_liked"] = {
                "track": tracks[max_likes_idx].title,
                "artist": tracks[max_likes_idx].artist,
                "likes": likes[max_likes_idx],
            }
        
        if durations:
            longest_idx = durations.index(max(durations))
            shortest_idx = durations.index(min(durations))
            
            stats["longest"] = {
                "track": tracks[longest_idx].title,
                "duration": durations[longest_idx] / 1000,  # Convert to seconds
            }
            
            stats["shortest"] = {
                "track": tracks[shortest_idx].title,
                "duration": durations[shortest_idx] / 1000,
            }
        
        # Convert counters to sorted lists
        stats["genres"] = self._counter_to_list(stats["genres"], 10)
        stats["artists"] = self._counter_to_list(stats["artists"], 10)
        stats["years"] = self._counter_to_list(stats["years"])
        stats["licenses"] = self._counter_to_list(stats["licenses"])
        stats["tags"] = self._counter_to_list(stats["tags"], 20)
        
        return stats
    
    def _aggregate_playlists(self, playlists: List[Playlist]) -> Dict[str, Any]:
        """Aggregate playlist search results."""
        stats = {
            "count": len(playlists),
            "total_tracks": 0,
            "average_tracks": 0,
            "total_duration": 0,
            "total_likes": 0,
            "total_reposts": 0,
            "genres": Counter(),
            "creators": Counter(),
            "types": Counter(),
            "tags": Counter(),
            "album_count": 0,
            "most_tracks": None,
            "most_liked": None,
        }
        
        track_counts = []
        likes = []
        
        for playlist in playlists:
            # Track stats
            if playlist.track_count:
                stats["total_tracks"] += playlist.track_count
                track_counts.append(playlist.track_count)
            
            # Duration
            if playlist.duration:
                stats["total_duration"] += playlist.duration
            
            # Engagement
            if playlist.likes_count:
                stats["total_likes"] += playlist.likes_count
                likes.append(playlist.likes_count)
            
            if playlist.reposts_count:
                stats["total_reposts"] += playlist.reposts_count
            
            # Categorization
            if playlist.genre:
                stats["genres"][playlist.genre] += 1
            
            if playlist.username:
                stats["creators"][playlist.username] += 1
            
            stats["types"][playlist.playlist_type] += 1
            
            # Tags
            for tag in playlist.tags:
                stats["tags"][tag] += 1
            
            # Album count
            if playlist.is_album:
                stats["album_count"] += 1
        
        # Calculate averages
        if track_counts:
            stats["average_tracks"] = sum(track_counts) / len(track_counts)
        
        # Find extremes
        if track_counts:
            max_tracks_idx = track_counts.index(max(track_counts))
            stats["most_tracks"] = {
                "playlist": playlists[max_tracks_idx].title,
                "tracks": track_counts[max_tracks_idx],
            }
        
        if likes:
            max_likes_idx = likes.index(max(likes))
            stats["most_liked"] = {
                "playlist": playlists[max_likes_idx].title,
                "likes": likes[max_likes_idx],
            }
        
        # Convert counters
        stats["genres"] = self._counter_to_list(stats["genres"], 10)
        stats["creators"] = self._counter_to_list(stats["creators"], 10)
        stats["types"] = self._counter_to_list(stats["types"])
        stats["tags"] = self._counter_to_list(stats["tags"], 20)
        
        return stats
    
    def _aggregate_users(self, users: List[User]) -> Dict[str, Any]:
        """Aggregate user search results."""
        stats = {
            "count": len(users),
            "total_tracks": 0,
            "total_playlists": 0,
            "total_followers": 0,
            "total_followings": 0,
            "verified_count": 0,
            "pro_count": 0,
            "countries": Counter(),
            "cities": Counter(),
            "plans": Counter(),
            "most_followed": None,
            "most_tracks": None,
        }
        
        followers = []
        track_counts = []
        
        for user in users:
            # Content stats
            if user.track_count:
                stats["total_tracks"] += user.track_count
                track_counts.append(user.track_count)
            
            if user.playlist_count:
                stats["total_playlists"] += user.playlist_count
            
            # Social stats
            if user.followers_count:
                stats["total_followers"] += user.followers_count
                followers.append(user.followers_count)
            
            if user.followings_count:
                stats["total_followings"] += user.followings_count
            
            # Status
            if user.verified:
                stats["verified_count"] += 1
            
            if user.is_pro:
                stats["pro_count"] += 1
            
            stats["plans"][user.plan] += 1
            
            # Location
            if user.country:
                stats["countries"][user.country] += 1
            
            if user.city:
                stats["cities"][user.city] += 1
        
        # Find extremes
        if followers:
            max_followers_idx = followers.index(max(followers))
            stats["most_followed"] = {
                "user": users[max_followers_idx].username,
                "followers": followers[max_followers_idx],
            }
        
        if track_counts:
            max_tracks_idx = track_counts.index(max(track_counts))
            stats["most_tracks"] = {
                "user": users[max_tracks_idx].username,
                "tracks": track_counts[max_tracks_idx],
            }
        
        # Convert counters
        stats["countries"] = self._counter_to_list(stats["countries"], 10)
        stats["cities"] = self._counter_to_list(stats["cities"], 10)
        stats["plans"] = self._counter_to_list(stats["plans"])
        
        return stats
    
    def _counter_to_list(
        self,
        counter: Counter,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Convert counter to sorted list of dicts."""
        items = []
        
        for value, count in counter.most_common(limit):
            items.append({"value": value, "count": count})
        
        return items
    
    def get_insights(self, stats: Dict[str, Any]) -> List[str]:
        """
        Generate insights from aggregated statistics.
        
        Args:
            stats: Aggregation statistics
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Track insights
        if "average_duration" in stats:
            avg_minutes = stats["average_duration"] / 60000
            insights.append(f"Average track duration: {avg_minutes:.1f} minutes")
        
        if "downloadable_count" in stats and stats["count"] > 0:
            download_pct = (stats["downloadable_count"] / stats["count"]) * 100
            insights.append(f"{download_pct:.1f}% of tracks are downloadable")
        
        if "most_played" in stats and stats["most_played"]:
            insights.append(
                f"Most played: {stats['most_played']['track']} "
                f"({stats['most_played']['plays']:,} plays)"
            )
        
        # Genre insights
        if "genres" in stats and stats["genres"]:
            top_genre = stats["genres"][0]
            insights.append(f"Most common genre: {top_genre['value']} ({top_genre['count']} tracks)")
        
        # Artist insights
        if "artists" in stats and stats["artists"]:
            top_artist = stats["artists"][0]
            if top_artist["count"] > 1:
                insights.append(f"Top artist: {top_artist['value']} ({top_artist['count']} tracks)")
        
        # Playlist insights
        if "album_count" in stats and stats["count"] > 0:
            album_pct = (stats["album_count"] / stats["count"]) * 100
            insights.append(f"{album_pct:.1f}% of playlists are albums")
        
        # User insights
        if "verified_count" in stats and stats["count"] > 0:
            verified_pct = (stats["verified_count"] / stats["count"]) * 100
            insights.append(f"{verified_pct:.1f}% of users are verified")
        
        return insights


__all__ = ["SearchAggregator"]