#!/usr/bin/env python3
"""
Debug script to inspect 1001 Tracklists HTML structure.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.tracklists_simple import TracklistsScraper
from bs4 import BeautifulSoup
import json

def debug_page_structure():
    """Debug what HTML we're actually getting from 1001 Tracklists."""
    
    scraper = TracklistsScraper()
    
    # Test URLs
    test_urls = [
        "https://www.1001tracklists.com/",  # Homepage
        "https://www.1001tracklists.com/tracklist/2p9mk1ht/amelie-lens-awakenings-festival-2023-07-01.html",
        "https://www.1001tracklists.com/search?q=carl+cox"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Debugging: {url}")
        print(f"{'='*60}")
        
        html = scraper.fetch_page(url)
        
        if not html:
            print("❌ Failed to fetch page")
            continue
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check page title
        title = soup.find('title')
        print(f"Page Title: {title.get_text(strip=True) if title else 'No title found'}")
        
        # Check for common error patterns
        if '404' in html[:1000] or 'not found' in html[:1000].lower():
            print("⚠️ Page may be 404")
        
        # Check for captcha/cloudflare
        if 'cloudflare' in html.lower()[:2000] or 'captcha' in html.lower()[:2000]:
            print("⚠️ Cloudflare/Captcha detected")
        
        # Look for track-related elements
        print("\n🔍 Looking for track elements...")
        
        # Strategy 1: Common class names for tracks
        track_classes = ['tlpTog', 'tlpItem', 'track', 'tracklist', 'playlist-track', 'track-item']
        for class_name in track_classes:
            elements = soup.find_all(class_=class_name)
            if elements:
                print(f"  Found {len(elements)} elements with class '{class_name}'")
                # Show first element structure
                if elements:
                    first = elements[0]
                    print(f"    First element HTML (truncated):")
                    html_str = str(first)[:300]
                    print(f"    {html_str}...")
        
        # Strategy 2: Look for data attributes
        print("\n🔍 Looking for data attributes...")
        data_elements = soup.find_all(attrs={"data-track": True})
        if data_elements:
            print(f"  Found {len(data_elements)} elements with data-track")
        
        data_elements = soup.find_all(attrs={"data-trackid": True})
        if data_elements:
            print(f"  Found {len(data_elements)} elements with data-trackid")
        
        # Strategy 3: Look for specific divs/spans
        print("\n🔍 Looking for div/span patterns...")
        
        # Find all divs with IDs or classes that might contain tracks
        track_containers = soup.find_all(['div', 'span', 'tr'], id=lambda x: x and 'track' in x.lower() if x else False)
        if track_containers:
            print(f"  Found {len(track_containers)} containers with 'track' in ID")
        
        # Look for artist - title patterns in text
        import re
        text_content = soup.get_text()
        track_patterns = re.findall(r'^\d+\.\s+[A-Za-z].+?\s+-\s+.+$', text_content, re.MULTILINE)
        if track_patterns:
            print(f"\n  Found {len(track_patterns)} potential track patterns in text:")
            for i, pattern in enumerate(track_patterns[:3]):
                print(f"    {i+1}. {pattern[:80]}...")
        
        # Check for JavaScript-rendered content
        scripts = soup.find_all('script')
        has_react = any('react' in str(s).lower() for s in scripts)
        has_vue = any('vue' in str(s).lower() for s in scripts)
        has_angular = any('angular' in str(s).lower() for s in scripts)
        
        if has_react or has_vue or has_angular:
            print(f"\n⚠️ Page appears to use client-side rendering:")
            if has_react: print("  - React detected")
            if has_vue: print("  - Vue detected")
            if has_angular: print("  - Angular detected")
            print("  This may require selenium or similar for full content")
        
        # Look for API endpoints in scripts
        print("\n🔍 Looking for API endpoints...")
        for script in scripts:
            script_text = str(script)
            if '/api/' in script_text or 'fetch(' in script_text or 'ajax' in script_text.lower():
                # Extract potential API URLs
                api_matches = re.findall(r'["\'](/api/[^"\']+)["\']', script_text)
                if api_matches:
                    print(f"  Found potential API endpoints:")
                    for endpoint in api_matches[:5]:
                        print(f"    {endpoint}")
        
        # Save sample HTML for inspection
        if 'tracklist' in url:
            output_file = Path("tracklist_sample.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n📄 Full HTML saved to: {output_file}")
            
            # Also save just the body content
            body = soup.find('body')
            if body:
                body_text = body.get_text(' ', strip=True)
                text_file = Path("tracklist_body_text.txt")
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(body_text)
                print(f"📄 Body text saved to: {text_file}")

if __name__ == "__main__":
    debug_page_structure()