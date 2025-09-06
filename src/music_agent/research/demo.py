#!/usr/bin/env python3
"""
Demo script for the Multi-Agent Music Research System

Shows how the agents work together to research and resolve track metadata.
"""

import asyncio
import logging
from datetime import datetime
import json
from typing import Dict, Any

from core.research_context import ResearchContext
from agents import ChiefResearcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def research_track(query: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Research a track using the multi-agent system.
    
    Args:
        query: Track search query (e.g., "Artist - Title")
        config: Optional configuration
    
    Returns:
        Research results
    """
    print(f"\n{'='*60}")
    print(f"🎵 MUSIC RESEARCH SYSTEM DEMO")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    # Create research context
    context = ResearchContext(query=query)
    
    # Configure the chief researcher
    chief_config = config or {
        'max_retries': 3,
        'parallel_agents': 5,
        'timeout_per_agent': 30
    }
    
    # Create and run the chief researcher
    chief = ChiefResearcher(context=context, config=chief_config)
    
    print("🚀 Starting research workflow...\n")
    
    # Execute research
    start_time = datetime.utcnow()
    result = await chief.execute()
    end_time = datetime.utcnow()
    
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"📊 RESEARCH RESULTS")
    print(f"{'='*60}")
    
    if result['success']:
        print(f"✅ Research completed successfully in {duration:.1f}s")
        
        if result.get('metadata'):
            metadata = result['metadata']
            print(f"\n📀 Track Information:")
            print(f"  Title:  {metadata.title}")
            print(f"  Artist: {metadata.artist}")
            print(f"  Album:  {metadata.album or 'N/A'}")
            print(f"  BPM:    {metadata.bpm or 'N/A'}")
            print(f"  Key:    {metadata.key or 'N/A'}")
            print(f"  Genre:  {metadata.genre or 'N/A'}")
            print(f"  Label:  {metadata.label or 'N/A'}")
        
        if result.get('quality_report'):
            report = result['quality_report']
            print(f"\n📈 Quality Assessment:")
            print(f"  Completeness: {report.metadata_completeness:.1%}")
            print(f"  Confidence:   {report.confidence_score:.1%}")
            print(f"  Audio Quality: {report.audio_quality.value}")
            print(f"  Meets Requirements: {'✅' if report.meets_requirements else '❌'}")
            
            if report.missing_fields:
                print(f"  Missing Fields: {', '.join(report.missing_fields[:5])}")
        
        if result.get('acquisition_options'):
            print(f"\n💰 Acquisition Options: {len(result['acquisition_options'])} found")
            for i, option in enumerate(result['acquisition_options'][:3], 1):
                price_str = f"${option.price:.2f}" if option.price else "Free"
                print(f"  {i}. {option.source} ({option.type}) - {option.quality.value} - {price_str}")
        
        print(f"\n🎯 Track Status: {'SOLVED' if result.get('solved') else 'NOT SOLVED'}")
        if result.get('reason'):
            print(f"  Reason: {result['reason']}")
        
    else:
        print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
    
    # Show execution metrics
    print(f"\n📊 Execution Metrics:")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Platforms Searched: {len(context.platforms_searched)}")
    print(f"  API Calls: {context.total_api_calls}")
    print(f"  Cache Hits: {context.total_cache_hits}")
    print(f"  Active Agents: {len(context.active_agents)}")
    print(f"  Completed Agents: {len(context.completed_agents)}")
    
    # Show recommendations if any
    if context.recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(context.recommendations[:5], 1):
            print(f"  {i}. {rec}")
    
    print(f"\n{'='*60}\n")
    
    return result


async def demo_workflow():
    """Run demo workflow with multiple test cases."""
    
    test_queries = [
        # Electronic music (should prioritize Beatport)
        "deadmau5 - Strobe",
        
        # Popular track (should find on multiple platforms)
        "Daft Punk - One More Time",
        
        # Classical (should prioritize MusicBrainz/Discogs)
        "Bach - Goldberg Variations",
        
        # Underground/rare (should check SoundCloud, Soulseek)
        "Unknown Artist - Rare White Label Remix"
    ]
    
    for query in test_queries[:1]:  # Run just first query for demo
        try:
            result = await research_track(query)
            
            # Save result to file
            filename = f"research_result_{query.replace(' - ', '_').replace(' ', '_')}.json"
            with open(filename, 'w') as f:
                # Convert result to JSON-serializable format
                json_result = {
                    'query': query,
                    'success': result['success'],
                    'solved': result.get('solved', False),
                    'confidence': result.get('confidence', 0),
                    'reason': result.get('reason', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }
                json.dump(json_result, f, indent=2)
                print(f"📁 Result saved to {filename}")
            
        except Exception as e:
            logger.error(f"Demo failed for '{query}': {e}")
            import traceback
            traceback.print_exc()
        
        # Wait between queries to respect rate limits
        await asyncio.sleep(2)


async def test_parallel_search():
    """Test parallel platform searching."""
    print("\n" + "="*60)
    print("🔄 TESTING PARALLEL SEARCH")
    print("="*60)
    
    context = ResearchContext(query="Test Artist - Test Track")
    
    # Simulate parallel data collection
    from agents.data_collector import DataCollector
    
    platforms = ['spotify', 'beatport', 'discogs']
    collectors = []
    
    for platform in platforms:
        collector = DataCollector(
            platform=platform,
            context=context,
            config={'max_retries': 1, 'cache_enabled': False}
        )
        collectors.append(collector)
    
    print(f"Created {len(collectors)} data collectors")
    print("Starting parallel execution...")
    
    # Run all collectors in parallel
    tasks = [collector.execute() for collector in collectors]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\nResults:")
    for platform, result in zip(platforms, results):
        if isinstance(result, Exception):
            print(f"  {platform}: ❌ Failed - {result}")
        else:
            print(f"  {platform}: ✅ Success")
    
    print(f"\nPlatforms searched: {context.platforms_searched}")
    print("="*60)


async def test_metadata_merging():
    """Test metadata merging and conflict resolution."""
    print("\n" + "="*60)
    print("🔀 TESTING METADATA MERGING")
    print("="*60)
    
    from models import UniversalTrackMetadata
    from core.metadata_merger import MetadataMerger
    
    # Create sample metadata from different sources
    spotify_data = UniversalTrackMetadata(
        title="Test Track",
        artist="Test Artist",
        bpm=128.0,
        key="C min",
        energy=0.8,
        danceability=0.75
    )
    spotify_data.research_sources = ['spotify']
    
    beatport_data = UniversalTrackMetadata(
        title="Test Track",
        artist="Test Artist",
        bpm=128.5,  # Slightly different
        key="Cm",  # Different notation
        genre="Progressive House",
        label="Test Label"
    )
    beatport_data.research_sources = ['beatport']
    
    # Merge metadata
    merger = MetadataMerger()
    merged = merger.merge_multiple([spotify_data, beatport_data])
    
    print("Merged Metadata:")
    print(f"  Title: {merged.title}")
    print(f"  Artist: {merged.artist}")
    print(f"  BPM: {merged.bpm}")
    print(f"  Key: {merged.key}")
    print(f"  Genre: {merged.genre}")
    print(f"  Energy: {merged.energy}")
    print(f"  Sources: {merged.research_sources}")
    
    # Calculate confidence
    confidence = merger.calculate_merge_confidence([spotify_data, beatport_data])
    print(f"\nMerge Confidence: {confidence:.1%}")
    print("="*60)


def main():
    """Main entry point."""
    print("\n🎵 Multi-Agent Music Research System Demo\n")
    
    # Run async demo
    loop = asyncio.get_event_loop()
    
    try:
        # Run main workflow demo
        loop.run_until_complete(demo_workflow())
        
        # Run additional tests
        loop.run_until_complete(test_parallel_search())
        loop.run_until_complete(test_metadata_merging())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()
        print("\n✅ Demo completed\n")


if __name__ == "__main__":
    main()