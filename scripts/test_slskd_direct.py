#!/usr/bin/env python3
"""
Direct slskd API Test
Tests the slskd API endpoints directly using curl
"""

import subprocess
import json
import time
import sys

def run_curl(endpoint, method="GET", data=None):
    """Run curl command and return JSON response"""
    cmd = [
        "curl", "-s",
        "-X", method,
        f"http://localhost:5030/api/v0/{endpoint}"
    ]
    
    if data:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            return json.loads(result.stdout)
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse response: {result.stdout}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_server_status():
    """Test server connection status"""
    print("\n" + "=" * 60)
    print("Testing Server Status")
    print("=" * 60)
    
    state = run_curl("server")
    if state:
        print(f"\nServer State:")
        print(f"  Connected: {state.get('isConnected', False)}")
        print(f"  Username: {state.get('username', 'not logged in')}")
        print(f"  Address: {state.get('address', 'unknown')}")
        print(f"  State: {state.get('state', 'unknown')}")
        return True
    else:
        print("Failed to get server state")
        return False

def test_search():
    """Test search functionality"""
    print("\n" + "=" * 60)
    print("Testing Search")
    print("=" * 60)
    
    # Start a search
    search_data = {
        "searchText": "Beatles",
        "fileLimit": 100,
        "filterResponses": True,
        "searchTimeout": 15000
    }
    
    print("\nStarting search for 'Beatles'...")
    search_result = run_curl("searches", "POST", search_data)
    
    if not search_result:
        print("Failed to start search")
        return False
    
    search_id = search_result.get('id')
    print(f"Search ID: {search_id}")
    
    # Wait for results
    print("Waiting for results...")
    for i in range(15):
        time.sleep(1)
        
        # Get search state
        state = run_curl(f"searches/{search_id}")
        if state:
            response_count = state.get('responseCount', 0)
            file_count = state.get('fileCount', 0)
            is_complete = state.get('isComplete', False)
            
            print(f"  [{i+1}s] Responses: {response_count}, Files: {file_count}, Complete: {is_complete}")
            
            if response_count > 0:
                # Get actual responses
                responses = run_curl(f"searches/{search_id}/responses")
                if responses and len(responses) > 0:
                    print(f"\nFound {len(responses)} responses")
                    
                    # Show first few results
                    for idx, response in enumerate(responses[:3]):
                        username = response.get('username', 'unknown')
                        files = response.get('files', [])
                        print(f"\nUser {idx+1}: {username}")
                        print(f"  Files: {len(files)}")
                        
                        for file in files[:2]:
                            filename = file.get('filename', '')
                            size_mb = file.get('size', 0) / (1024*1024)
                            bitrate = file.get('bitRate', 'unknown')
                            print(f"    - {filename.split('/')[-1]}")
                            print(f"      Size: {size_mb:.1f} MB, Bitrate: {bitrate}")
                
                # Stop the search
                run_curl(f"searches/{search_id}", "DELETE")
                return True
    
    # Stop the search if no results
    run_curl(f"searches/{search_id}", "DELETE")
    print("No results found")
    return False

def test_rooms():
    """Test room listing"""
    print("\n" + "=" * 60)
    print("Testing Rooms")
    print("=" * 60)
    
    rooms = run_curl("rooms")
    if rooms:
        print(f"Found {len(rooms)} rooms")
        for room in rooms[:5]:
            name = room.get('name', '')
            users = room.get('users', 0)
            print(f"  - {name}: {users} users")
        return True
    else:
        print("Failed to get rooms")
        return False

def test_transfers():
    """Test transfer listing"""
    print("\n" + "=" * 60)
    print("Testing Transfers")
    print("=" * 60)
    
    downloads = run_curl("transfers/downloads")
    uploads = run_curl("transfers/uploads")
    
    if downloads is not None:
        print(f"Downloads: {len(downloads)}")
    else:
        print("Failed to get downloads")
    
    if uploads is not None:
        print(f"Uploads: {len(uploads)}")
    else:
        print("Failed to get uploads")
    
    return downloads is not None or uploads is not None

def main():
    """Run all tests"""
    print("=" * 60)
    print("Direct slskd API Test")
    print("=" * 60)
    
    tests = [
        ("Server Status", test_server_status),
        ("Search", test_search),
        ("Rooms", test_rooms),
        ("Transfers", test_transfers),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("⚠️ Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())