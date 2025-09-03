#!/usr/bin/env python3
"""
Test Rekordbox sync with debugging
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.rekordbox_sync import RekordboxSync

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure OpenAI API key is set from environment
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY environment variable not set!")
    print("Please set your OpenAI API key in .env file")
    sys.exit(1)

async def test_sync():
    """Test sync with debugging"""
    sync = RekordboxSync()
    
    try:
        logger.info("Initializing...")
        await sync.initialize()
        
        logger.info("Starting sync...")
        await sync.sync_tracks()
        
        logger.info("Sync completed successfully")
        
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
    finally:
        await sync.close()

if __name__ == "__main__":
    asyncio.run(test_sync())