#!/usr/bin/env python3
"""
Strands Music Research System - OpenAI Provider Implementation.

This demonstrates the CORRECT way to use Strands with OpenAI as the LLM provider.
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

from strands import Agent, tool
from strands.models.openai import OpenAIModel
from pydantic import BaseModel, Field


# ============================================================================
# DATA MODELS
# ============================================================================

class TrackMetadata(BaseModel):
    """Structured track metadata."""
    title: str = Field(description="Track title")
    artist: str = Field(description="Artist name")
    album: str = Field(default="", description="Album name")
    bpm: float = Field(default=None, description="Beats per minute")
    key: str = Field(default="", description="Musical key")
    genre: str = Field(default="", description="Genre")
    sources: List[str] = Field(default_factory=list, description="Data sources")
    confidence: float = Field(default=0.0, description="Confidence score")


class QualityReport(BaseModel):
    """Quality assessment report."""
    completeness: float = Field(description="Percentage of fields filled")
    missing_fields: List[str] = Field(default_factory=list)
    confidence: float = Field(description="Overall confidence")
    meets_requirements: bool = Field(description="Meets quality threshold")
    sources_count: int = Field(description="Number of sources")


# ============================================================================
# TOOLS
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
    print(f"    [Tool] Searching Spotify for: {query}")
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
    print(f"    [Tool] Searching Beatport for: {query}")
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
def search_discogs(query: str) -> Dict[str, Any]:
    """
    Search Discogs for release information.
    
    Args:
        query: Search query
    
    Returns:
        Release metadata from Discogs
    """
    print(f"    [Tool] Searching Discogs for: {query}")
    return {
        "platform": "discogs",
        "success": True,
        "release": {
            "title": "For Lack Of A Better Name",
            "artist": "Deadmau5",
            "year": 2009,
            "label": ["Ultra Records", "mau5trap"],
            "catalog_number": "UL 2339",
            "genre": ["Electronic"],
            "style": ["Progressive House", "Electro House"]
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
    print(f"    [Tool] Merging {len(results)} results")
    
    if not results:
        return {"error": "No results to merge"}
    
    merged = {
        "title": "",
        "artist": "",
        "album": "",
        "bpm": None,
        "key": "",
        "genre": "",
        "sources": []
    }
    
    for result in results:
        if result.get("success"):
            platform = result.get("platform", "unknown")
            merged["sources"].append(platform)
            
            # Extract track data from various formats
            data = result.get("track") or result.get("release", {})
            
            merged["title"] = merged["title"] or data.get("title", "")
            merged["artist"] = merged["artist"] or data.get("artist", "")
            merged["album"] = merged["album"] or data.get("album", "")
            merged["bpm"] = merged["bpm"] or data.get("bpm")
            merged["key"] = merged["key"] or data.get("key", "")
            merged["genre"] = merged["genre"] or data.get("genre", "")
            
            # Handle genre as list
            if isinstance(data.get("genre"), list) and data["genre"]:
                merged["genre"] = merged["genre"] or data["genre"][0]
    
    merged["confidence"] = len(merged["sources"]) / 3.0
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
    print(f"    [Tool] Assessing quality")
    
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
def find_acquisition_sources(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find where to purchase or stream a track.
    
    Args:
        metadata: Track metadata
    
    Returns:
        List of acquisition options
    """
    print(f"    [Tool] Finding acquisition sources")
    
    sources = []
    
    if "beatport" in metadata.get("sources", []):
        sources.append({
            "platform": "beatport",
            "type": "purchase",
            "quality": "lossless",
            "price": 2.49,
            "formats": ["WAV", "AIFF", "MP3 320"],
            "url": "https://www.beatport.com/track/strobe-original-mix/1234567"
        })
    
    if "spotify" in metadata.get("sources", []):
        sources.append({
            "platform": "spotify",
            "type": "stream",
            "quality": "high",
            "subscription_required": True,
            "url": "https://open.spotify.com/track/3Oa0j5wSr3Z3BmP8Qzqjyj"
        })
    
    return sources


# ============================================================================
# OPENAI-CONFIGURED AGENTS
# ============================================================================

