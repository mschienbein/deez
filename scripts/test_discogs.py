#!/usr/bin/env python3
"""
Test script for Discogs API integration.
Tests all major endpoints and features.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.discogs import DiscogsIntegration, SearchFilters, SearchType
from src.music_agent.tools import discogs_tools

console = Console()


def test_database_search():
    """Test database search functionality."""
    console.print("\n[bold cyan]Testing Database Search[/bold cyan]")
    console.print("=" * 60)
    
    # Test basic search
    results = discogs_tools.discogs_search(
        query="Daft Punk Discovery",
        search_type="release",
        per_page=5
    )
    
    if results.get('results'):
        console.print(f"✅ Found {len(results['results'])} results")
        
        # Display results in a table
        table = Table(title="Search Results")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Year", style="magenta")
        
        for item in results['results'][:5]:
            table.add_row(
                str(item.get('id', '')),
                item.get('title', '')[:50],
                item.get('type', ''),
                str(item.get('year', ''))
            )
        
        console.print(table)
        return results['results'][0]['id'] if results['results'] else None
    else:
        console.print("❌ No results found")
        return None


def test_release_details(release_id):
    """Test getting release details."""
    console.print("\n[bold cyan]Testing Release Details[/bold cyan]")
    console.print("=" * 60)
    
    if not release_id:
        console.print("⚠️ No release ID available, skipping")
        return
    
    release = discogs_tools.discogs_get_release(release_id)
    
    if not release.get('error'):
        console.print(f"✅ Retrieved release: {release.get('title')}")
        
        # Display release info
        info = Panel(
            f"""[bold]Title:[/bold] {release.get('title')}
[bold]Artists:[/bold] {', '.join([a['name'] for a in release.get('artists', [])])}
[bold]Year:[/bold] {release.get('year')}
[bold]Genres:[/bold] {', '.join(release.get('genres', []))}
[bold]Styles:[/bold] {', '.join(release.get('styles', []))}
[bold]Tracklist:[/bold] {len(release.get('tracklist', []))} tracks
[bold]Format:[/bold] {', '.join([f['name'] for f in release.get('formats', [])])}
[bold]Community Have:[/bold] {release.get('community', {}).get('have', 0)}
[bold]Community Want:[/bold] {release.get('community', {}).get('want', 0)}
[bold]For Sale:[/bold] {release.get('marketplace', {}).get('num_for_sale', 0)}
[bold]Lowest Price:[/bold] ${release.get('marketplace', {}).get('lowest_price', 'N/A')}""",
            title="Release Information",
            border_style="green"
        )
        console.print(info)
    else:
        console.print(f"❌ Error: {release.get('error')}")


def test_artist_search():
    """Test artist search and details."""
    console.print("\n[bold cyan]Testing Artist Search[/bold cyan]")
    console.print("=" * 60)
    
    results = discogs_tools.discogs_search(
        query="Aphex Twin",
        search_type="artist",
        per_page=3
    )
    
    if results.get('results'):
        console.print(f"✅ Found {len(results['results'])} artists")
        
        # Get details for first artist
        artist_id = results['results'][0]['id']
        artist = discogs_tools.discogs_get_artist(artist_id)
        
        if not artist.get('error'):
            info = Panel(
                f"""[bold]Name:[/bold] {artist.get('name')}
[bold]Real Name:[/bold] {artist.get('real_name', 'N/A')}
[bold]Profile:[/bold] {(artist.get('profile', '')[:200] + '...' if len(artist.get('profile', '')) > 200 else artist.get('profile', ''))}
[bold]URLs:[/bold] {len(artist.get('urls', []))} links
[bold]Name Variations:[/bold] {', '.join(artist.get('namevariations', [])[:5])}""",
                title="Artist Information",
                border_style="yellow"
            )
            console.print(info)
    else:
        console.print("❌ No artists found")


def test_label_search():
    """Test label search and details."""
    console.print("\n[bold cyan]Testing Label Search[/bold cyan]")
    console.print("=" * 60)
    
    results = discogs_tools.discogs_search(
        query="Warp Records",
        search_type="label",
        per_page=3
    )
    
    if results.get('results'):
        console.print(f"✅ Found {len(results['results'])} labels")
        
        # Get details for first label
        label_id = results['results'][0]['id']
        label = discogs_tools.discogs_get_label(label_id)
        
        if not label.get('error'):
            info = Panel(
                f"""[bold]Name:[/bold] {label.get('name')}
