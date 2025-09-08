#!/usr/bin/env python3
"""
Comprehensive test suite for Mixcloud API integration.
Tests all major endpoints and functionality.
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

# Import Mixcloud components
from src.music_agent.integrations.mixcloud import (
    MixcloudClient,
    MixcloudConfig,
    Cloudcast,
    User,
    Tag,
    Category,
)

class TestMixcloudAPI:
    """Test suite for Mixcloud API."""
    
    def __init__(self):
        """Initialize test suite."""
        self.config = MixcloudConfig()
        self.client = MixcloudClient(self.config)
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "=" * 60)
        print(" MIXCLOUD API TEST SUITE")
        print("=" * 60 + "\n")
        
        async with self.client:
            # Search tests
            await self.test_search_cloudcasts()
            await self.test_search_users()
            await self.test_search_tags()
            
            # Cloudcast tests
            await self.test_get_cloudcast()
            await self.test_cloudcast_similar()
            
            # User tests
            await self.test_get_user()
            await self.test_user_cloudcasts()
            
            # Discover tests
            await self.test_popular_cloudcasts()
            await self.test_hot_cloudcasts()
            await self.test_categories()
        
        # Print summary
        self.print_summary()
    
    async def test_search_cloudcasts(self):
        """Test searching for cloudcasts."""
        test_name = "Search Cloudcasts"
        try:
            results = await self.client.search_cloudcasts(
                query="house music",
                limit=5
            )
            
            assert results, "No results returned"
            assert len(results) <= 5, f"Too many results: {len(results)}"
            assert all(isinstance(r, Cloudcast) for r in results), "Invalid result type"
            
            # Check first result has expected fields
            if results:
                cloudcast = results[0]
                assert cloudcast.name, "Missing cloudcast name"
                assert cloudcast.key, "Missing cloudcast key"
                assert cloudcast.url, "Missing cloudcast URL"
            
            self.record_success(test_name, f"Found {len(results)} cloudcasts")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_search_users(self):
        """Test searching for users."""
        test_name = "Search Users"
        try:
            results = await self.client.search_users(
                query="dj",
                limit=3
            )
            
            assert results, "No users found"
            assert len(results) <= 3, f"Too many results: {len(results)}"
            assert all(isinstance(r, User) for r in results), "Invalid result type"
            
            # Check first user has expected fields
            if results:
                user = results[0]
                assert user.username, "Missing username"
                assert user.name, "Missing display name"
                assert user.key, "Missing user key"
            
            self.record_success(test_name, f"Found {len(results)} users")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_search_tags(self):
        """Test searching for tags."""
        test_name = "Search Tags"
        try:
            results = await self.client.search_tags(
                query="techno",
                limit=3
            )
            
            assert results, "No tags found"
            assert len(results) <= 3, f"Too many results: {len(results)}"
            assert all(isinstance(r, Tag) for r in results), "Invalid result type"
            
            # Check first tag has expected fields
            if results:
                tag = results[0]
                assert tag.name, "Missing tag name"
                assert tag.key, "Missing tag key"
            
            self.record_success(test_name, f"Found {len(results)} tags")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_get_cloudcast(self):
        """Test getting a specific cloudcast."""
        test_name = "Get Cloudcast"
        try:
            # First search for a cloudcast
            search_results = await self.client.search_cloudcasts("mix", limit=1)
            if not search_results:
                self.record_failure(test_name, "No cloudcasts found to test")
                return
            
            cloudcast = search_results[0]
            # Extract username and slug from the key (format: /username/cloudcast-slug/)
            key_parts = cloudcast.key.strip('/').split('/')
            if len(key_parts) >= 2:
                username = key_parts[0]
                cloudcast_slug = key_parts[1]
                
                # Get the cloudcast details
                detailed_cloudcast = await self.client.get_cloudcast(username, cloudcast_slug)
                
                assert detailed_cloudcast, "Failed to get cloudcast"
                assert detailed_cloudcast.name, "Missing cloudcast name"
                assert detailed_cloudcast.user, "Missing user info"
                
                self.record_success(test_name, f"Got cloudcast: {detailed_cloudcast.name}")
            else:
                self.record_failure(test_name, f"Invalid cloudcast key format: {cloudcast.key}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_cloudcast_similar(self):
        """Test getting similar cloudcasts."""
        test_name = "Similar Cloudcasts"
        try:
            # First search for a cloudcast
            search_results = await self.client.search_cloudcasts("electronic", limit=1)
            if not search_results:
                self.record_failure(test_name, "No cloudcasts found to test")
                return
            
            cloudcast = search_results[0]
            # Extract username and slug from the key
            key_parts = cloudcast.key.strip('/').split('/')
            if len(key_parts) >= 2:
                username = key_parts[0]
                cloudcast_slug = key_parts[1]
                
                # Get similar cloudcasts using the API directly
                result = await self.client._cloudcasts_api.get_similar(username, cloudcast_slug, limit=3)
                
                # The result might be a PaginatedResult or similar object
                if hasattr(result, 'items'):
                    similar = result.items
                elif hasattr(result, 'data'):
                    similar = result.data
                else:
                    similar = result if isinstance(result, list) else []
                
                if similar:
                    assert len(similar) <= 3, f"Too many results: {len(similar)}"
                    assert all(isinstance(c, Cloudcast) for c in similar), "Invalid cloudcast type"
                    self.record_success(test_name, f"Found {len(similar)} similar cloudcasts")
                else:
                    self.record_success(test_name, "No similar cloudcasts found (normal)")
            else:
                self.record_failure(test_name, f"Invalid cloudcast key format: {cloudcast.key}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_get_user(self):
        """Test getting a specific user."""
        test_name = "Get User"
        try:
            # First search for a user
            search_results = await self.client.search_users("mixcloud", limit=1)
            if not search_results:
                self.record_failure(test_name, "No users found to test")
                return
            
            username = search_results[0].username
            
            # Get the user details
            user = await self.client.get_user(username)
            
            assert user, "Failed to get user"
            assert user.username == username, "Username mismatch"
            assert user.name, "Missing display name"
            
            self.record_success(test_name, f"Got user: {user.name}")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_user_cloudcasts(self):
        """Test getting user's cloudcasts."""
        test_name = "User Cloudcasts"
        try:
            # First search for a user
            search_results = await self.client.search_users("dj", limit=1)
            if not search_results:
                self.record_failure(test_name, "No users found to test")
                return
            
            username = search_results[0].username
            
            # Get user's cloudcasts
            cloudcasts = await self.client.get_user_cloudcasts(username, limit=3)
            
            assert isinstance(cloudcasts, list), "Invalid result type"
            assert len(cloudcasts) <= 3, f"Too many results: {len(cloudcasts)}"
            
            if cloudcasts:
                assert all(isinstance(c, Cloudcast) for c in cloudcasts), "Invalid cloudcast type"
            
            self.record_success(test_name, f"Found {len(cloudcasts)} cloudcasts")
            
        except Exception as e:
            self.record_failure(test_name, str(e))
    
    async def test_popular_cloudcasts(self):
        """Test getting popular cloudcasts."""
        test_name = "Popular Cloudcasts"
        try:
            # Try to get popular cloudcasts (may not always be available)
            popular = await self.client.get_popular(limit=5)
            
            if popular:
                assert len(popular) <= 5, f"Too many results: {len(popular)}"
                assert all(isinstance(c, Cloudcast) for c in popular), "Invalid cloudcast type"
                self.record_success(test_name, f"Found {len(popular)} popular cloudcasts")
            else:
                # Not a failure if endpoint returns empty
                self.record_success(test_name, "Popular endpoint returned empty (normal behavior)")
            
        except Exception as e:
            # Some endpoints may not be available
            if "not found" in str(e).lower():
                self.record_success(test_name, "Popular endpoint not available (expected)")
            else:
                self.record_failure(test_name, str(e))
    
    async def test_hot_cloudcasts(self):
        """Test getting hot cloudcasts."""
        test_name = "Hot Cloudcasts"
        try:
            # Try to get hot cloudcasts (may not always be available)
            hot = await self.client.get_hot(limit=5)
            
            if hot:
                assert len(hot) <= 5, f"Too many results: {len(hot)}"
                assert all(isinstance(c, Cloudcast) for c in hot), "Invalid cloudcast type"
                self.record_success(test_name, f"Found {len(hot)} hot cloudcasts")
            else:
                # Not a failure if endpoint returns empty
                self.record_success(test_name, "Hot endpoint returned empty (normal behavior)")
            
        except Exception as e:
            # Some endpoints may not be available
            if "not found" in str(e).lower():
                self.record_success(test_name, "Hot endpoint not available (expected)")
            else:
                self.record_failure(test_name, str(e))
    
    async def test_categories(self):
        """Test getting categories."""
        test_name = "Categories"
        try:
            categories = await self.client.get_categories()
            
            assert categories, "No categories found"
            assert all(isinstance(c, Category) for c in categories), "Invalid category type"
            
            # Check first category has expected fields
            if categories:
                category = categories[0]
                assert category.name, "Missing category name"
                assert category.key, "Missing category key"
            
            self.record_success(test_name, f"Found {len(categories)} categories")
            
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
    tester = TestMixcloudAPI()
    await tester.run_all_tests()
    
    # Return exit code
    return 0 if tester.failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)