def create_openai_model(api_key: str = None, model_id: str = "gpt-5") -> OpenAIModel:
    """
    Create an OpenAI model instance for Strands.
    
    Args:
        api_key: OpenAI API key (uses env var if not provided)
        model_id: Model to use (gpt-3.5-turbo, gpt-4, etc.)
    
    Returns:
        Configured OpenAIModel instance
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
    
    return OpenAIModel(
        client_args={"api_key": api_key},
        model_id=model_id,
        params={
            "max_tokens": 1000,
            "temperature": 0.7,
        }
    )


class OpenAIDataCollector:
    """Data collector agent using OpenAI."""
    
    def __init__(self, platform: str, model: OpenAIModel):
        """Initialize collector for specific platform."""
        self.platform = platform
        
        # Select tools for this platform
        tools_map = {
            "spotify": [search_spotify],
            "beatport": [search_beatport],
            "discogs": [search_discogs]
        }
        
        self.agent = Agent(
            model=model,
            tools=tools_map.get(platform, []),
            system_prompt=f"""You are a {platform} search specialist.
            When asked to search for a track, use the search_{platform} tool.
            Return the complete result from the tool."""
        )
    
    def search(self, query: str) -> Dict[str, Any]:
        """Search the platform."""
        response = self.agent(f"Search for this track: {query}")
        # The agent should return the tool result
        return response


class OpenAIMetadataAnalyst:
    """Metadata analyst agent using OpenAI."""
    
    def __init__(self, model: OpenAIModel):
        """Initialize analyst."""
        self.agent = Agent(
            model=model,
            tools=[merge_metadata],
            system_prompt="""You are a metadata analyst.
            When given search results, use the merge_metadata tool to combine them.
            Return the merged result."""
        )
    
    def analyze(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge and analyze results."""
        response = self.agent(f"Merge these search results: {json.dumps(results)}")
        return response