[bold]Profile:[/bold] {(label.get('profile', '')[:200] + '...' if len(label.get('profile', '')) > 200 else label.get('profile', ''))}
[bold]Contact:[/bold] {label.get('contact_info', 'N/A')}
[bold]Parent Label:[/bold] {label.get('parent_label', {}).get('name') if label.get('parent_label') else 'None'}
[bold]Sublabels:[/bold] {len(label.get('sublabels', []))} sublabels""",
                title="Label Information",
                border_style="magenta"
            )
            console.print(info)
    else:
        console.print("❌ No labels found")


def test_advanced_search():
    """Test advanced search with filters."""
    console.print("\n[bold cyan]Testing Advanced Search with Filters[/bold cyan]")
    console.print("=" * 60)
    
    # Search for electronic music from the 90s on vinyl
    results = discogs_tools.discogs_search(
        query="",
        search_type="release",
        genre="Electronic",
        style="Ambient",
        year="1990-1999",
        format="Vinyl",
        per_page=5
    )
    
    if results.get('results'):
        console.print(f"✅ Found {results['pagination']['items']} total results")
        
        table = Table(title="Filtered Search Results (90s Electronic Ambient Vinyl)")
        table.add_column("Title", style="green")
        table.add_column("Artist", style="cyan")
        table.add_column("Year", style="yellow")
        table.add_column("Label", style="magenta")
        
        for item in results['results']:
            table.add_row(
                item.get('title', '')[:40],
                item.get('artist', '')[:30] if 'artist' in item else 'Various',
                str(item.get('year', '')),
                item.get('label', '')[:20] if 'label' in item else ''
            )
        
        console.print(table)
    else:
        console.print("❌ No results found with filters")


def test_marketplace_search():
    """Test marketplace functionality."""
    console.print("\n[bold cyan]Testing Marketplace Search[/bold cyan]")
    console.print("=" * 60)
    
    # Search for a popular release and check marketplace
    results = discogs_tools.discogs_find_in_marketplace(
        query="Pink Floyd Dark Side of the Moon",
        max_price=50.0,
        min_condition="Very Good (VG)"
    )
    
    if results.get('results'):
        console.print(f"✅ Found {len(results['results'])} marketplace results")
        
        for item in results['results'][:3]:
            release = item['release']
            marketplace = item.get('marketplace', {})
            
            info = Panel(
                f"""[bold]Title:[/bold] {release.get('title')}
[bold]For Sale:[/bold] {marketplace.get('num_for_sale', 0)} copies
[bold]Lowest Price:[/bold] ${marketplace.get('lowest_price', 'N/A')}
[bold]Meets Price Criteria:[/bold] {'✅' if item.get('meets_price_criteria') else '❌'}""",
                title=f"Marketplace Result #{results['results'].index(item) + 1}",
                border_style="blue"
            )
            console.print(info)
    else:
        console.print("❌ No marketplace results found")


def test_user_functions():
    """Test user-related functions (requires authentication)."""
    console.print("\n[bold cyan]Testing User Functions[/bold cyan]")
    console.print("=" * 60)
    
    try:
        # Try to get user identity (requires authentication)
        identity = discogs_tools.discogs_get_identity()
        
        if not identity.get('error'):
            console.print(f"✅ Authenticated as: {identity.get('username')}")
            
            # Test collection functions
            folders = discogs_tools.discogs_get_collection_folders()
            console.print(f"✅ Found {len(folders)} collection folders")
            
            # Test wantlist
            wantlist = discogs_tools.discogs_get_wantlist(per_page=5)
            console.print(f"✅ Wantlist has {wantlist.get('pagination', {}).get('items', 0)} items")
        else:
            console.print("⚠️ Not authenticated - skipping user functions")
            console.print("   To enable: Add a Discogs personal access token to DISCOGS_USER_TOKEN in .env")
    except Exception as e:
        console.print(f"⚠️ User functions not available: {e}")


def main():
    """Run all Discogs API tests."""
    console.print("\n[bold green]🎵 Discogs API Integration Test Suite[/bold green]")
    console.print("=" * 60)
    
    try:
        # Test database search
        release_id = test_database_search()
        
        # Test release details
        if release_id:
            test_release_details(release_id)
        
        # Test artist search
        test_artist_search()
        
        # Test label search
        test_label_search()
        
        # Test advanced search
        test_advanced_search()
        
        # Test marketplace
        test_marketplace_search()
        
        # Test user functions (if authenticated)
        test_user_functions()
        
        console.print("\n[bold green]✅ All tests completed![/bold green]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed with error: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()