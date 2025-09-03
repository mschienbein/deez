#!/usr/bin/env python3
"""
Debug Rekordbox database reading
"""

import sqlite3
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.rekordbox_sync import RekordboxSync

def test_decrypt():
    """Test decryption of Rekordbox database"""
    
    sync = RekordboxSync()
    
    print(f"Rekordbox DB path: {sync.rekordbox_db_path}")
    print(f"DB exists: {os.path.exists(sync.rekordbox_db_path)}")
    
    # Try to decrypt
    temp_db = "/tmp/rekordbox_debug.db"
    if os.path.exists(temp_db):
        os.remove(temp_db)
    
    print("\nAttempting decryption...")
    success = sync.decrypt_rekordbox_db(sync.rekordbox_db_path, temp_db)
    print(f"Decryption successful: {success}")
    
    if success and os.path.exists(temp_db):
        print(f"\nDecrypted DB size: {os.path.getsize(temp_db)} bytes")
        
        # Try to query it
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            print(f"\nTables found: {len(tables)}")
            for table in tables[:10]:  # Show first 10 tables
                print(f"  - {table[0]}")
            
            # Check djmdContent table
            cursor.execute("SELECT COUNT(*) FROM djmdContent WHERE Disable = 0")
            count = cursor.fetchone()[0]
            print(f"\nActive tracks in djmdContent: {count}")
            
            # Get sample track
            cursor.execute("""
                SELECT 
                    ID, Name, Artist, Album, BPM, Genre
                FROM djmdContent 
                WHERE Disable = 0 
                LIMIT 1
            """)
            track = cursor.fetchone()
            if track:
                print(f"\nSample track:")
                print(f"  ID: {track[0]}")
                print(f"  Name: {track[1]}")
                print(f"  Artist: {track[2]}")
                print(f"  Album: {track[3]}")
                print(f"  BPM: {track[4]}")
                print(f"  Genre: {track[5]}")
            
            conn.close()
        except Exception as e:
            print(f"Error querying decrypted DB: {e}")
        
        # Clean up
        os.remove(temp_db)
    else:
        print("Decryption failed or temp file not created")

if __name__ == "__main__":
    test_decrypt()