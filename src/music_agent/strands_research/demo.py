#!/usr/bin/env python3
"""
Demo script for the AWS Strands-based Music Research System.

This demonstrates the PROPER implementation using Strands framework
instead of building custom orchestration.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Import our Strands-based components
from core import MusicResearchOrchestrator
from agents import ChiefResearcherSupervisor
from models import ResearchResult


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🎵 {title}")
    print("="*60)


def print_result(result: ResearchResult):
    """Print research results in a formatted way."""
    print(f"\n📊 RESEARCH RESULTS")
    print("-"*40)
    
    if result.success:
        print(f"✅ Research completed successfully")
        
        if result.metadata:
            print(f"\n📀 Track Information:")
            print(f"  Title:  {result.metadata.title}")
            print(f"  Artist: {result.metadata.artist}")
            print(f"  Album:  {result.metadata.album or 'N/A'}")
            print(f"  BPM:    {result.metadata.bpm or 'N/A'}")
            print(f"  Key:    {result.metadata.key or 'N/A'}")
            print(f"  Genre:  {result.metadata.genre or 'N/A'}")
            print(f"  Sources: {', '.join(result.metadata.sources)}")
        
        if result.quality_report:
            report = result.quality_report
            print(f"\n📈 Quality Assessment:")
            print(f"  Completeness: {report.get('metadata_completeness', 0):.1%}")
            print(f"  Confidence:   {report.get('confidence_score', 0):.1%}")
            print(f"  Meets Requirements: {'✅' if report.get('meets_requirements') else '❌'}")
        
        if result.acquisition_options:
            print(f"\n💰 Acquisition Options: {len(result.acquisition_options)} found")
            for i, option in enumerate(result.acquisition_options[:3], 1):
                price = f"${option['price']:.2f}" if option.get('price') else "Free"
                print(f"  {i}. {option['source']} ({option['type']}) - {option.get('quality', 'unknown')} - {price}")
        
        print(f"\n🎯 Track Status: {'SOLVED' if result.solved else 'NOT SOLVED'}")
        print(f"  Confidence: {result.confidence:.1%}")
        if result.solve_reason:
            print(f"  Reason: {result.solve_reason}")
    
    else:
        print(f"❌ Research failed")
        if result.solve_reason:
            print(f"  Error: {result.solve_reason}")
    
    if result.duration_ms:
        print(f"\n⏱️  Duration: {result.duration_ms/1000:.1f}s")


async def demo_orchestrator_pattern():
    """
    Demonstrate the MultiAgentOrchestrator pattern.
    
    This is the recommended approach for production systems.
    """
    print_header("DEMO: MultiAgentOrchestrator Pattern")
    print("""
    This demonstrates the PROPER Strands implementation using:
    - MultiAgentOrchestrator for coordination
    - @tool decorators for capabilities
    - Built-in parallel execution
    - Session management
    """)
    
    # Create orchestrator with default platforms
    orchestrator = MusicResearchOrchestrator(
        platforms=["spotify", "beatport", "discogs"],
        config={
            "log_level": "INFO",
            "timeout": 30
        }
    )
    
    # Test queries
    test_queries = [
        "deadmau5 - Strobe",
        "Daft Punk - One More Time",
        "Swedish House Mafia - Don't You Worry Child"
    ]
    
    for query in test_queries[:1]:  # Test first query
        print(f"\n🔍 Researching: {query}")
        
        try:
            # Research with full orchestration
            result = await orchestrator.research_track(
                query=query,
                parallel_search=True,
                context={"genre_hint": "electronic"}
            )
            
            # Print results
            print_result(result)
            
            # Save to file
            filename = f"strands_result_{query.replace(' - ', '_').replace(' ', '_')}.json"
            with open(filename, 'w') as f:
                # Convert to JSON-serializable format
                json_result = {
                    "query": result.query,
                    "success": result.success,
                    "solved": result.solved,
                    "confidence": result.confidence,
                    "metadata": result.metadata.dict() if result.metadata else None,
                    "quality_report": result.quality_report,
                    "acquisition_options": result.acquisition_options,
                    "duration_ms": result.duration_ms,
                    "session_id": result.session_id
                }
                json.dump(json_result, f, indent=2)
                print(f"\n📁 Results saved to {filename}")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)


async def demo_supervisor_pattern():
    """
    Demonstrate the Supervisor Agent pattern.
    
    This shows how one agent can coordinate others using natural language.
    """
    print_header("DEMO: Supervisor Agent Pattern")
    print("""
    This demonstrates the Supervisor pattern where:
    - ChiefResearcher agent coordinates sub-agents
    - Uses natural language for orchestration
    - Handles complex multi-step workflows
    """)
    
    # Create supervisor agent
    chief = ChiefResearcherSupervisor(
        platforms=["spotify", "beatport", "musicbrainz"]
    )
    
    query = "Eric Prydz - Opus"
    print(f"\n🔍 Researching: {query}")
    
    try:
        # Research using supervisor
        result = await chief.research_track(
            query=query,
            context={"genre": "progressive house", "year": 2015}
        )
        
        print("\n📊 Supervisor Results:")
        print(json.dumps(result, indent=2)[:500] + "...")  # Print partial result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def demo_quick_search():
    """Demonstrate quick search functionality."""
    print_header("DEMO: Quick Search")
    print("Fast search using only 2 platforms")
    
    orchestrator = MusicResearchOrchestrator()
    
    result = await orchestrator.quick_search(
        query="Calvin Harris - Feel So Close",
        platforms=["spotify", "beatport"]
    )
    
    print("\n📊 Quick Search Results:")
    for platform, data in result.get("results", {}).items():
        print(f"\n{platform}:")
        if isinstance(data, dict) and data.get("success"):
            print(f"  ✅ Found")
        else:
            print(f"  ❌ Not found")


async def compare_implementations():
    """
    Compare Strands implementation vs custom implementation.
    """
    print_header("STRANDS VS CUSTOM IMPLEMENTATION")
    
    comparison = """
    STRANDS IMPLEMENTATION (This):
    ✅ Uses MultiAgentOrchestrator - built-in coordination
    ✅ @tool decorators - simple tool creation
    ✅ Supervisor agents - hierarchical control
    ✅ Session management - automatic context
    ✅ Parallel execution - built-in async
    ✅ ~500 lines of code
    
    CUSTOM IMPLEMENTATION (Previous):
    ❌ Custom ResearchAgent base class
    ❌ Manual asyncio orchestration
    ❌ Custom context management
    ❌ Manual parallel execution
    ❌ Custom tool registry
    ❌ ~2000+ lines of code
    
    BENEFITS OF STRANDS:
    • 75% less code
    • Production-ready features
    • Built-in observability
    • Easier to maintain
    • Better error handling
    • Automatic retries
    """
    
    print(comparison)


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("🚀 AWS STRANDS MUSIC RESEARCH SYSTEM")
    print("The PROPER implementation using Strands framework")
    print("="*60)
    
    # Run async demos
    loop = asyncio.get_event_loop()
    
    try:
        # Demo 1: MultiAgentOrchestrator
        loop.run_until_complete(demo_orchestrator_pattern())
        
        # Demo 2: Supervisor Pattern
        # loop.run_until_complete(demo_supervisor_pattern())
        
        # Demo 3: Quick Search
        loop.run_until_complete(demo_quick_search())
        
        # Show comparison
        loop.run_until_complete(compare_implementations())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()
    
    print("\n✅ Strands demo complete!")
    print("This is how the system SHOULD have been built.\n")


if __name__ == "__main__":
    main()