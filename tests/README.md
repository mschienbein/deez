# Music Agent Integration Tests

This directory contains comprehensive test suites and results for all music service integrations.

## Test Structure

```
tests/
├── README.md                 # This file
├── test_report.md            # Automated test results
├── run_tests.py              # Master test runner
├── discogs/                  # Discogs API tests ✅
│   ├── test_connection.py    # Basic connection test
│   └── test_discogs_api.py   # Comprehensive API test
├── musicbrainz/              # MusicBrainz tests ✅
│   ├── test_connection.py    # Basic connection test
│   └── test_musicbrainz_api.py # Comprehensive API test
├── beatport/                 # Beatport tests ✅
│   ├── test_connection.py    # Basic connection test
│   └── test_beatport_api.py  # Comprehensive API test
├── mixcloud/                 # Mixcloud tests ✅
│   ├── test_connection.py    # Basic connection test
│   └── test_mixcloud_api.py  # Comprehensive API test
├── deezer/                   # Deezer tests ✅
│   ├── test_connection.py    # Basic connection test
│   └── test_deezer_api.py    # Comprehensive API test with download
├── spotify/                  # Spotify tests (pending)
├── soundcloud/               # SoundCloud tests (pending)
├── bandcamp/                 # Bandcamp tests (pending)
├── youtube/                  # YouTube tests (pending)
└── soulseek/                 # Soulseek tests (pending)
```

## Running Tests

### Prerequisites
- Python 3.13+
- uv package manager
- Valid API credentials in `.env` file

### Run All Tests
```bash
# Run all integration tests with the master test runner
uv run python tests/run_tests.py

# Run specific integration tests
uv run python tests/discogs/test_discogs_api.py
uv run python tests/musicbrainz/test_musicbrainz_api.py
uv run python tests/beatport/test_beatport_api.py
uv run python tests/mixcloud/test_mixcloud_api.py
uv run python tests/deezer/test_deezer_api.py
```

### Run Individual Test Suites
```bash
# Connection tests (quick validation)
uv run python tests/discogs/test_connection.py
uv run python tests/musicbrainz/test_connection.py
uv run python tests/beatport/test_connection.py
uv run python tests/mixcloud/test_connection.py
uv run python tests/deezer/test_connection.py

# Comprehensive API tests
uv run python tests/discogs/test_discogs_api.py
uv run python tests/musicbrainz/test_musicbrainz_api.py
uv run python tests/beatport/test_beatport_api.py
uv run python tests/mixcloud/test_mixcloud_api.py
uv run python tests/deezer/test_deezer_api.py
```

## Test Coverage Status

| Integration | Status | Test Coverage | API Coverage | Last Tested |
|------------|--------|---------------|--------------|-------------|
| Discogs | ✅ Complete | 100% | 8/8 endpoints | 2025-09-07 |
| MusicBrainz | ✅ Complete | 100% | 12/12 endpoints | 2025-09-07 |
| Beatport | ✅ Complete | 100% | 10/10 endpoints | 2025-09-07 |
| Mixcloud | ✅ Complete | 100% | 7/7 endpoints | 2025-09-07 |
| Deezer | ✅ Complete | 100% | 13/13 endpoints | 2025-09-08 |
| Spotify | 🚧 Pending | 0% | 0/15 endpoints | - |
| SoundCloud | 🚧 Pending | 0% | 0/10 endpoints | - |
| Bandcamp | 🚧 Pending | 0% | 0/8 endpoints | - |
| YouTube | 🚧 Pending | 0% | 0/5 endpoints | - |
| Soulseek | 🚧 Pending | 0% | 0/8 endpoints | - |

### Latest Test Results (from test_report.md)
- **Total Integrations Tested:** 5
- **All Passing:** ✅ 100% success rate
- **Test Duration:** ~3 seconds total
- **Endpoints Tested:** 50+ API endpoints
- **Download Support:** Deezer (with encryption/decryption)

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

*Last Updated: September 8, 2025*