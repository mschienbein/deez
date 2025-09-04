# Mixcloud Integration

A fully-featured Mixcloud integration for the music agent, following the same modular pattern as the SoundCloud integration.

## Features

### ✅ Completed
- **OAuth2 Authentication**: Full OAuth2 flow with browser-based authentication
- **Search**: Search for cloudcasts, users, and tags
- **Discovery**: Get popular, trending, new, and featured content
- **User Management**: Get user info, cloudcasts, favorites, followers
- **Cloudcast Operations**: Get cloudcast details, comments, similar tracks
- **Categories**: Browse content by category
- **Data Models**: Complete TypedDict definitions and model classes
- **Error Handling**: Comprehensive exception hierarchy
- **Configuration**: Environment variable support with sensible defaults
- **Utilities**: Formatters, validators, and helper functions

### 🔄 Partial Support
- **Download**: Stream extraction framework (limited by Mixcloud's protection)
- **Social Features**: Favorite, follow, repost (requires authentication)

## Installation

```bash
pip install aiohttp mutagen
```

## Configuration

Set environment variables in `.env`:

```bash
# Mixcloud Configuration
MIXCLOUD_CLIENT_ID="your-client-id"
MIXCLOUD_CLIENT_SECRET="your-client-secret"
MIXCLOUD_REDIRECT_URI="http://localhost:8080/callback"
```

## Usage

```python
import asyncio
from src.music_agent.integrations.mixcloud import MixcloudClient

async def main():
    # Create client
    client = MixcloudClient()
    
    async with client:
        # Search for cloudcasts
        results = await client.search_cloudcasts("techno", limit=5)
        for cloudcast in results:
            print(f"{cloudcast.name} by {cloudcast.username}")
        
        # Get user info
        user = await client.get_user("NTSRadio")
        print(f"{user.display_name}: {user.follower_count} followers")
        
        # Get popular content
        popular = await client.get_popular(limit=10)
        
        # Download (if stream available)
        # Note: Most Mixcloud content is protected
        try:
            path = await client.download_cloudcast(
                cloudcast,
                output_dir="downloads/"
            )
            print(f"Downloaded to: {path}")
        except Exception as e:
            print(f"Download not available: {e}")

asyncio.run(main())
```

## API Coverage

### Implemented Endpoints
- `GET /search/` - Search content
- `GET /{username}/` - Get user
- `GET /{username}/{cloudcast}/` - Get cloudcast
- `GET /{username}/cloudcasts/` - User's cloudcasts
- `GET /{username}/favorites/` - User's favorites
- `GET /{username}/followers/` - User's followers
- `GET /{username}/following/` - User's following
- `GET /popular/` - Popular cloudcasts
- `GET /popular/hot/` - Trending cloudcasts
- `GET /categories/` - Browse categories
- `GET /tag/{tag}/` - Content by tag

### Authenticated Endpoints (OAuth2 Required)
- `POST /{username}/{cloudcast}/favorite/` - Like cloudcast
- `POST /{username}/{cloudcast}/repost/` - Repost cloudcast
- `POST /{username}/follow/` - Follow user
- `POST /{username}/{cloudcast}/comments/` - Add comment

## Architecture

```
mixcloud/
├── api/           # API endpoint clients
├── auth/          # OAuth2 authentication
├── config/        # Configuration management
├── download/      # Download functionality
├── models/        # Data models
├── types/         # TypedDict definitions
├── utils/         # Helper utilities
├── exceptions/    # Exception hierarchy
└── client.py      # Main client
```

## Testing

Run the test script:

```bash
python test_mixcloud.py
```

With download testing:

```bash
python test_mixcloud.py --download
```

## Limitations

1. **Stream Protection**: Mixcloud protects most streams with encryption and HLS
2. **Exclusive Content**: Mixcloud Select content requires subscription
3. **Rate Limiting**: API has rate limits (handled automatically)
4. **Authentication**: Some features require OAuth2 authentication

## Similar to SoundCloud Integration

This integration follows the exact same patterns as the SoundCloud integration:
- Modular architecture with separation of concerns
- Async/await throughout with aiohttp
- TypedDict for type safety
- Comprehensive error handling
- Environment variable configuration
- OAuth2 authentication flow
- Download support with metadata
- Search and discovery features

## API Keys

The integration is configured with the provided API credentials:
- Client ID: `bi9gnDJ9fY6C0n12xQ`
- Client Secret: `sMnouM3jgdAAyto84DhFeVLrRvA7ahxL`

These are already set in the `.env` file for testing.