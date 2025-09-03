#!/usr/bin/env python3
"""
Test Graphiti connection for Deez Music Agent
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.graphiti_memory import MusicMemory

# Ensure OpenAI API key is set from environment
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY environment variable not set!")
    print("Please set your OpenAI API key in .env file")
    sys.exit(1)


async def test_graphiti():
    """Test Graphiti memory system"""
    print("=" * 60)
    print("Testing Graphiti Memory System for Deez Music Agent")
    print("=" * 60)
    
    # Initialize memory
    memory = MusicMemory()
    try:
        print("\n1. Initializing Graphiti...")
        await memory.initialize(session_id="test_session")
        print("✅ Graphiti initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test conversation storage
    try:
        print("\n2. Testing conversation storage...")
        await memory.add_conversation(
            user_message="Can you find me some house music at 128 BPM?",
            agent_response="I'll search for house tracks at 128 BPM for you.",
            context={"intent": "music_search", "genre": "house", "bpm": 128}
        )
        print("✅ Conversation stored successfully")
    except Exception as e:
        print(f"❌ Failed to store conversation: {e}")
    
    # Test track discovery
    try:
        print("\n3. Testing track discovery...")
        sample_track = {
            "id": "test_001",
            "title": "Summer Vibes",
            "artist": "DJ Test",
            "album": "Test Album",
            "bpm": 128.0,
            "key": "8A",
            "genre": "House"
        }
        
        await memory.add_track_discovery(
            track=sample_track,
            source="deezer",
            action="added_to_library"
        )
        print("✅ Track discovery stored successfully")
    except Exception as e:
        print(f"❌ Failed to store track discovery: {e}")
    
    # Test preference storage
    try:
        print("\n4. Testing preference storage...")
        await memory.add_preference(
            entity_type="genre",
            entity_name="House",
            preference_type="favorite",
            score=0.9,
            reason="Great for mixing and energy"
        )
        print("✅ Preference stored successfully")
    except Exception as e:
        print(f"❌ Failed to store preference: {e}")
    
    # Test search
    try:
        print("\n5. Testing memory search...")
        results = await memory.search_memory("house music", limit=5)
        print(f"✅ Search returned {len(results)} results")
        
        if results:
            print("\nFirst result:")
            result = results[0]
            print(f"  Content: {result.get('content', 'N/A')[:100]}...")
            print(f"  Score: {result.get('score', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to search memory: {e}")
    
    # Test getting recent context
    try:
        print("\n6. Testing recent context retrieval...")
        context = await memory.get_recent_context(limit=5)
        print(f"✅ Retrieved {len(context)} recent context items")
        
        if context:
            print("\nMost recent item:")
            item = context[0]
            print(f"  Type: {item.get('type', 'N/A')}")
            print(f"  Content: {item.get('content', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Failed to get recent context: {e}")
    
    # Close connection
    await memory.close()
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_graphiti())