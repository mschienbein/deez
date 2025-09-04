#!/usr/bin/env python3
"""
Simple test for Mixcloud API integration.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.music_agent.integrations.mixcloud import MixcloudClient


async def simple_test():
    """Run a simple test."""
    client = MixcloudClient()
    
    try:
        await client.initialize()
        print("✅ Client initialized\n")
        
        # Direct API test
        print("Testing direct API call...")
        from src.music_agent.integrations.mixcloud.api.search import SearchAPI
        search_api = SearchAPI(client._session, client.config.api)
        
        # Debug the raw response
        print(f"Base URL: {search_api.base_url}")
        endpoint = "search/"
        params = {"q": "techno", "type": "cloudcast", "limit": 2}
        
        # Check full URL
        full_url = search_api._build_url(endpoint)
        print(f"Full URL: {full_url}")
        
        raw_data = await search_api._get(endpoint, params)
        print(f"Raw response keys: {raw_data.keys()}")
        if '_raw' in raw_data:
            print(f"Raw text response (first 200 chars): {raw_data['response'][:200]}")
        
        result = await search_api.search("techno", "cloudcast", limit=2)
        print(f"Found {len(result.items)} results")
        
        for item in result.items:
            print(f"- {item.name} by {item.user.username if item.user else 'Unknown'}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(simple_test())