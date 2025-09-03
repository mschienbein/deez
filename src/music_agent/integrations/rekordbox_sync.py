"""
Rekordbox Database Integration
Syncs music library data from Rekordbox to Neo4j/PostgreSQL
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import asyncpg
# Note: Decryption is handled by sqlcipher3 directly
# No need for manual AES decryption
import hashlib

from .graphiti_memory import MusicMemory

logger = logging.getLogger(__name__)


class RekordboxSync:
    """Sync Rekordbox database with music agent memory"""
    
    # Rekordbox database encryption key (publicly known)
    ENCRYPTION_KEY = "402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497"
    
    def __init__(self):
        self.rekordbox_db_path = os.path.expanduser(
            os.getenv("REKORDBOX_DB_PATH", "~/Library/Pioneer/rekordbox/master.db")
        )
        self.postgres_conn = None
        self.memory = MusicMemory()
        
    async def initialize(self, skip_graphiti: bool = False):
        """Initialize connections"""
        # Initialize Graphiti memory (optional)
        if not skip_graphiti:
            try:
                await self.memory.initialize(session_id="rekordbox_sync")
                logger.info("Graphiti memory initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Graphiti: {e}")
                # Continue without Graphiti
        
        # Connect to PostgreSQL
        self.postgres_conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "music_agent"),
            password=os.getenv("POSTGRES_PASSWORD", "music123"),
            database=os.getenv("POSTGRES_DB", "music_catalog")
        )
        
        logger.info("Rekordbox sync initialized")
    
    def decrypt_rekordbox_db(self, encrypted_db_path: str, output_path: str):
        """Decrypt Rekordbox database using SQLCipher"""
        try:
            # Remove existing decrypted file if it exists
            if os.path.exists(output_path):
                os.remove(output_path)
                
            # Use SQLCipher to decrypt (requires sqlcipher3 binary)
            import subprocess
            
            # Create SQL script to decrypt (no 'x' prefix needed)
            decrypt_sql = f"""
            PRAGMA key = '{self.ENCRYPTION_KEY}';
            ATTACH DATABASE '{output_path}' AS plaintext KEY '';
            SELECT sqlcipher_export('plaintext');
            DETACH DATABASE plaintext;
            """
            
            # Run sqlcipher command
            process = subprocess.run(
                ["sqlcipher", encrypted_db_path],
                input=decrypt_sql.encode(),
                capture_output=True
            )
            
            if process.returncode == 0:
                logger.info(f"Successfully decrypted Rekordbox database to {output_path}")
                return True
            else:
                logger.error(f"Failed to decrypt: {process.stderr.decode()}")
                return False
                
        except FileNotFoundError:
            logger.error("sqlcipher not found. Install with: brew install sqlcipher")
            return False
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return False
    
    async def sync_tracks(self):
        """Sync tracks from Rekordbox to our databases"""
        
        # Decrypt database to temp location
        temp_db = "/tmp/rekordbox_decrypted.db"
        
        if not self.decrypt_rekordbox_db(self.rekordbox_db_path, temp_db):
            logger.error("Failed to decrypt Rekordbox database")
            return
        
        try:
            # Connect to decrypted database
            conn = sqlite3.connect(temp_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query tracks from Rekordbox with artist/album joins
            query = """
            SELECT 
                c.ID as id,
                c.Title as title,
                a.Name as artist,
                al.Name as album,
                g.Name as genre,
                c.BPM as bpm,
                c.Rating as rating,
                c.ColorID as color,
                c.Commnt as comment,
                k.ScaleName as key,
                c.Length as duration,
                c.BitRate as bitrate,
                c.SampleRate as sample_rate,
                c.FolderPath as file_path,
                c.DateCreated as date_added,
                c.updated_at as date_modified,
                c.DJPlayCount as play_count
            FROM djmdContent c
            LEFT JOIN djmdArtist a ON c.ArtistID = a.ID
            LEFT JOIN djmdAlbum al ON c.AlbumID = al.ID
            LEFT JOIN djmdGenre g ON c.GenreID = g.ID
            LEFT JOIN djmdKey k ON c.KeyID = k.ID
            WHERE c.rb_local_deleted = 0
            ORDER BY c.created_at DESC
            LIMIT 1000
            """
            
            cursor.execute(query)
            tracks = cursor.fetchall()
            
            logger.info(f"Found {len(tracks)} tracks in Rekordbox")
            
            # Process each track
            for track in tracks:
                await self.process_track(dict(track))
            
            # Sync playlists
            await self.sync_playlists(cursor)
            
            # Sync cue points
            await self.sync_cue_points(cursor)
            
            conn.close()
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    async def process_track(self, track: Dict[str, Any]):
        """Process a single track"""
        
        # Convert Rekordbox data to our format
        # Rekordbox rating is 0-255, convert to 1-5 scale
        rating = None
        if track["rating"] is not None:
            # Map 0-255 to 1-5
            if track["rating"] == 0:
                rating = None  # No rating
            else:
                rating = min(5, max(1, int(track["rating"] * 5 / 255) + 1))
        
        track_data = {
            "id": f"rekordbox_{track['id']}",
            "title": track["title"],
            "artist": track["artist"],
            "album": track["album"],
            "genre": track["genre"],
            "bpm": float(track["bpm"]) / 100 if track["bpm"] else None,  # RB stores BPM * 100
            "key": track["key"],  # Key is already text from join
            "rating": rating,
            "color": self.convert_color(track["color"]),
            "comment": track["comment"],
            "duration_ms": track["duration"] * 1000 if track["duration"] else None,
            "bitrate": track["bitrate"],
            "sample_rate": track["sample_rate"],
            "file_path": track["file_path"],
            "play_count": track["play_count"] or 0
        }
        
        # Store in PostgreSQL
        await self.store_track_postgres(track_data)
        
        # Add to Graphiti memory with error handling
        if self.memory.initialized:
            try:
                await self.memory.add_track_discovery(
                    track=track_data,
                    source="rekordbox",
                    action="synced"
                )
            except Exception as e:
                logger.warning(f"Failed to add track to Graphiti: {e}")
                # Continue anyway - PostgreSQL storage succeeded
        
    async def store_track_postgres(self, track: Dict[str, Any]):
        """Store track in PostgreSQL"""
        
        import json
        
        query = """
        INSERT INTO music.tracks (
            title, bpm, key, rating,
            duration_ms, bitrate, sample_rate,
            file_path, play_count, metadata
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb
        )
        ON CONFLICT (id) DO UPDATE SET
            bpm = EXCLUDED.bpm,
            key = EXCLUDED.key,
            rating = EXCLUDED.rating,
            play_count = EXCLUDED.play_count,
            updated_at = CURRENT_TIMESTAMP
        """
        
        await self.postgres_conn.execute(
            query,
            track["title"],
            track["bpm"],
            track["key"],
            track["rating"],
            track["duration_ms"],
            track["bitrate"],
            track["sample_rate"],
            track["file_path"],
            track["play_count"],
            json.dumps({"rekordbox_id": track["id"], "color": track["color"], "comment": track["comment"]})
        )
    
    async def sync_playlists(self, cursor):
        """Sync playlists from Rekordbox"""
        
        query = """
        SELECT 
            p.ID as id,
            p.Name as name,
            p.ParentID as parent_id,
            p.Seq as position
        FROM djmdPlaylist p
        """
        
        cursor.execute(query)
        playlists = cursor.fetchall()
        
        logger.info(f"Found {len(playlists)} playlists")
        
        for playlist in playlists:
            # Get tracks in playlist
            tracks_query = """
            SELECT 
                s.ContentID as track_id,
                s.TrackNo as position
            FROM djmdSongPlaylist s
            WHERE s.PlaylistID = ?
            ORDER BY s.TrackNo
            """
            
            cursor.execute(tracks_query, (playlist["id"],))
            playlist_tracks = cursor.fetchall()
            
            # Store playlist info in memory
            playlist_data = {
                "id": f"rekordbox_playlist_{playlist['id']}",
                "name": playlist["name"],
                "track_count": len(playlist_tracks)
            }
            
            # Add to Graphiti (if initialized)
            if self.memory.initialized:
                try:
                    await self.memory.add_preference(
                        entity_type="playlist",
                        entity_name=playlist["name"],
                        preference_type="created",
                        score=0.8,
                        reason=f"Rekordbox playlist with {len(playlist_tracks)} tracks"
                    )
                except Exception as e:
                    logger.warning(f"Failed to add playlist to Graphiti: {e}")
    
    async def sync_cue_points(self, cursor):
        """Sync cue points and hot cues"""
        
        query = """
        SELECT 
            c.ContentID as track_id,
            c.Kind as cue_type,
            c.InMsec as position_ms,
            c.OutMsec as out_position_ms,
            c.Color as color,
            c.Comment as comment
        FROM djmdCue c
        WHERE c.ContentID IS NOT NULL
        """
        
        cursor.execute(query)
        cues = cursor.fetchall()
        
        logger.info(f"Found {len(cues)} cue points")
        
        # Store cue points in PostgreSQL
        for cue in cues:
            await self.store_cue_point(dict(cue))
    
    async def store_cue_point(self, cue: Dict[str, Any]):
        """Store cue point in PostgreSQL"""
        
        # Store as JSON in track metadata for now
        # TODO: Create dedicated cue_points table if needed
        pass
    
    def convert_key_id(self, rb_key: Optional[int]) -> Optional[str]:
        """Convert Rekordbox key ID to Camelot notation"""
        
        if not rb_key:
            return None
            
        # Rekordbox key mapping to Camelot
        key_map = {
            1: "8B", 2: "3B", 3: "10B", 4: "5B", 5: "12B", 6: "7B",
            7: "2B", 8: "9B", 9: "4B", 10: "11B", 11: "6B", 12: "1B",
            13: "5A", 14: "12A", 15: "7A", 16: "2A", 17: "9A", 18: "4A",
            19: "11A", 20: "6A", 21: "1A", 22: "8A", 23: "3A", 24: "10A"
        }
        
        return key_map.get(rb_key)
    
    def convert_color(self, color_id: Optional[int]) -> Optional[str]:
        """Convert Rekordbox color ID to color name"""
        
        if not color_id:
            return None
            
        colors = {
            1: "red", 2: "orange", 3: "yellow", 4: "green",
            5: "aqua", 6: "blue", 7: "purple", 8: "pink"
        }
        
        return colors.get(color_id)
    
    def convert_cue_color(self, color: Optional[int]) -> Optional[str]:
        """Convert cue color to color name"""
        
        if color is None:
            return None
            
        # Rekordbox uses RGB values, we'll map common ones
        color_map = {
            0xFF0000: "red",
            0xFFA500: "orange", 
            0xFFFF00: "yellow",
            0x00FF00: "green",
            0x00FFFF: "aqua",
            0x0000FF: "blue",
            0x800080: "purple",
            0xFFC0CB: "pink"
        }
        
        return color_map.get(color, "none")
    
    def get_cue_type(self, type_id: int) -> str:
        """Get cue type from Rekordbox type ID"""
        
        cue_types = {
            0: "cue", 1: "fade_in", 2: "fade_out", 3: "load",
            4: "loop", 5: "hot_cue"
        }
        
        return cue_types.get(type_id, "cue")
    
    async def close(self):
        """Close connections"""
        
        if self.postgres_conn:
            await self.postgres_conn.close()
        
        await self.memory.close()


async def main():
    """Run Rekordbox sync"""
    
    logging.basicConfig(level=logging.INFO)
    
    sync = RekordboxSync()
    
    try:
        await sync.initialize()
        await sync.sync_tracks()
        logger.info("✅ Rekordbox sync completed successfully")
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
    finally:
        await sync.close()


if __name__ == "__main__":
    asyncio.run(main())