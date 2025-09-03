#!/usr/bin/env python3
"""
Working Soulseek Test Script
Based on confirmed working API calls
"""

import time
import json
import requests
from typing import List, Dict, Any

# slskd API configuration
API_URL = "http://localhost:5030/api/v0"

def search_music(query: str, max_results: int = 100, timeout: int = 15000) -> Dict[str, Any]:
    """
    Search for music on Soulseek network
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        timeout: Search timeout in milliseconds
    
    Returns:
        Dictionary containing search results
    """
    print(f"\n🔍 Searching for: '{query}'")
    
    # Start the search
    search_data = {
        "searchText": query,
        "fileLimit": max_results,
        "filterResponses": True,
        "searchTimeout": timeout
    }
    
    response = requests.post(f"{API_URL}/searches", json=search_data)
    if response.status_code != 200:
        print(f"❌ Search failed: {response.text}")
        return {}
    
    search_result = response.json()
    search_id = search_result.get('id')
    print(f"📋 Search ID: {search_id}")
    
    # Wait for results
    print("⏳ Waiting for results...")
    max_wait = timeout // 1000 + 5  # Convert to seconds and add buffer
    
    for i in range(max_wait):
        time.sleep(1)
        
        # Check search status
        status_response = requests.get(f"{API_URL}/searches/{search_id}")
        if status_response.status_code == 200:
            status = status_response.json()
            response_count = status.get('responseCount', 0)
            file_count = status.get('fileCount', 0)
            is_complete = status.get('isComplete', False)
            
            print(f"  [{i+1}s] Responses: {response_count}, Files: {file_count}, Complete: {is_complete}")
            
            if response_count > 0 or is_complete:
                break
    
    # Get the actual responses
    responses_response = requests.get(f"{API_URL}/searches/{search_id}/responses")
    if responses_response.status_code != 200:
        print(f"❌ Failed to get responses: {responses_response.text}")
        return {}
    
    responses = responses_response.json()
    
    # Process results
    results = {
        'search_id': search_id,
        'total_responses': len(responses),
        'total_files': sum(len(r.get('files', [])) for r in responses),
        'results': []
    }
    
    for response in responses[:5]:  # Show first 5 users
        username = response.get('username', 'unknown')
        files = response.get('files', [])
        has_free_slot = response.get('hasFreeUploadSlot', False)
        
        if files:
            results['results'].append({
                'username': username,
                'has_free_slot': has_free_slot,
                'file_count': len(files),
                'sample_files': files[:3]  # First 3 files
            })
    
    # Clean up the search
    requests.delete(f"{API_URL}/searches/{search_id}")
    
    return results

def download_file(username: str, filename: str, size: int) -> bool:
    """
    Attempt to download a file from a user
    
    Args:
        username: Soulseek username
        filename: Full path to the file
        size: File size in bytes
    
    Returns:
        True if download was queued successfully
    """
    print(f"\n📥 Attempting to download from {username}:")
    print(f"   File: {filename}")
    print(f"   Size: {size / (1024*1024):.1f} MB")
    
    download_data = [{
        "filename": filename,
        "size": size
    }]
    
    response = requests.post(
        f"{API_URL}/transfers/downloads/{username}",
        json=download_data
    )
    
    if response.status_code == 200:
        print("✅ Download queued successfully!")
        return True
    else:
        error_msg = response.text
        print(f"❌ Download failed: {error_msg}")
        return False

def check_downloads() -> List[Dict[str, Any]]:
    """Check status of current downloads"""
    response = requests.get(f"{API_URL}/transfers/downloads")
    if response.status_code == 200:
        return response.json()
    return []

def main():
    """Run Soulseek functionality tests"""
    print("=" * 60)
    print("Soulseek Network Test")
    print("=" * 60)
    
    # Check server connection
    print("\n📡 Checking server connection...")
    server_response = requests.get(f"{API_URL}/server")
    if server_response.status_code == 200:
        server_status = server_response.json()
        print(f"✅ Connected: {server_status.get('isConnected', False)}")
        print(f"   State: {server_status.get('state', 'unknown')}")
        print(f"   Address: {server_status.get('address', 'unknown')}")
    else:
        print("❌ Server not connected")
        return
    
    # Test searches
    test_queries = [
        "Aphex Twin",
        "electronic ambient",
        "jazz fusion",
        "test"
    ]
    
    all_results = []
    for query in test_queries:
        results = search_music(query, max_results=50, timeout=10000)
        if results:
            all_results.append(results)
            print(f"\n✅ Found {results['total_files']} files from {results['total_responses']} users")
            
            # Show sample results
            for idx, result in enumerate(results['results'][:3], 1):
                print(f"\n  User {idx}: {result['username']}")
                print(f"    Free slot: {'✅' if result['has_free_slot'] else '❌'}")
                print(f"    Files: {result['file_count']}")
                
                for file in result['sample_files'][:2]:
                    filename = file.get('filename', '').split('\\')[-1]
                    size_mb = file.get('size', 0) / (1024*1024)
                    bitrate = file.get('bitRate', 'unknown')
                    print(f"      - {filename[:50]}")
                    print(f"        Size: {size_mb:.1f} MB, Bitrate: {bitrate}")
    
    # Try to download something if we found results with free slots
    print("\n" + "=" * 60)
    print("Download Test")
    print("=" * 60)
    
    for result_set in all_results:
        for result in result_set['results']:
            if result['has_free_slot'] and result['sample_files']:
                # Try to download the first file from a user with free slot
                file = result['sample_files'][0]
                success = download_file(
                    result['username'],
                    file['filename'],
                    file['size']
                )
                if success:
                    # Check download status
                    time.sleep(2)
                    downloads = check_downloads()
                    if downloads:
                        print("\n📊 Current downloads:")
                        for dl in downloads[:5]:
                            print(f"  - {dl.get('filename', 'unknown')}: {dl.get('state', 'unknown')}")
                    break
            if success:
                break
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()