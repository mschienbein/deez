# Music Agent Testing Guide

## Quick Start

### Run All Tests
```bash
# Run test suite for all ready integrations
uv run python tests/run_tests.py

# Run specific integration test
uv run python tests/run_tests.py discogs

# Run multiple integration tests
uv run python tests/run_tests.py discogs spotify deezer
```

### Individual Test Files
```bash
# Discogs tests
uv run python tests/discogs/test_connection.py
uv run python tests/discogs/test_discogs_api.py

# Other integrations (when ready)
uv run python tests/spotify/test_spotify.py
uv run python tests/musicbrainz/test_musicbrainz.py
```

## Test Organization

```
tests/
├── README.md              # Overview and status
├── TESTING_GUIDE.md       # This file
├── run_tests.py           # Master test runner
├── test_report.md         # Latest test results
│
├── discogs/               # ✅ Complete
│   ├── test_connection.py
│   ├── test_discogs_api.py
│   ├── test_discogs.py
│   └── test_results.md
│
├── musicbrainz/           # 🚧 Pending
├── spotify/               # 🚧 Pending
├── deezer/                # 🚧 Pending
├── beatport/              # 🚧 Pending
├── soundcloud/            # ✅ Complete
├── bandcamp/              # ✅ Complete
├── mixcloud/              # ✅ Complete
├── youtube/               # 🚧 Pending
└── soulseek/              # 🚧 Pending
```

## Test Types

### 1. Connection Test (`test_connection.py`)
Quick verification of API connectivity and authentication.

**Checks:**
- Environment variables loaded
- API credentials valid
- Basic API call succeeds
- Response format correct

### 2. Comprehensive API Test (`test_{service}_api.py`)
Full test suite covering all endpoints and features.

**Coverage:**
- Search operations
- Metadata retrieval
- Entity lookups (artists, albums, tracks)
- Pagination
- Error handling
- Rate limiting
- Edge cases

### 3. Integration Test (`test_{service}.py`)
Original test files with interactive features and detailed logging.

## Writing Tests

### Test Template
```python
#!/usr/bin/env python3
"""
Test suite for {Service} integration.
"""

import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.music_agent.integrations.{service} import {Service}Client

def test_connection():
    """Test basic API connection."""
    client = {Service}Client.from_env()
    
    # Test basic search
    results = client.search("test query")
    assert len(results) > 0
    
    return True

def test_metadata():
    """Test metadata retrieval."""
    client = {Service}Client.from_env()
    
    # Test getting specific item
    item = client.get_item(item_id)
    assert item.title is not None
    
    return True

if __name__ == "__main__":
    success = test_connection() and test_metadata()
    sys.exit(0 if success else 1)
```

### Best Practices

1. **Use Real APIs**: No mocks - test against actual endpoints
2. **Handle Auth Properly**: Check for credentials before testing
3. **Test Error Cases**: Include 404s, rate limits, invalid inputs
4. **Document Results**: Update test_results.md with findings
5. **Be Idempotent**: Tests should be runnable multiple times
6. **Clean Up**: Don't leave test data in external services

## Environment Setup

### Required Variables
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your credentials
vim .env
```

### Service-Specific Requirements

#### Discogs
- `DISCOGS_USER_TOKEN`: Personal access token
- `DISCOGS_CONSUMER_KEY`: OAuth consumer key
- `DISCOGS_CONSUMER_SECRET`: OAuth consumer secret
- Rate limit: 60 requests/minute (authenticated)

#### Spotify
- `SPOTIFY_CLIENT_ID`: App client ID
- `SPOTIFY_CLIENT_SECRET`: App client secret
- OAuth flow required for user data

#### MusicBrainz
- `MUSICBRAINZ_USER_AGENT`: Custom user agent string
- Rate limit: 1 request/second
- No authentication required

#### Deezer
- `DEEZER_APP_ID`: Application ID
- `DEEZER_SECRET_KEY`: Secret key
- OAuth for user data access

## Debugging Tests

### Verbose Output
```bash
# Run with verbose flag
uv run python tests/run_tests.py --verbose

# Enable debug logging
export DEBUG=1
uv run python tests/discogs/test_connection.py
```

### Common Issues

#### Authentication Errors
- Check `.env` file exists and has correct values
- Verify API credentials are valid
- Check token expiration

#### Rate Limiting
- Tests include automatic rate limit handling
- If persistent, wait 60 seconds between runs
- Check service-specific rate limits

#### Network Issues
- Verify internet connectivity
- Check service status pages
- Try with curl/wget first

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'
    
    - name: Install uv
      run: pip install uv
    
    - name: Install dependencies
      run: uv pip install -r requirements.txt
    
    - name: Run tests
      env:
        DISCOGS_USER_TOKEN: ${{ secrets.DISCOGS_USER_TOKEN }}
        # Add other secrets
      run: uv run python tests/run_tests.py
```

## Reporting

### Test Results Format
Each integration should have a `test_results.md` file with:

1. **Executive Summary**: Overall status and key findings
2. **Configuration**: Environment and dependencies
3. **Test Results**: Detailed results for each endpoint
4. **Performance Metrics**: Response times, rate limits
5. **Known Issues**: Any problems or limitations
6. **Recommendations**: Improvements or next steps

### Success Criteria

Integration is considered complete when:
- [ ] All endpoints documented in API are tested
- [ ] Authentication mechanisms verified
- [ ] Error handling validated
- [ ] Rate limiting confirmed working
- [ ] Test documentation complete
- [ ] Results documented in test_results.md

## Support

For test-related issues:
1. Check this guide first
2. Review service API documentation
3. Check test_results.md for known issues
4. Verify credentials and network

---

*Last Updated: September 7, 2025*