class OpenAIQualityAssessor:
    """Quality assessor agent using OpenAI."""
    
    def __init__(self, model: OpenAIModel):
        """Initialize assessor."""
        self.agent = Agent(
            model=model,
            tools=[assess_quality],
            system_prompt="""You assess metadata quality.
            When given metadata, use the assess_quality tool.
            Return the quality assessment."""
        )
    
    def assess(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess metadata quality."""
        response = self.agent(f"Assess this metadata: {json.dumps(metadata)}")
        return response


class OpenAIAcquisitionScout:
    """Acquisition scout agent using OpenAI."""
    
    def __init__(self, model: OpenAIModel):
        """Initialize scout."""
        self.agent = Agent(
            model=model,
            tools=[find_acquisition_sources],
            system_prompt="""You find acquisition sources for tracks.
            When given metadata, use the find_acquisition_sources tool.
            Return the list of sources."""
        )
    
    def find_sources(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find acquisition sources."""
        response = self.agent(f"Find sources for: {json.dumps(metadata)}")
        return response


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class StrandsOpenAIOrchestrator:
    """
    Music research orchestrator using Strands with OpenAI.
    
    This is the CORRECT implementation using:
    - strands.models.openai.OpenAIModel for LLM provider
    - Strands Agent class with proper configuration
    - @tool decorated functions for capabilities
    """
    
    def __init__(
        self,
        api_key: str = None,
        model_id: str = "gpt-3.5-turbo",
        platforms: List[str] = None
    ):
        """
        Initialize orchestrator with OpenAI configuration.
        
        Args:
            api_key: OpenAI API key (uses env var if not provided)
            model_id: OpenAI model to use
            platforms: List of platforms to search
        """
        print("\n🔧 Initializing Strands + OpenAI Orchestrator")
        
        # Create OpenAI model
        self.model = create_openai_model(api_key, model_id)
        print(f"✅ OpenAI Model: {model_id}")
        
        # Set platforms
        self.platforms = platforms or ["spotify", "beatport", "discogs"]
        
        # Create agents
        self.collectors = {
            platform: OpenAIDataCollector(platform, self.model)
            for platform in self.platforms
        }
        self.analyst = OpenAIMetadataAnalyst(self.model)
        self.assessor = OpenAIQualityAssessor(self.model)
        self.scout = OpenAIAcquisitionScout(self.model)
        
        print(f"✅ Platforms: {', '.join(self.platforms)}")
        print(f"✅ Agents: {len(self.collectors) + 3} initialized")
    
    def research_track(self, query: str) -> Dict[str, Any]:
        """
        Research a track using all agents.
        
        Args:
            query: Track search query
        
        Returns:
            Complete research results
        """
        print(f"\n🔍 Researching: {query}")
        start_time = datetime.now()
        
        try:
            # Phase 1: Search platforms
            print("\n📡 PHASE 1: Platform Search")
            search_results = []
            for platform, collector in self.collectors.items():
                try:
                    result = collector.search(query)
                    # Handle string responses
                    if isinstance(result, str):
                        # Try to extract JSON from response
                        import re
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                    search_results.append(result)
                    print(f"  ✓ {platform}")
                except Exception as e:
                    print(f"  ✗ {platform}: {e}")
            
            # Phase 2: Merge metadata
            print("\n🔀 PHASE 2: Metadata Analysis")
            merged = self.analyst.analyze(search_results)
            if isinstance(merged, str):
                # Extract JSON if needed
                import re
                json_match = re.search(r'\{.*\}', merged, re.DOTALL)
                if json_match:
                    merged = json.loads(json_match.group())
            print(f"  ✓ Merged {len(merged.get('sources', []))} sources")
            
            # Phase 3: Assess quality
            print("\n📊 PHASE 3: Quality Assessment")
            quality = self.assessor.assess(merged)
            if isinstance(quality, str):
                # Extract JSON if needed
                import re
                json_match = re.search(r'\{.*\}', quality, re.DOTALL)
                if json_match:
                    quality = json.loads(json_match.group())
            print(f"  ✓ Completeness: {quality.get('completeness', 0):.0%}")
            
            # Phase 4: Find sources
            print("\n💰 PHASE 4: Acquisition Sources")
            sources = self.scout.find_sources(merged)
            if isinstance(sources, str):
                # Extract JSON if needed
                import re
                json_match = re.search(r'\[.*\]', sources, re.DOTALL)
                if json_match:
                    sources = json.loads(json_match.group())
            print(f"  ✓ Found {len(sources) if isinstance(sources, list) else 0} sources")
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Determine if solved
            is_solved = (
                quality.get("meets_requirements", False) and
                len(sources) > 0 if isinstance(sources, list) else False
            )
            
            return {
                "query": query,
                "metadata": merged,
                "quality": quality,
                "sources": sources,
                "solved": is_solved,
                "confidence": merged.get("confidence", 0),
                "duration": duration,
                "success": True
            }
            
        except Exception as e:
            print(f"\n❌ Research failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "query": query,
                "success": False,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            }


# ============================================================================
# DEMO
# ============================================================================

def main():
    """Run the Strands + OpenAI demo."""
    print("\n" + "="*60)
    print("🎵 STRANDS MUSIC RESEARCH - OPENAI PROVIDER")
    print("="*60)
    print("\nThis demonstrates the CORRECT way to use Strands with OpenAI")
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️  No OpenAI API key found!")
        print("\nTo run this demo:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\nThen run:")
        print("  python openai_correct_demo.py")
        return
    
    print(f"✅ OpenAI API key configured")
    
    try:
        # Create orchestrator
        orchestrator = StrandsOpenAIOrchestrator(
            api_key=api_key,
            model_id="gpt-3.5-turbo",
            platforms=["spotify", "beatport", "discogs"]
        )
        
        # Research a track
        query = "deadmau5 - Strobe"
        result = orchestrator.research_track(query)
        
        # Display results
        print("\n" + "="*60)
        print("📊 RESULTS")
        print("="*60)
        
        if result.get("success"):
            metadata = result.get("metadata", {})
            print(f"\n📀 Track Information:")
            print(f"  Title:     {metadata.get('title')}")
            print(f"  Artist:    {metadata.get('artist')}")
            print(f"  Album:     {metadata.get('album')}")
            print(f"  BPM:       {metadata.get('bpm')}")
            print(f"  Key:       {metadata.get('key')}")
            print(f"  Genre:     {metadata.get('genre')}")
            print(f"  Sources:   {', '.join(metadata.get('sources', []))}")
            
            quality = result.get("quality", {})
            print(f"\n📈 Quality Assessment:")
            print(f"  Completeness:  {quality.get('completeness', 0):.0%}")
            print(f"  Confidence:    {quality.get('confidence', 0):.0%}")
            print(f"  Requirements:  {'✅ Met' if quality.get('meets_requirements') else '❌ Not Met'}")
            
            sources = result.get("sources", [])
            if isinstance(sources, list) and sources:
                print(f"\n💰 Acquisition Options: {len(sources)} found")
                for i, source in enumerate(sources, 1):
                    price = f"${source.get('price'):.2f}" if source.get('price') else "Subscription"
                    print(f"  {i}. {source['platform']} ({source['type']}) - {source['quality']} - {price}")
            
            print(f"\n🎯 Track Status: {'SOLVED' if result.get('solved') else 'NOT SOLVED'}")
            print(f"  Confidence: {result.get('confidence', 0):.0%}")
            print(f"  Duration: {result.get('duration', 0):.1f}s")
            
            # Save results
            with open("strands_openai_results.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n📁 Results saved to strands_openai_results.json")
        else:
            print(f"\n❌ Research failed: {result.get('error')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
    print("="*60)


if __name__ == "__main__":
    main()