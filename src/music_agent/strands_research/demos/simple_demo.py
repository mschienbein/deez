#!/usr/bin/env python3
"""
Simple working demo of the Strands music research system.

This demonstrates the correct usage of Strands framework with minimal complexity.
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

from strands import Agent, tool


# ============================================================================
# SIMPLE TOOLS - Basic implementations that actually work
# ============================================================================

@tool
def search_spotify(query: str) -> Dict[str, Any]:
    """
    Search Spotify for track metadata.
    
    Args:
        query: Search query (artist - title format)
    
    Returns:
        Track metadata from Spotify
    """
    # Mock response for demo
    return {
        "platform": "spotify",
        "success": True,
        "track": {
            "title": "Strobe",
            "artist": "deadmau5",
            "album": "For Lack of a Better Name",
            "duration_ms": 634000,
            "bpm": 128.0,
            "key": "C# min",
            "isrc": "USUS11000356",
            "spotify_id": "3Oa0j5wSr3Z3BmP8Qzqjyj",
            "energy": 0.72,
            "danceability": 0.68
        }
    }


@tool
def search_beatport(query: str) -> Dict[str, Any]:
    """
    Search Beatport for electronic music metadata.
    
    Args:
        query: Search query
    
    Returns:
        Track metadata from Beatport
    """
    return {
        "platform": "beatport",
        "success": True,
        "track": {
            "title": "Strobe",
            "artist": "deadmau5",
            "mix": "Original Mix",
            "bpm": 128.0,
            "key": "C# min",
            "genre": "Progressive House",
            "label": "mau5trap",
            "release_date": "2009-10-06",
            "beatport_id": 1234567,
            "price": 2.49
        }
    }


@tool
def merge_metadata(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge metadata from multiple sources.
    
    Args:
        results: List of search results from different platforms
    
    Returns:
        Merged metadata
    """
    if not results:
        return {"error": "No results to merge"}
    
    # Simple merge - take first non-null value for each field
    merged = {
        "title": "",
        "artist": "",
        "bpm": None,
        "key": "",
        "genre": "",
        "sources": []
    }
    
    for result in results:
        if result.get("success") and "track" in result:
            track = result["track"]
            platform = result.get("platform", "unknown")
            
            merged["sources"].append(platform)
            merged["title"] = merged["title"] or track.get("title", "")
            merged["artist"] = merged["artist"] or track.get("artist", "")
            merged["bpm"] = merged["bpm"] or track.get("bpm")
            merged["key"] = merged["key"] or track.get("key", "")
            merged["genre"] = merged["genre"] or track.get("genre", "")
    
    merged["confidence"] = len(merged["sources"]) / 3.0  # Simple confidence
    return merged


