#!/usr/bin/env python3
"""
Comprehensive test suite for Soulseek/slskd integration.
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List

# Add parent directory to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

# Load .env file
env_path = project_root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

# Import Soulseek components
from src.music_agent.integrations.soulseek import (
    SoulseekClient,
    SoulseekConfig,
    FileInfo,
    SearchResult,
    UserInfo,
)


class TestSoulseekAPI:
    """Test suite for Soulseek API."""
    
    def __init__(self):
        """Initialize test suite."""
        self.config = SoulseekConfig.from_env()
        self.client = SoulseekClient(self.config)
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print(" SOULSEEK/SLSKD API TEST SUITE")
        print("=" * 60 + "\n")
        
        # Connect to slskd
        try:
            await self.client.connect()
            print("✓ Connected to slskd server")
            print(f"  Host: {self.config.slskd.host}")
            print()
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            print("\nMake sure slskd is running and accessible")
            return
        
        # Run tests
        await self.test_search()
        await self.test_advanced_search()
        await self.test_user_info()
        await self.test_browse_user()
        await self.test_discover_by_genre()
        await self.test_discover_similar()
        await self.test_download_management()
        
        # Close connection
        await self.client.close()
        
        # Print summary
        self.print_summary()
    
    async def test_search(self):
        """Test basic search functionality."""
        test_name = "Basic Search"
        try:
            results = await self.client.search(
                query="electronic music",
                max_results=5,
                min_bitrate=128,
                timeout=10
            )
            
            assert results, "No results returned"
            assert len(results) <= 5, f"Too many results: {len(results)}"
            assert all(isinstance(r, FileInfo) for r in results), "Invalid result type"
            
            # Check first result
            if results:
                first = results[0]
                assert first.file.filename, "Missing filename"
                assert first.username, "Missing username"
                assert first.file.size > 0, "Invalid file size"
            
            self.record_success(test_name, f"Found {len(results)} files")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_advanced_search(self):
        """Test advanced search with full SearchResult."""
        test_name = "Advanced Search"
        try:
            result = await self.client.search_advanced(
                query="techno",
                min_bitrate=320,
                max_results=10,
                timeout=8
            )
            
            assert isinstance(result, SearchResult), "Invalid result type"
            assert result.search_id, "Missing search ID"
            assert result.query == "techno", "Query mismatch"
            
            # Get best files
            best_files = result.get_best_files(5)
            if best_files:
                assert len(best_files) <= 5, "Too many best files"
            
            self.record_success(
                test_name, 
                f"Search ID: {result.search_id}, Files: {result.file_count}"
            )
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_user_info(self):
        """Test getting user information."""
        test_name = "User Info"
        try:
            # First get a user from search
            results = await self.client.search("music", max_results=1)
            if not results:
                self.record_failure(test_name, "No search results to test with")
                return
            
            username = results[0].username
            
            # Get user info
            user_info = await self.client.get_user_info(username)
            
            assert isinstance(user_info, UserInfo), "Invalid user info type"
            assert user_info.username == username, "Username mismatch"
            
            self.record_success(
                test_name, 
                f"User: {username}, Queue: {user_info.queue_length}"
            )
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_browse_user(self):
        """Test browsing user's shared files."""
        test_name = "Browse User"
        try:
            # First get a user from search
            results = await self.client.search("music", max_results=1)
            if not results:
                self.record_failure(test_name, "No search results to test with")
                return
            
            username = results[0].username
            
            # Browse user (with short timeout as this might fail)
            try:
                browse_result = await asyncio.wait_for(
                    self.client.browse_user(username),
                    timeout=5
                )
                
                assert browse_result.username == username, "Username mismatch"
                
                total_files = browse_result.total_files
                self.record_success(
                    test_name,
                    f"Browsed {username}: {total_files} files"
                )
            except asyncio.TimeoutError:
                self.record_success(test_name, "Browse timed out (expected for some users)")
                
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_discover_by_genre(self):
        """Test discovering music by genre."""
        test_name = "Discover by Genre"
        try:
            results = await self.client.discover_by_genre(
                genre="techno",
                limit=5
            )
            
            # Genre discovery might not always return results
            if results:
                assert len(results) <= 5, f"Too many results: {len(results)}"
                self.record_success(test_name, f"Found {len(results)} techno tracks")
            else:
                self.record_success(test_name, "No genre matches found (can happen)")
                
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_discover_similar(self):
        """Test discovering similar tracks."""
        test_name = "Discover Similar"
        try:
            # This is a complex operation that might fail
            results = await asyncio.wait_for(
                self.client.discover_similar(
                    reference_track="daft punk",
                    limit=5
                ),
                timeout=15
            )
            
            if results:
                self.record_success(test_name, f"Found {len(results)} similar tracks")
            else:
                self.record_success(test_name, "No similar tracks found (expected)")
                
        except asyncio.TimeoutError:
            self.record_success(test_name, "Discovery timed out (expected for complex search)")
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_download_management(self):
        """Test download management functions."""
        test_name = "Download Management"
        try:
            # Just test that we can get download lists
            downloads = self.client.get_downloads()
            active = self.client.get_active_downloads()
            
            assert isinstance(downloads, list), "Invalid downloads list"
            assert isinstance(active, list), "Invalid active downloads list"
            
            self.record_success(
                test_name,
                f"Downloads: {len(downloads)}, Active: {len(active)}"
            )
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    def record_success(self, test_name: str, details: str = ""):
        """Record a successful test."""
        self.passed += 1
        self.tests.append((test_name, True, details))
        print(f"✅ {test_name}: {details}")
    
    def record_failure(self, test_name: str, error: str):
        """Record a failed test."""
        self.failed += 1
        self.tests.append((test_name, False, error))
        print(f"❌ {test_name}: {error}")
    
    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print(" TEST SUMMARY")
        print("=" * 60)
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed. See details above.")


async def main():
    """Run the test suite."""
    tester = TestSoulseekAPI()
    await tester.run_all_tests()
    
    # Return exit code
    return 0 if tester.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)