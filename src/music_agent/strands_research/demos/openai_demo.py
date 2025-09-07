#!/usr/bin/env python3
"""
OpenAI-powered demo of the Strands music research system.

This demonstrates using Strands with OpenAI as the LLM provider.
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

# Configure OpenAI provider for Strands
os.environ["STRANDS_MODEL_PROVIDER"] = "openai"
os.environ["STRANDS_MODEL"] = "gpt-3.5-turbo"

# Import after setting environment variables
from strands import Agent, tool


# ============================================================================
# TOOLS - Decorated functions for agent capabilities
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
        Merged metadata with confidence score
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
    Assess metadata quality and completeness.
    
    Args:
        metadata: Merged metadata
    
    Returns:
        Quality assessment report
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
# OPENAI-CONFIGURED AGENTS
# ============================================================================

def create_data_collector(platform: str) -> Agent:
    """
    Create a data collector agent for a specific platform.
    
    Uses OpenAI provider through environment configuration.
    """
    tools = {
        "spotify": [search_spotify],
        "beatport": [search_beatport]
    }
    
    return Agent(
        name=f"DataCollector_{platform}",
        provider="openai",  # Explicitly set OpenAI provider
        model="gpt-3.5-turbo",
        tools=tools.get(platform, []),
        system_prompt=f"""You are a {platform} search specialist.
        When asked to search for a track, use the search_{platform} tool.
        Return the complete result from the tool."""
    )


def create_metadata_analyst() -> Agent:
    """Create metadata analyst agent with OpenAI."""
    return Agent(
        name="MetadataAnalyst",
        provider="openai",
        model="gpt-3.5-turbo",
        tools=[merge_metadata],
        system_prompt="""You merge metadata from multiple sources.
        When given search results, use the merge_metadata tool.
        Return the merged result with confidence score."""
    )


def create_quality_assessor() -> Agent:
    """Create quality assessor agent with OpenAI."""
    return Agent(
        name="QualityAssessor",
        provider="openai",
        model="gpt-3.5-turbo",
        tools=[assess_quality],
        system_prompt="""You assess metadata quality.
        When given metadata, use the assess_quality tool.
        Return the quality assessment report."""
    )


def create_acquisition_scout() -> Agent:
    """Create acquisition scout agent with OpenAI."""
    return Agent(
        name="AcquisitionScout",
        provider="openai",
        model="gpt-3.5-turbo",
        tools=[find_sources],
        system_prompt="""You find acquisition sources for tracks.
        When given metadata, use the find_sources tool.
        Return the list of available sources."""
    )


# ============================================================================
# ORCHESTRATOR - Coordinates agents
# ============================================================================

class OpenAIMusicOrchestrator:
    """
    Orchestrator using OpenAI-powered Strands agents.
    
    This implementation properly configures Strands to use OpenAI
    as the LLM provider instead of AWS Bedrock.
    """
    
    def __init__(self, platforms: List[str] = None):
        """
        Initialize with OpenAI configuration.
        
        Requires OPENAI_API_KEY environment variable to be set.
        """
        # Check for OpenAI API key
        if not os.environ.get("OPENAI_API_KEY"):
            print("⚠️  Warning: OPENAI_API_KEY not set. Set it with:")
            print("   export OPENAI_API_KEY='your-api-key-here'")
        
        self.platforms = platforms or ["spotify", "beatport"]
        
        # Create OpenAI-configured agents
        self.collectors = {
            platform: create_data_collector(platform)
            for platform in self.platforms
        }
        self.analyst = create_metadata_analyst()
        self.assessor = create_quality_assessor()
        self.scout = create_acquisition_scout()
        
        print(f"✅ Initialized with OpenAI provider")
        print(f"   Platforms: {', '.join(self.platforms)}")
    
    def research_track(self, query: str) -> Dict[str, Any]:
        """
        Research a track using OpenAI-powered agents.
        
        Args:
            query: Track search query
        
        Returns:
            Research results
        """
        print(f"\n🔍 Researching: {query}")
        start_time = datetime.now()
        
        try:
            # Step 1: Search platforms
            print("📡 Searching platforms...")
            search_results = []
            for platform, collector in self.collectors.items():
                try:
                    prompt = f"Search for this track: {query}"
                    result = collector(prompt)
                    
                    # Handle agent response
                    if isinstance(result, dict):
                        search_results.append(result)
                    else:
                        # Parse text response if needed
                        search_results.append({"platform": platform, "success": False})
                    
                    print(f"  ✓ {platform}")
                except Exception as e:
                    print(f"  ✗ {platform}: {e}")
                    search_results.append({"platform": platform, "success": False, "error": str(e)})
            
            # Step 2: Merge metadata
            print("🔀 Merging metadata...")
            merge_prompt = f"Merge these search results: {json.dumps(search_results)}"
            merged = self.analyst(merge_prompt)
            
            # Parse response if it's text
            if isinstance(merged, str):
                try:
                    merged = json.loads(merged)
                except:
                    merged = {"error": "Failed to parse merge result"}
            
            # Step 3: Assess quality
            print("📊 Assessing quality...")
            assess_prompt = f"Assess this metadata: {json.dumps(merged)}"
            quality = self.assessor(assess_prompt)
            
            # Parse response if it's text
            if isinstance(quality, str):
                try:
                    quality = json.loads(quality)
                except:
                    quality = {"error": "Failed to parse quality assessment"}
            
            # Step 4: Find sources
            print("💰 Finding sources...")
            scout_prompt = f"Find sources for: {json.dumps(merged)}"
            sources = self.scout(scout_prompt)
            
            # Parse response if it's text
            if isinstance(sources, str):
                try:
                    sources = json.loads(sources)
                except:
                    sources = []
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Compile results
            return {
                "query": query,
                "metadata": merged,
                "quality": quality,
                "sources": sources,
                "duration": duration,
                "success": True,
                "provider": "openai"
            }
            
        except Exception as e:
            print(f"❌ Research failed: {e}")
            return {
                "query": query,
                "success": False,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            }


# ============================================================================
# DEMO WITH NO LLM CALLS (Fallback)
# ============================================================================

def run_mock_demo(query: str = "deadmau5 - Strobe"):
    """Run demo with mock data (no LLM calls)."""
    print("\n" + "="*60)
    print("🎵 MUSIC RESEARCH - MOCK MODE (No API calls)")
    print("="*60)
    
    # Mock the entire flow
    search_results = [
        search_spotify(query),
        search_beatport(query)
    ]
    
    merged = merge_metadata(search_results)
    quality = assess_quality(merged)
    sources = find_sources(merged)
    
    # Display results
    print(f"\n📀 Track Information:")
    print(f"  Title:  {merged.get('title')}")
    print(f"  Artist: {merged.get('artist')}")
    print(f"  BPM:    {merged.get('bpm')}")
    print(f"  Key:    {merged.get('key')}")
    print(f"  Genre:  {merged.get('genre')}")
    
    print(f"\n📈 Quality Assessment:")
    print(f"  Completeness: {quality.get('completeness', 0):.1%}")
    print(f"  Meets Requirements: {'✅' if quality.get('meets_requirements') else '❌'}")
    
    print(f"\n💰 Acquisition Options:")
    for source in sources:
        print(f"  - {source['platform']} ({source['type']})")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the OpenAI-powered demo."""
    print("\n" + "="*60)
    print("🎵 STRANDS MUSIC RESEARCH - OPENAI PROVIDER")
    print("="*60)
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️  No OpenAI API key found!")
        print("To run with real LLM:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nRunning in MOCK mode instead...")
        run_mock_demo()
        return
    
    print(f"✅ OpenAI API key configured")
    
    # Create orchestrator
    orchestrator = OpenAIMusicOrchestrator(platforms=["spotify", "beatport"])
    
    # Test query
    query = "deadmau5 - Strobe"
    
    # Research track
    result = orchestrator.research_track(query)
    
    # Display results
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)
    
    if result.get("success"):
        if result.get("metadata"):
            metadata = result["metadata"]
            print(f"\n📀 Track Information:")
            print(f"  Title:  {metadata.get('title')}")
            print(f"  Artist: {metadata.get('artist')}")
            print(f"  BPM:    {metadata.get('bpm')}")
            print(f"  Key:    {metadata.get('key')}")
            print(f"  Genre:  {metadata.get('genre')}")
        
        if result.get("quality"):
            quality = result["quality"]
            print(f"\n📈 Quality Assessment:")
            print(f"  Completeness: {quality.get('completeness', 0):.1%}")
            print(f"  Confidence:   {quality.get('confidence', 0):.1%}")
        
        if result.get("sources"):
            sources = result["sources"]
            if isinstance(sources, list) and sources:
                print(f"\n💰 Acquisition Options: {len(sources)} found")
                for i, source in enumerate(sources[:3], 1):
                    print(f"  {i}. {source.get('platform')} ({source.get('type')})")
        
        print(f"\n⏱️  Duration: {result.get('duration', 0):.1f}s")
        print(f"🔧 Provider: {result.get('provider', 'unknown')}")
        
        # Save results
        with open("openai_demo_results.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n📁 Results saved to openai_demo_results.json")
    else:
        print(f"\n❌ Research failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
    print("="*60)


if __name__ == "__main__":
    main()