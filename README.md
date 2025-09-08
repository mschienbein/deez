# Music Discovery Agent

An intelligent music agent built with AWS Strands that integrates with multiple music platforms (Deezer, Spotify, YouTube) for comprehensive music discovery, playlist management, and analytics.

## Features

- **Multi-Platform Search**: Search across Deezer, Spotify, and YouTube simultaneously
- **Natural Language Interface**: Query music using natural language 
- **Cross-Platform Playlists**: Create playlists with tracks from multiple platforms
- **Intelligent Matching**: Automatically match tracks across platforms using metadata
- **Music Analytics**: Analyze listening patterns and trends
- **High-Quality Downloads**: Support for FLAC and high-quality MP3 downloads
- **Playlist Export**: Export playlists in various formats (JSON, M3U, CSV)

## Architecture

Built on AWS Strands Agents framework with:
- **OpenAI**: GPT-5 as the AI model provider
- **AWS AgentCore**: Production deployment runtime
- **SQLite Database**: Local storage for tracks, playlists, and user data
- **Multi-Platform APIs**: Direct integration with music service APIs

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key
- AWS Account (for AgentCore deployment)
- Music service accounts (Deezer, Spotify, YouTube)

### Setup

1. **Clone and install**:
```bash
git clone <repo-url>
cd music-agent
pip install -e .
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Required credentials**:
   - **Deezer**: ARL cookie from browser
   - **Spotify**: Username, password, TOTP secret (if 2FA enabled)
   - **YouTube**: Cookies file (optional)
   - **AWS**: Access keys and Bedrock permissions

## Usage

### Rich Interactive CLI

```bash
# Interactive mode with beautiful Rich interface
python music_agent.py --interactive

# Direct search (simple mode)
python music_agent.py --search "Adele Hello" --platform all

# Single query (simple mode)
python music_agent.py --query "Find me some relaxing jazz music"

# Check configuration
python music_agent.py --config-check
```

#### Rich CLI Features
- 🎨 Beautiful terminal interface with colors and formatting
- 📊 Real-time progress indicators and status displays
- 📋 Formatted tables for search results and playlists
- 🤖 Clear agent status with provider information
- ⚙️ Configuration display with service availability
- 📖 Built-in help system with command documentation

### Interactive Examples

```
You: Find all songs by The Beatles on Spotify and Deezer
Agent: I'll search for The Beatles across both platforms...

You: Create a playlist called "Road Trip" with classic rock songs
Agent: Creating a "Road Trip" playlist with classic rock tracks...

You: What are my listening trends from last month?
Agent: Analyzing your listening patterns from the past month...

You: Download the highest quality version of "Bohemian Rhapsody"
Agent: Searching for the best quality version across platforms...
```

## Platform Integration

### Completed Integrations (Fully Modular) - 6 Total

#### Deezer ✅
- Full async/await architecture with modular structure
- Search tracks, albums, playlists, artists
- Download FLAC/MP3 with AES encryption/decryption support
- Track metadata writing with mutagen
- ARL cookie authentication
- Gateway API and CDN integration

#### Discogs ✅
- Comprehensive search across releases, artists, labels
- OAuth1 authentication flow
- Collection management and wantlist features
- Marketplace integration
- Rate limiting with retry logic

#### MusicBrainz ✅
- Artist, release, recording searches
- Advanced query builder with filters
- Relationship data (collaborations, remixes)
- Cover art archive integration
- No authentication required

#### Beatport ✅
- Track, release, artist searches
- Genre-specific charts and trending
- OAuth2 authentication
- High-quality download support
- DJ-focused metadata (BPM, key, genre)

#### Mixcloud ✅
- Cloudcast (mix) search and streaming
- User profile and show discovery
- OAuth2 authentication
- Tag-based discovery
- Live show support

#### Soulseek ✅
- P2P file sharing network via slskd server
- Advanced search with bitrate filtering
- Download management with progress monitoring
- User browsing and file discovery
- Quality scoring algorithm
- Concurrent download support

### In-Progress Integrations

#### Spotify (Single file - needs refactor)
- Browse playlists and discover music
- Get recommendations and trending tracks
- Web API integration with 2FA support
- Track metadata and audio features

#### YouTube (Single file - needs enhancement)
- Find music videos and live performances
- Download audio using yt-dlp
- Search rare and unavailable tracks
- Extract metadata from video descriptions

#### SoundCloud (Partial structure)
- Track and playlist search
- User profile browsing
- Free streaming and downloads
- Remix and DJ set discovery

#### Bandcamp (Partial structure)
- Artist and album discovery
- Direct artist support
- High-quality downloads
- Underground music focus

## AWS AgentCore Deployment

### Local Development
```bash
# Run locally
python music_agent.py --interactive
```

### Production Deployment
```bash
# Configure AgentCore
agentcore configure --config config/agentcore.config.yaml

# Deploy to AWS
agentcore deploy --region us-east-1
```

### Required AWS Resources
- Amazon Bedrock access
- AWS Secrets Manager for credentials
- Amazon S3 for configuration storage
- AWS CloudWatch for monitoring
- AWS IAM roles with appropriate permissions

## Database Schema

SQLite database with tables for:
- **Tracks**: Music metadata across platforms
- **Playlists**: User-created and imported playlists  
- **User Preferences**: Quality settings and platform preferences
- **Listening History**: Play counts and timestamps
- **Search History**: Query logs for analytics

## Custom Tools

The agent includes custom Strands tools:
- `search_music()`: Multi-platform music search
- `get_track_info()`: Detailed track metadata
- `create_cross_platform_playlist()`: Cross-platform playlist creation
- `analyze_music_trends()`: Listening pattern analysis
- `export_playlist()`: Multi-format playlist export
- `match_track_across_platforms()`: Cross-platform track matching

## Configuration

Environment variables (`.env`):
```bash
# Music Services
DEEZER_ARL=your_arl_cookie
SPOTIFY_USERNAME=your_username
SPOTIFY_PASSWORD=your_password
SPOTIFY_TOTP_SECRET=your_totp_secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5
OPENAI_BASE_URL=
OPENAI_ORGANIZATION=

# AWS (for AgentCore deployment)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0

# Database
DATABASE_URL=sqlite:///music_agent.db

# Agent Settings
AGENT_LOG_LEVEL=INFO
CACHE_DIR=.cache
```

## Security & Compliance

- Secure credential storage using AWS Secrets Manager
- Local metadata processing (no external data transmission)
- Compliance with music platform Terms of Service
- Rate limiting to respect API constraints
- Educational and personal use focus

## Development

### Project Structure
```
src/music_agent/
├── agent/          # Core agent implementation
├── integrations/   # Platform-specific APIs
├── tools/          # Custom Strands tools
├── database/       # Database schema and operations
└── utils/          # Configuration and utilities
```

### Testing
```bash
# Run tests (coming soon)
pytest tests/

# Manual testing
python music_agent.py --search "test query" --platform deezer
```

## Observability

When deployed with AgentCore:
- Automatic Langfuse tracing integration
- CloudWatch metrics and logging
- Performance monitoring
- Cost tracking for Bedrock usage
- Session tracking and user analytics

## License

Educational and personal use. Ensure compliance with music platform Terms of Service.
