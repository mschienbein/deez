#!/usr/bin/env python3
"""
Initialize Neo4j and PostgreSQL databases for the music agent
"""

import asyncio
import os
import sys
from pathlib import Path
import logging
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.graphiti_memory import MusicMemory
from src.music_agent.utils.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_neo4j_connection():
    """Test Neo4j connection and Graphiti initialization"""
    logger.info("Testing Neo4j connection...")
    
    try:
        memory = MusicMemory()
        await memory.initialize()
        
        # Test adding a simple conversation
        await memory.add_conversation(
            user_message="Hello, music agent!",
            agent_response="Hello! I'm ready to help you discover music.",
            context={"intent": "greeting"}
        )
        
        # Test search
        results = await memory.search_memory("hello", limit=5)
        logger.info(f"✅ Neo4j/Graphiti working. Found {len(results)} results.")
        
        await memory.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Neo4j/Graphiti initialization failed: {e}")
        return False


async def test_postgres_connection():
    """Test PostgreSQL connection"""
    logger.info("Testing PostgreSQL connection...")
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "music_agent"),
            password=os.getenv("POSTGRES_PASSWORD", "music123"),
            database=os.getenv("POSTGRES_DB", "music_catalog")
        )
        
        # Test query
        version = await conn.fetchval("SELECT version()")
        logger.info(f"✅ PostgreSQL connected: {version[:50]}...")
        
        # Check if schema exists
        schema_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'music')"
        )
        
        if schema_exists:
            logger.info("✅ Music schema exists")
        else:
            logger.warning("⚠️ Music schema not found. Run migrations.")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False


async def initialize_sample_data():
    """Add sample data to test the system"""
    logger.info("Adding sample data...")
    
    try:
        memory = MusicMemory()
        await memory.initialize()
        
        # Add sample track discovery
        sample_track = {
            "id": "test_001",
            "title": "Test Track",
            "artist": "Test Artist",
            "album": "Test Album",
            "bpm": 128.0,
            "key": "8A"
        }
        
        await memory.add_track_discovery(
            track=sample_track,
            source="manual_test",
            action="initialized"
        )
        
        # Add sample preference
        await memory.add_preference(
            entity_type="genre",
            entity_name="House",
            preference_type="favorite",
            score=0.9,
            reason="Great for mixing"
        )
        
        logger.info("✅ Sample data added successfully")
        await memory.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to add sample data: {e}")
        return False


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("Music Agent Database Initialization")
    logger.info("=" * 60)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️ OPENAI_API_KEY not set. Some features may not work.")
    
    # Test connections
    neo4j_ok = await test_neo4j_connection()
    postgres_ok = await test_postgres_connection()
    
    if not neo4j_ok or not postgres_ok:
        logger.error("\n❌ Database initialization failed!")
        logger.info("\nMake sure Docker services are running:")
        logger.info("  docker-compose up -d neo4j postgres")
        return 1
    
    # Add sample data
    if input("\nAdd sample data? (y/n): ").lower() == 'y':
        await initialize_sample_data()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)