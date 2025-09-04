#!/usr/bin/env python3
"""
Test 1001 Tracklists with Playwright integration.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.music_agent.integrations.tracklists_simple import TracklistsScraper
from bs4 import BeautifulSoup
import json

def test_playwright_integration():
    """Test that Playwright is working with 1001 Tracklists."""
    
    print("=" * 60)
    print("Testing 1001 Tracklists with Playwright")
    print("=" * 60)
    
    scraper = TracklistsScraper()
    
    # Test 1: Homepage
    print("\n1. Testing Homepage...")
    url = "https://www.1001tracklists.com/"
    html = scraper.fetch_page(url)
    
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if we got real content (not the JS warning)
        if "Please enable JavaScript" in html[:500]:
            print("❌ Still getting JavaScript warning - Playwright may not be working")
        else:
            print("✅ Successfully fetched with JavaScript rendered")
            
            # Look for track elements
            track_elements = soup.find_all(attrs={"data-trackid": True})
            if track_elements:
                print(f"✅ Found {len(track_elements)} tracks on homepage")
                
                # Show first track info
                first_track = track_elements[0]
                print(f"\nFirst track data-trackid: {first_track.get('data-trackid')}")
                print(f"First track text: {first_track.get_text(strip=True)[:100]}...")
            else:
                print("⚠️ No track elements found")
    else:
        print("❌ Failed to fetch homepage")
    
    # Test 2: Search
    print("\n2. Testing Search...")
    search_url = "https://www.1001tracklists.com/search?q=carl+cox"
    html = scraper.fetch_page(search_url)
    
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for search results
        links = soup.find_all('a', href=lambda x: x and '/tracklist/' in x)
        if links:
            print(f"✅ Found {len(links)} tracklist links in search results")
            
            # Show first few results
            for i, link in enumerate(links[:3], 1):
                print(f"   {i}. {link.get_text(strip=True)[:80]}...")
                print(f"      URL: {link.get('href')[:80]}...")
        else:
            print("⚠️ No tracklist links found in search")
            
            # Debug: Check what we got
            text = soup.get_text()[:500]
            print(f"Page text preview: {text}")
    else:
        print("❌ Failed to fetch search page")
    
    # Test 3: Try a specific tracklist (construct a likely valid URL)
    print("\n3. Testing Tracklist Page...")
    # Try to get a tracklist URL from the homepage
    tracklist_url = None
    
    if html:  # Use the last fetched HTML
        soup = BeautifulSoup(html, 'html.parser')
        tracklist_link = soup.find('a', href=lambda x: x and '/tracklist/' in x)
        if tracklist_link:
            href = tracklist_link.get('href')
            if href.startswith('http'):
                tracklist_url = href
            else:
                tracklist_url = f"https://www.1001tracklists.com{href}"
    
    if tracklist_url:
        print(f"Testing URL: {tracklist_url[:100]}...")
        html = scraper.fetch_page(tracklist_url)
        
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for track data
            track_elements = soup.find_all(class_=['tlpTog', 'tlpItem'])
            if track_elements:
                print(f"✅ Found {len(track_elements)} track elements")
            else:
                # Try data-trackid
                track_elements = soup.find_all(attrs={"data-trackid": True})
                if track_elements:
                    print(f"✅ Found {len(track_elements)} tracks with data-trackid")
                else:
                    print("⚠️ No track elements found on tracklist page")
                    
                    # Check page title to see if we loaded something
                    title = soup.find('title')
                    if title:
                        print(f"Page title: {title.get_text(strip=True)}")
        else:
            print("❌ Failed to fetch tracklist page")
    else:
        print("⚠️ Could not find a tracklist URL to test")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_playwright_integration()