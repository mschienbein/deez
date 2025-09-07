# Music Agent Integration Tests

This directory contains comprehensive test suites and results for all music service integrations.

## Test Structure

```
tests/
├── README.md                 # This file
├── discogs/                  # Discogs API tests
│   ├── test_connection.py    # Basic connection test
│   ├── test_discogs_api.py   # Comprehensive API test
│   ├── test_discogs.py       # Original test suite
│   └── test_results.md       # Test results documentation
├── musicbrainz/              # MusicBrainz tests (pending)
├── spotify/                  # Spotify tests (pending)
├── deezer/                   # Deezer tests (pending)
├── beatport/                 # Beatport tests (pending)
├── soundcloud/               # SoundCloud tests (existing)
├── bandcamp/                 # Bandcamp tests (existing)
├── mixcloud/                 # Mixcloud tests (existing)
└── youtube/                  # YouTube tests (pending)
```

## Running Tests

### Prerequisites
- Python 3.13+
- uv package manager
- Valid API credentials in `.env` file

### Run All Tests
```bash
# Run all integration tests
uv run pytest tests/

# Run specific integration tests
uv run pytest tests/discogs/
```

### Run Individual Test Suites
```bash
# Discogs
uv run python tests/discogs/test_connection.py
uv run python tests/discogs/test_discogs_api.py

# Other integrations (when available)
uv run python tests/spotify/test_spotify.py
uv run python tests/musicbrainz/test_musicbrainz.py
```

## Test Coverage Status

| Integration | Status | Test Coverage | API Coverage | Last Tested |
|------------|--------|---------------|--------------|-------------|
| Discogs | ✅ Complete | 100% | 8/8 endpoints | 2025-09-07 |
| MusicBrainz | 🚧 Pending | 0% | 0/10 endpoints | - |
| Spotify | 🚧 Pending | 0% | 0/15 endpoints | - |
| Deezer | 🚧 Pending | 0% | 0/12 endpoints | - |
| Beatport | 🔄 In Progress | 50% | 5/10 endpoints | - |
| SoundCloud | ✅ Complete | 100% | 10/10 endpoints | - |
| Bandcamp | ✅ Complete | 100% | 8/8 endpoints | - |
| Mixcloud | ✅ Complete | 100% | 7/7 endpoints | - |
| YouTube | 🚧 Pending | 0% | 0/5 endpoints | - |
| Soulseek | 🚧 Pending | 0% | 0/8 endpoints | - |

## Environment Setup

Create a `.env` file in the project root with the following variables:

```bash
# Discogs
DISCOGS_USER_TOKEN=your_token_here
DISCOGS_CONSUMER_KEY=your_key_here
DISCOGS_CONSUMER_SECRET=your_secret_here
DISCOGS_USER_AGENT=YourApp/1.0

# Spotify
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Deezer
DEEZER_APP_ID=your_app_id
DEEZER_SECRET_KEY=your_secret

# MusicBrainz
MUSICBRAINZ_USER_AGENT=YourApp/1.0

# YouTube
YOUTUBE_API_KEY=your_api_key

# Beatport
BEATPORT_USERNAME=your_username
BEATPORT_PASSWORD=your_password

# Add other service credentials as needed
```

## Test Requirements

Each integration test suite should include:

1. **Connection Test** - Verify API authentication and basic connectivity
2. **Search Test** - Test search functionality with various filters
3. **Metadata Retrieval** - Test fetching detailed information
4. **Rate Limiting** - Verify rate limit handling
5. **Error Handling** - Test error scenarios and recovery
6. **Edge Cases** - Test boundary conditions and special cases

## Writing New Tests

When adding tests for a new integration:

1. Create a directory under `tests/` for the service
2. Include at least:
   - `test_connection.py` - Basic connectivity test
   - `test_{service}_api.py` - Comprehensive API test
   - `test_results.md` - Document test results
3. Follow the existing test patterns from Discogs
4. Use real API endpoints (no mocks)
5. Handle authentication properly
6. Document all test results

## Test Utilities

Common test utilities are available:

```python
from tests.utils import (
    load_test_config,    # Load test configuration
    assert_api_response,  # Validate API responses
    measure_performance,  # Performance testing
    retry_on_rate_limit  # Rate limit handling
)
```

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Main branch commits
- Nightly schedules

## Contributing

When contributing new tests:
1. Ensure all tests pass locally
2. Document test results
3. Update this README with coverage status
4. Include error handling and edge cases
5. Follow existing naming conventions

## Support

For test-related issues:
- Check test results documentation
- Review API credentials
- Verify network connectivity
- Check service API status pages

---

*Last Updated: September 7, 2025*