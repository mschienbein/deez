#!/usr/bin/env python3
"""
Sync Rekordbox database with music agent
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.rekordbox_sync import RekordboxSync

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main sync function"""
    
    print("=" * 60)
    print("Rekordbox Database Sync")
    print("=" * 60)
    
    # Check if Rekordbox database exists
    rekordbox_db = os.path.expanduser(
        os.getenv("REKORDBOX_DB_PATH", "~/Library/Pioneer/rekordbox/master.db")
    )
    
    if not os.path.exists(rekordbox_db):
        print(f"\n❌ Rekordbox database not found at: {rekordbox_db}")
        print("\nPlease ensure:")
        print("1. Rekordbox is installed")
        print("2. You have analyzed some tracks")
        print("3. The database path is correct")
        print("\nYou can set a custom path with:")
        print("  export REKORDBOX_DB_PATH=/path/to/master.db")
        return 1
    
    print(f"\n✅ Found Rekordbox database at: {rekordbox_db}")
    
    # Check if sqlcipher is installed
    import subprocess
    try:
        result = subprocess.run(["which", "sqlcipher"], capture_output=True)
        if result.returncode != 0:
            print("\n❌ sqlcipher not found")
            print("\nInstall with:")
            print("  macOS: brew install sqlcipher")
            print("  Linux: apt-get install sqlcipher")
            return 1
    except:
        print("\n❌ Could not check for sqlcipher")
        return 1
    
    print("✅ sqlcipher is installed")
    
    # Check database connections
    print("\n🔍 Checking database connections...")
    
    # Neo4j check
    try:
        from neo4j import AsyncGraphDatabase
        
        driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USERNAME", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "deezmusic123")
            )
        )
        await driver.execute_query("RETURN 1", database_=os.getenv("NEO4J_DATABASE", "music"))
        await driver.close()
        print("✅ Neo4j connection successful")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("\nMake sure Neo4j is running:")
        print("  docker-compose up -d neo4j")
        return 1
    
    # PostgreSQL check
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "music_agent"),
            password=os.getenv("POSTGRES_PASSWORD", "music123"),
            database=os.getenv("POSTGRES_DB", "music_catalog")
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker-compose up -d postgres")
        return 1
    
    # Run sync
    print("\n" + "=" * 60)
    print("Starting Rekordbox sync...")
    print("=" * 60 + "\n")
    
    sync = RekordboxSync()
    
    try:
        # Initialize with optional Graphiti skip for faster sync
        skip_graphiti = os.getenv("SKIP_GRAPHITI", "false").lower() == "true"
        await sync.initialize(skip_graphiti=skip_graphiti)
        await sync.sync_tracks()
        
        print("\n" + "=" * 60)
        print("✅ Rekordbox sync completed successfully!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        print("\n" + "=" * 60)
        print("❌ Rekordbox sync failed!")
        print("=" * 60)
        return 1
        
    finally:
        await sync.close()


if __name__ == "__main__":
    # Ensure OpenAI API key is set from environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key in .env file")
        sys.exit(1)
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)