@tool
def assess_quality(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess metadata quality.
    
    Args:
        metadata: Merged metadata
    
    Returns:
        Quality assessment
    """
    required_fields = ["title", "artist", "bpm", "key", "genre"]
    present = sum(1 for field in required_fields if metadata.get(field))
    completeness = present / len(required_fields)
    
    return {
        "completeness": completeness,
        "missing_fields": [f for f in required_fields if not metadata.get(f)],
        "confidence": metadata.get("confidence", 0),
        "meets_requirements": completeness >= 0.8,
        "sources_count": len(metadata.get("sources", []))
    }


@tool
def find_sources(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find acquisition sources for a track.
    
    Args:
        metadata: Track metadata
    
    Returns:
        List of acquisition options
    """
    sources = []
    
    # Add Beatport purchase option
    if "beatport" in metadata.get("sources", []):
        sources.append({
            "platform": "beatport",
            "type": "purchase",
            "quality": "lossless",
            "price": 2.49,
            "formats": ["WAV", "AIFF", "MP3 320"]
        })
    
    # Add Spotify streaming option
    if "spotify" in metadata.get("sources", []):
        sources.append({
            "platform": "spotify",
            "type": "stream",
            "quality": "high",
            "subscription_required": True
        })
    
    return sources


# ============================================================================
# SIMPLE AGENTS - Using Strands Agent class correctly
# ============================================================================

class SimpleDataCollector(Agent):
    """Simple data collector agent for a specific platform."""
    
    def __init__(self, platform: str):
        self.platform = platform
        
        # Select appropriate tool
        tools = {
            "spotify": [search_spotify],
            "beatport": [search_beatport]
        }
        
        super().__init__(
            name=f"DataCollector_{platform}",
            model="gpt-3.5-turbo",  # Use a supported model
            tools=tools.get(platform, []),
            system_prompt=f"You are a {platform} search specialist. Search for tracks and return metadata."
        )


class SimpleAnalyst(Agent):
    """Simple metadata analyst agent."""
    
    def __init__(self):
        super().__init__(
            name="MetadataAnalyst",
            model="gpt-3.5-turbo",
            tools=[merge_metadata],
            system_prompt="You merge metadata from multiple sources. Use the merge_metadata tool."
        )


class SimpleAssessor(Agent):
    """Simple quality assessor agent."""
    
    def __init__(self):
        super().__init__(
            name="QualityAssessor",
            model="gpt-3.5-turbo",
            tools=[assess_quality],
            system_prompt="You assess metadata quality. Use the assess_quality tool."
        )


class SimpleScout(Agent):
    """Simple acquisition scout agent."""
    
    def __init__(self):
        super().__init__(
            name="AcquisitionScout",
            model="gpt-3.5-turbo",
            tools=[find_sources],
            system_prompt="You find acquisition sources. Use the find_sources tool."
        )


# ============================================================================
# SIMPLE ORCHESTRATOR - Basic coordination
# ============================================================================

class SimpleMusicOrchestrator:
    """
    Simple orchestrator for music research using Strands.
    
    This is a minimal working implementation that demonstrates
    the correct patterns without unnecessary complexity.
    """
    
    def __init__(self, platforms: List[str] = None):
        """Initialize with specified platforms."""
        self.platforms = platforms or ["spotify", "beatport"]
        
        # Create agents
        self.collectors = {
            platform: SimpleDataCollector(platform)
            for platform in self.platforms
        }
        self.analyst = SimpleAnalyst()
        self.assessor = SimpleAssessor()
        self.scout = SimpleScout()
    
    def research_track(self, query: str) -> Dict[str, Any]:
        """
        Research a track using all agents.
        
        Args:
            query: Track search query
        
        Returns:
            Research results
        """
        print(f"\n🔍 Researching: {query}")
        start_time = datetime.now()
        
        # Step 1: Search platforms
        print("📡 Searching platforms...")
        search_results = []
        for platform, collector in self.collectors.items():
            try:
                prompt = f"Search for this track: {query}"
                result = collector(prompt)
                search_results.append(result)
                print(f"  ✓ {platform}")
            except Exception as e:
                print(f"  ✗ {platform}: {e}")
        
        # Step 2: Merge metadata
        print("🔀 Merging metadata...")
        merge_prompt = f"Merge these search results: {search_results}"
        merged = self.analyst(merge_prompt)
        
        # Step 3: Assess quality
        print("📊 Assessing quality...")
        assess_prompt = f"Assess this metadata: {merged}"
        quality = self.assessor(assess_prompt)
        
        # Step 4: Find sources
        print("💰 Finding sources...")
        scout_prompt = f"Find sources for: {merged}"
        sources = self.scout(scout_prompt)
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Compile results
        return {
            "query": query,
            "metadata": merged,
            "quality": quality,
            "sources": sources,
            "duration": duration,
            "success": True
        }


# ============================================================================
# MAIN DEMO - Show it working
# ============================================================================

def main():
    """Run the simple demo."""
    print("\n" + "="*60)
    print("🎵 STRANDS MUSIC RESEARCH - SIMPLE WORKING DEMO")
    print("="*60)
    
    # Create orchestrator
    orchestrator = SimpleMusicOrchestrator(platforms=["spotify", "beatport"])
    
    # Test query
    query = "deadmau5 - Strobe"
    
    try:
        # Research track
        result = orchestrator.research_track(query)
        
        # Print results
        print("\n" + "="*60)
        print("📊 RESULTS")
        print("="*60)
        
        if result.get("metadata"):
            metadata = result["metadata"]
            print(f"\n📀 Track Information:")
            print(f"  Title:  {metadata.get('title')}")
            print(f"  Artist: {metadata.get('artist')}")
            print(f"  BPM:    {metadata.get('bpm')}")
            print(f"  Key:    {metadata.get('key')}")
            print(f"  Genre:  {metadata.get('genre')}")
            print(f"  Sources: {', '.join(metadata.get('sources', []))}")
        
        if result.get("quality"):
            quality = result["quality"]
            print(f"\n📈 Quality Assessment:")
            print(f"  Completeness: {quality.get('completeness', 0):.1%}")
            print(f"  Confidence:   {quality.get('confidence', 0):.1%}")
            print(f"  Meets Requirements: {'✅' if quality.get('meets_requirements') else '❌'}")
        
        if result.get("sources"):
            sources = result["sources"]
            if isinstance(sources, list):
                print(f"\n💰 Acquisition Options: {len(sources)} found")
                for i, source in enumerate(sources[:3], 1):
                    print(f"  {i}. {source.get('platform')} ({source.get('type')}) - {source.get('quality')}")
        
        print(f"\n⏱️  Duration: {result.get('duration', 0):.1f}s")
        
        # Save results
        with open("simple_demo_results.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n📁 Results saved to simple_demo_results.json")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
    print("="*60)


if __name__ == "__main__":
    # Run the async main function
    main()