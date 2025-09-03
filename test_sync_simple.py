#!/usr/bin/env python3
"""
Test Rekordbox sync without Graphiti
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
import asyncpg
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleRekordboxSync:
    """Simple sync without Graphiti"""
    
    ENCRYPTION_KEY = "402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497"
    
    def __init__(self):
        self.rekordbox_db_path = os.path.expanduser(
            "~/Library/Pioneer/rekordbox/master.db"
        )
        self.postgres_conn = None
        
    async def initialize(self):
        """Initialize PostgreSQL connection"""
        self.postgres_conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="music_agent",
            password="music123",
            database="music_catalog"
        )
        logger.info("Connected to PostgreSQL")
    
    def decrypt_rekordbox_db(self, encrypted_db_path: str, output_path: str):
        """Decrypt Rekordbox database"""
        import subprocess
        
        decrypt_sql = f"""
        PRAGMA key = '{self.ENCRYPTION_KEY}';
        ATTACH DATABASE '{output_path}' AS plaintext KEY '';
        SELECT sqlcipher_export('plaintext');
        DETACH DATABASE plaintext;
        """
        
        process = subprocess.run(
            ["sqlcipher", encrypted_db_path],
            input=decrypt_sql.encode(),
            capture_output=True
        )
        
        return process.returncode == 0
    
    async def sync_tracks(self):
        """Sync tracks only"""
        
        # Decrypt database
        temp_db = "/tmp/rekordbox_simple.db"
        
        if not self.decrypt_rekordbox_db(self.rekordbox_db_path, temp_db):
            logger.error("Failed to decrypt Rekordbox database")
            return
        
        logger.info("Database decrypted successfully")
        
        try:
            # Connect to decrypted database
            conn = sqlite3.connect(temp_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Simple query - just get tracks
            query = """
            SELECT 
                c.ID as id,
                c.Title as title,
                c.BPM as bpm,
                c.Rating as rating,
                c.DJPlayCount as play_count
            FROM djmdContent c
            WHERE c.rb_local_deleted = 0
            LIMIT 10
            """
            
            cursor.execute(query)
            tracks = cursor.fetchall()
            
            logger.info(f"Found {len(tracks)} tracks")
            
            # Process each track
            for track in tracks:
                track_dict = dict(track)
                logger.info(f"Processing: {track_dict.get('title', 'Unknown')}")
                
                # Convert BPM
                bpm = None
                if track_dict["bpm"]:
                    bpm = float(track_dict["bpm"]) / 100
                
                # Store in PostgreSQL
                import json
                query = """
                INSERT INTO music.tracks (
                    title, bpm, rating, play_count, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5::jsonb
                )
                ON CONFLICT (id) DO UPDATE SET
                    bpm = EXCLUDED.bpm,
                    play_count = EXCLUDED.play_count
                """
                
                await self.postgres_conn.execute(
                    query,
                    track_dict["title"],
                    bpm,
                    None,  # rating needs conversion
                    track_dict["play_count"] or 0,
                    json.dumps({"rekordbox_id": track_dict["id"]})
                )
            
            conn.close()
            logger.info("Sync completed successfully")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    async def close(self):
        """Close connections"""
        if self.postgres_conn:
            await self.postgres_conn.close()

async def main():
    """Main function"""
    sync = SimpleRekordboxSync()
    
    try:
        await sync.initialize()
        await sync.sync_tracks()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await sync.close()

if __name__ == "__main__":
    asyncio.run(main())