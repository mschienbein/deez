#!/usr/bin/env python3
"""
Query and explore synced music data from Neo4j and PostgreSQL
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.graphiti_memory import MusicMemory
import asyncpg
from neo4j import AsyncGraphDatabase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


class MusicDataExplorer:
    """Explore synced music data"""
    
    def __init__(self):
        self.postgres_conn = None
        self.neo4j_driver = None
        self.memory = MusicMemory()
        
    async def initialize(self):
        """Initialize connections"""
        # PostgreSQL
        self.postgres_conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "music_agent"),
            password=os.getenv("POSTGRES_PASSWORD", "music123"),
            database=os.getenv("POSTGRES_DB", "music_catalog")
        )
        
        # Neo4j
        self.neo4j_driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USERNAME", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "deezmusic123")
            )
        )
        
        # Graphiti memory
        await self.memory.initialize(session_id="query_session")
        
        console.print("[green]✅ All connections initialized[/green]")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get overview statistics"""
        stats = {}
        
        # PostgreSQL stats
        pg_query = """
        SELECT 
            (SELECT COUNT(*) FROM music.tracks) as track_count,
            (SELECT COUNT(DISTINCT artist_id) FROM music.tracks WHERE artist_id IS NOT NULL) as artist_count,
            (SELECT COUNT(DISTINCT album_id) FROM music.tracks WHERE album_id IS NOT NULL) as album_count,
            (SELECT AVG(bpm) FROM music.tracks WHERE bpm IS NOT NULL) as avg_bpm,
            (SELECT AVG(rating) FROM music.tracks WHERE rating IS NOT NULL) as avg_rating
        """
        
        result = await self.postgres_conn.fetchrow(pg_query)
        stats['postgres'] = dict(result) if result else {}
        
        # Neo4j stats
        neo4j_query = """
        MATCH (n)
        WITH labels(n) as node_labels
        UNWIND node_labels as label
        WITH label, COUNT(*) as count
        RETURN collect({label: label, count: count}) as label_counts
        """
        
        async with self.neo4j_driver.session(database=os.getenv("NEO4J_DATABASE", "music")) as session:
            result = await session.run(neo4j_query)
            record = await result.single()
            stats['neo4j'] = {
                'node_types': record['label_counts'] if record else []
            }
            
            # Get relationship counts
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship, COUNT(*) as count
            ORDER BY count DESC
            """
            result = await session.run(rel_query)
            relationships = []
            async for record in result:
                relationships.append({
                    'type': record['relationship'],
                    'count': record['count']
                })
            stats['neo4j']['relationships'] = relationships
        
        return stats
    
    async def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tracks in PostgreSQL"""
        
        search_query = """
        SELECT 
            id, title, artist_id, album_id, bpm, key, rating,
            color, duration_ms, play_count, file_path
        FROM music.tracks
        WHERE 
            title ILIKE $1 OR
            comment ILIKE $1
        ORDER BY play_count DESC NULLS LAST
        LIMIT $2
        """
        
        results = await self.postgres_conn.fetch(
            search_query,
            f"%{query}%",
            limit
        )
        
        return [dict(r) for r in results]
    
    async def get_tracks_by_bpm(self, min_bpm: float, max_bpm: float, limit: int = 20) -> List[Dict[str, Any]]:
        """Get tracks within BPM range"""
        
        query = """
        SELECT 
            title, bpm, key, rating, play_count
        FROM music.tracks
        WHERE bpm BETWEEN $1 AND $2
        ORDER BY rating DESC NULLS LAST, play_count DESC NULLS LAST
        LIMIT $3
        """
        
        results = await self.postgres_conn.fetch(query, min_bpm, max_bpm, limit)
        return [dict(r) for r in results]
    
    async def get_tracks_by_key(self, key: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get tracks in a specific key"""
        
        query = """
        SELECT 
            title, artist_id, bpm, key, rating, play_count
        FROM music.tracks
        WHERE key = $1
        ORDER BY rating DESC NULLS LAST, play_count DESC NULLS LAST
        LIMIT $2
        """
        
        results = await self.postgres_conn.fetch(query, key, limit)
        return [dict(r) for r in results]
    
    async def get_memory_insights(self) -> Dict[str, Any]:
        """Get insights from Graphiti memory"""
        
        # Search for recent activity
        recent = await self.memory.search_memory("track discovery rekordbox", limit=10)
        
        # Get preferences
        preferences = await self.memory.get_user_preferences()
        
        # Analyze patterns
        patterns = await self.memory.analyze_listening_patterns("week")
        
        return {
            "recent_discoveries": len(recent),
            "preferences": preferences[:5],
            "patterns": patterns
        }
    
    async def display_results(self):
        """Display exploration results"""
        
        # Get stats
        console.print("\n[bold cyan]📊 Database Statistics[/bold cyan]")
        stats = await self.get_stats()
        
        # PostgreSQL stats table
        pg_table = Table(title="PostgreSQL Music Catalog")
        pg_table.add_column("Metric", style="cyan")
        pg_table.add_column("Value", style="green")
        
        for key, value in stats['postgres'].items():
            if isinstance(value, float):
                value = f"{value:.2f}"
            pg_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(pg_table)
        
        # Neo4j stats
        if stats['neo4j']['node_types']:
            neo_table = Table(title="Neo4j Graph Database")
            neo_table.add_column("Node Type", style="cyan")
            neo_table.add_column("Count", style="green")
            
            for node in stats['neo4j']['node_types']:
                neo_table.add_row(node['label'], str(node['count']))
            
            console.print(neo_table)
        
        # Sample tracks by BPM
        console.print("\n[bold cyan]🎵 Sample Tracks (126-130 BPM)[/bold cyan]")
        tracks = await self.get_tracks_by_bpm(126, 130, 5)
        
        if tracks:
            track_table = Table()
            track_table.add_column("Title", style="yellow")
            track_table.add_column("BPM", style="cyan")
            track_table.add_column("Key", style="magenta")
            track_table.add_column("Rating", style="green")
            
            for track in tracks:
                track_table.add_row(
                    track['title'][:40],
                    f"{track['bpm']:.1f}" if track['bpm'] else "N/A",
                    track['key'] or "N/A",
                    str(track['rating']) if track['rating'] else "N/A"
                )
            
            console.print(track_table)
        
        # Memory insights
        console.print("\n[bold cyan]🧠 Graphiti Memory Insights[/bold cyan]")
        insights = await self.get_memory_insights()
        
        insight_panel = Panel(
            f"Recent Discoveries: {insights['recent_discoveries']}\n"
            f"Preferences Stored: {len(insights['preferences'])}\n"
            f"Patterns: {json.dumps(insights['patterns'], indent=2) if insights['patterns'] else 'No patterns yet'}",
            title="Memory System",
            border_style="cyan"
        )
        console.print(insight_panel)
    
    async def close(self):
        """Close connections"""
        if self.postgres_conn:
            await self.postgres_conn.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        await self.memory.close()


async def main():
    """Main query function"""
    
    # Ensure OpenAI API key is set from environment
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]❌ OPENAI_API_KEY environment variable not set![/red]")
        console.print("[yellow]Please set your OpenAI API key in .env file[/yellow]")
        return
    
    explorer = MusicDataExplorer()
    
    try:
        await explorer.initialize()
        await explorer.display_results()
        
        console.print("\n[bold green]✅ Music data exploration complete![/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await explorer.close()


if __name__ == "__main__":
    asyncio.run(main())