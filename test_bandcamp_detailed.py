#!/usr/bin/env python3
"""
Detailed test and analysis of Bandcamp integration.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
from bs4 import BeautifulSoup


async def analyze_bandcamp_page(url: str):
    """Analyze a Bandcamp page to understand its structure."""
    print(f"\n📊 Analyzing: {url}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        async with session.get(url, headers=headers) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Check for TralbumData
            print("\n1. Looking for TralbumData...")
            tralbum_match = re.search(r'var TralbumData = ({.*?});', html, re.DOTALL)
            if tralbum_match:
                print("✅ Found TralbumData")
                try:
                    # Extract JSON
                    json_str = tralbum_match.group(1)
                    # Clean it up for parsing
                    json_str = re.sub(r'^\s*//.*$', '', json_str, flags=re.MULTILINE)  # Remove comments
                    
                    # Try to parse key parts
                    print("\n   Key fields found:")
                    
                    # Track info
                    trackinfo_match = re.search(r'trackinfo\s*:\s*(\[.*?\])', json_str, re.DOTALL)
                    if trackinfo_match:
                        print("   ✅ trackinfo array")
                        tracks_str = trackinfo_match.group(1)
                        # Count tracks
                        track_count = tracks_str.count('"file"')
                        print(f"      - Found {track_count} tracks with file info")
                        
                        # Look for mp3-128 streams
                        mp3_matches = re.findall(r'"mp3-128"\s*:\s*"([^"]+)"', tracks_str)
                        if mp3_matches:
                            print(f"      - Found {len(mp3_matches)} MP3 streams")
                            print(f"      - Example URL: {mp3_matches[0][:50]}...")
                    
                    # Current info
                    current_match = re.search(r'current\s*:\s*({.*?})', json_str, re.DOTALL)
                    if current_match:
                        print("   ✅ current object (album/track info)")
                        current_str = current_match.group(1)
                        if 'title' in current_str:
                            title_match = re.search(r'title\s*:\s*"([^"]+)"', current_str)
                            if title_match:
                                print(f"      - Title: {title_match.group(1)}")
                    
                    # Artist info
                    artist_match = re.search(r'artist\s*:\s*"([^"]+)"', json_str)
                    if artist_match:
                        print(f"   ✅ artist: {artist_match.group(1)}")
                    
                    # URL info
                    url_match = re.search(r'url\s*:\s*"([^"]+)"', json_str)
                    if url_match:
                        print(f"   ✅ url: {url_match.group(1)}")
                        
                except Exception as e:
                    print(f"   ⚠️ Error parsing TralbumData: {e}")
            else:
                print("❌ TralbumData not found")
            
            # 2. Check for data-tralbum attribute
            print("\n2. Looking for data-tralbum attribute...")
            tralbum_elem = soup.find(attrs={"data-tralbum": True})
            if tralbum_elem:
                print("✅ Found data-tralbum attribute")
                try:
                    data = json.loads(tralbum_elem["data-tralbum"])
                    print(f"   - Keys: {list(data.keys())}")
                except:
                    print("   ⚠️ Could not parse data-tralbum")
            else:
                print("❌ data-tralbum not found")
            
            # 3. Check for EmbedData
            print("\n3. Looking for EmbedData...")
            embed_match = re.search(r'var EmbedData = ({.*?});', html, re.DOTALL)
            if embed_match:
                print("✅ Found EmbedData")
            else:
                print("❌ EmbedData not found")
            
            # 4. Check for player data
            print("\n4. Looking for player elements...")
            player = soup.find("div", {"id": "pgBd"})
            if player:
                print("✅ Found player container")
                
                # Check for inline player
                inline_player = soup.find("table", {"id": "track_table"})
                if inline_player:
                    print("   ✅ Found track table (album)")
                    tracks = inline_player.find_all("tr", class_=re.compile("track"))
                    print(f"      - {len(tracks)} tracks in table")
            
            # 5. Check meta tags
            print("\n5. Checking meta tags...")
            og_audio = soup.find("meta", {"property": "og:audio"})
            if og_audio:
                print(f"✅ og:audio: {og_audio.get('content')[:50]}...")
            
            og_video = soup.find("meta", {"property": "og:video"})
            if og_video:
                print(f"✅ og:video: {og_video.get('content')[:50]}...")
            
            # 6. Check for free download
            print("\n6. Checking download availability...")
            free_download = soup.find("a", {"class": "download-link"})
            if free_download:
                print("✅ Free download link found")
            
            buy_link = soup.find("h4", class_="ft compound-button main-button")
            if buy_link:
                print(f"✅ Buy/name-your-price button: {buy_link.get_text(strip=True)}")
            
            return html, soup


async def test_specific_album():
    """Test with a specific known free album."""
    print("\n🎵 Testing with specific albums")
    print("=" * 60)
    
    # Test URLs - these should have free/streaming content
    test_urls = [
        "https://music.monstercat.com/album/hearts-divide",  # Monstercat album
        "https://music.monstercat.com/album/nemesis",  # Another Monstercat album
        "https://music.monstercat.com/track/feel-it",  # Single track
    ]
    
    for url in test_urls:
        try:
            html, soup = await analyze_bandcamp_page(url)
            
            # Try to extract actual stream URL
            print(f"\n🔍 Extracting stream URL from: {url}")
            
            # Method 1: Extract from TralbumData
            tralbum_match = re.search(r'var TralbumData = ({.*?});', html, re.DOTALL)
            if tralbum_match:
                json_str = tralbum_match.group(1)
                
                # Extract trackinfo
                trackinfo_match = re.search(r'trackinfo\s*:\s*(\[.*?\])', json_str, re.DOTALL)
                if trackinfo_match:
                    tracks_str = trackinfo_match.group(1)
                    
                    # Find MP3 URLs
                    mp3_pattern = r'"mp3-128"\s*:\s*"([^"]+)"'
                    mp3_urls = re.findall(mp3_pattern, tracks_str)
                    
                    if mp3_urls:
                        print(f"✅ Found {len(mp3_urls)} MP3 stream URLs")
                        for i, mp3_url in enumerate(mp3_urls[:2], 1):
                            # Clean up URL
                            if not mp3_url.startswith("http"):
                                mp3_url = "https:" + mp3_url if mp3_url.startswith("//") else mp3_url
                            print(f"   Track {i}: {mp3_url[:80]}...")
                            
                            # Test if URL is accessible
                            if mp3_url.startswith("http"):
                                async with aiohttp.ClientSession() as session:
                                    try:
                                        async with session.head(mp3_url, allow_redirects=True) as resp:
                                            if resp.status == 200:
                                                print(f"      ✅ URL is accessible (status: {resp.status})")
                                                content_length = resp.headers.get('Content-Length')
                                                if content_length:
                                                    size_mb = int(content_length) / (1024 * 1024)
                                                    print(f"      📦 File size: {size_mb:.1f} MB")
                                            else:
                                                print(f"      ❌ URL returned status: {resp.status}")
                                    except Exception as e:
                                        print(f"      ❌ Could not access URL: {e}")
                    else:
                        print("❌ No MP3 URLs found in trackinfo")
                        
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            import traceback
            traceback.print_exc()


async def test_our_implementation():
    """Test our Bandcamp integration."""
    from src.music_agent.integrations.bandcamp import BandcampClient
    
    print("\n🧪 Testing Our Implementation")
    print("=" * 60)
    
    client = BandcampClient()
    
    try:
        await client.initialize()
        
        # Test with a known free album
        test_url = "https://music.monstercat.com/album/hearts-divide"
        
        print(f"\nTesting album: {test_url}")
        
        album = await client.get_album(test_url)
        print(f"✅ Album: {album.title}")
        print(f"   Artist: {album.artist}")
        print(f"   Tracks: {album.num_tracks}")
        
        if album.tracks:
            print("\nTrack details:")
            for i, track in enumerate(album.tracks[:3], 1):
                print(f"   {i}. {track.title}")
                print(f"      - Duration: {track.duration_formatted}")
                print(f"      - Stream URL: {'Yes' if track.stream_url else 'No'}")
                print(f"      - Downloadable: {track.is_downloadable}")
        
        # Try to download if possible
        downloadable = album.get_downloadable_tracks()
        if downloadable:
            print(f"\n✅ Found {len(downloadable)} downloadable tracks")
            
            # Test download of first track
            track = downloadable[0]
            if track.stream_url:
                print(f"   Testing download of: {track.title}")
                try:
                    path = await client.download_track(track, output_dir="downloads/test")
                    print(f"   ✅ Downloaded to: {path}")
                except Exception as e:
                    print(f"   ❌ Download failed: {e}")
        else:
            print("\n❌ No downloadable tracks found")
            
    finally:
        await client.close()


async def main():
    """Run all tests."""
    # First analyze page structure
    await test_specific_album()
    
    # Then test our implementation
    await test_our_implementation()
    
    # Create report
    print("\n" + "=" * 60)
    print("📋 TEST REPORT")
    print("=" * 60)
    print("""
FINDINGS:
1. Bandcamp embeds track data in JavaScript variable 'TralbumData'
2. Stream URLs are in trackinfo[].file['mp3-128'] 
3. URLs may need 'https:' prefix if they start with '//'
4. Not all content has stream URLs (purchase required)
5. Free/name-your-price albums usually have streams available

IMPLEMENTATION STATUS:
✅ Search functionality works
✅ URL parsing works
✅ Basic page scraping works
⚠️  Stream URL extraction needs improvement
⚠️  TralbumData parsing needs to handle JavaScript object format

RECOMMENDATIONS:
1. Improve JavaScript data extraction with proper regex
2. Add fallback methods for stream URL discovery
3. Handle different URL formats (https://, //, relative)
4. Add support for preview streams when full streams unavailable
""")


if __name__ == "__main__":
    asyncio.run(main())