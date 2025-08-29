# Music Agent Architecture Plan

## Project Overview

This project creates an intelligent music agent using AWS Strands Agents framework that integrates with multiple music services (Deezer, Spotify, YouTube) and can be queried in natural language to find, analyze, and manage music across platforms. The agent will be deployed using AWS AgentCore for production scalability.

## Architecture Components

### 1. Core Agent Framework

**Technology**: AWS Strands Agents SDK
- **Model Provider**: Amazon Bedrock with Anthropic Claude 3.5 Haiku/Sonnet
- **Deployment Target**: AWS AgentCore Runtime (with local development support)
- **Agent Pattern**: Model-first design with autonomous reasoning capabilities

### 2. Music Service Integration Layer

#### 2.1 Deezer Integration
**Based on**: `kmille/deezer-downloader` repository APIs
- **Authentication**: ARL cookie-based authentication
- **Core Functions**:
  - `deezer_search()` - Search tracks, albums, artists, playlists
  - `get_song_infos_from_deezer_website()` - Detailed track metadata
  - `parse_deezer_playlist()` - Playlist parsing and song extraction
  - `get_deezer_favorites()` - User favorites retrieval
- **Quality Support**: FLAC/MP3 320kbps (premium) or MP3 128kbps (free)
- **Implementation**: Direct API calls via Strands `http_request` tool

#### 2.2 Spotify Integration
**Based on**: `deezer-downloader/spotify.py` implementation
- **Authentication**: Web token-based authentication with TOTP
- **Core Functions**:
  - `get_songs_from_spotify_website()` - Playlist/album/track parsing
  - `parse_track()` - Track metadata extraction
  - Support for playlists, albums, and individual tracks
- **Implementation**: HTTP requests via Strands tools to Spotify Web API

#### 2.3 YouTube Integration
**Based on**: yt-dlp integration from deezer-downloader
- **Tool Used**: Strands `shell` tool to execute yt-dlp commands
- **Capabilities**:
  - Video/audio download and extraction
  - Metadata retrieval
  - Search and discovery
- **Fallback Strategy**: Use YouTube as fallback when tracks unavailable on primary services

### 3. Data Storage Layer

#### 3.1 Primary Database: SQLite
**Purpose**: Local development and simple deployments
- **Schema Design**:
  ```sql
  CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    album TEXT,
    deezer_id TEXT,
    spotify_id TEXT,
    youtube_url TEXT,
    duration INTEGER,
    genre TEXT,
    release_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE playlists (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    source_platform TEXT,
    source_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE playlist_tracks (
    playlist_id INTEGER,
    track_id INTEGER,
    position INTEGER,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
  );

  CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    preferred_quality TEXT DEFAULT 'mp3_320',
    preferred_platform TEXT DEFAULT 'deezer',
    auto_fallback BOOLEAN DEFAULT true
  );
  ```

#### 3.2 Future Scaling Options
- **Amazon DynamoDB**: For production scale with AgentCore
- **Amazon RDS**: For complex relational queries
- **Memory Integration**: Strands `mem0_memory` or `agent_core_memory` tools for user personalization

### 4. Strands Tools Implementation

#### 4.1 Core Tools Used
```python
from strands_tools import (
    http_request,      # API calls to music services
    python_repl,       # Complex data processing
    shell,             # yt-dlp execution
    file_read,         # Configuration management
    file_write,        # Data export
    calculator,        # Analytics calculations
    current_time,      # Timestamps
    use_aws           # AWS service integration
)
```

#### 4.2 Custom Tools Development
```python
@tool
def search_music(query: str, platform: str = "all", limit: int = 10) -> List[Dict]:
    """Search for music across platforms with intelligent fallback"""
    # Implementation using http_request tool for each platform
    
@tool
def get_track_info(track_id: str, platform: str) -> Dict:
    """Get detailed track information from specific platform"""
    
@tool
def create_cross_platform_playlist(name: str, tracks: List[str]) -> Dict:
    """Create playlist with tracks from multiple platforms"""
    
@tool
def analyze_music_trends(timeframe: str = "month") -> Dict:
    """Analyze listening patterns and trends"""
    
@tool
def export_playlist(playlist_id: str, format: str = "json") -> str:
    """Export playlist in various formats"""
```

### 5. Agent Capabilities

#### 5.1 Natural Language Interface
**Examples of supported queries**:
- "Find all songs by Adele on Deezer and Spotify"
- "Create a playlist of top electronic tracks from 2023"
- "What's the audio quality available for this album?"
- "Download this YouTube playlist and match tracks on Deezer"
- "Show me my most played genres from last month"

#### 5.2 Cross-Platform Operations
- **Track Matching**: Intelligent matching of tracks across platforms
- **Quality Selection**: Automatic best quality selection based on availability
- **Fallback Strategy**: YouTube → Deezer → Spotify priority chain
- **Duplicate Detection**: Avoid duplicate tracks in cross-platform playlists

#### 5.3 Analytics and Insights
- **Usage Statistics**: Track listening patterns and preferences
- **Platform Comparison**: Compare catalog availability across services
- **Quality Analysis**: Audio format and bitrate optimization
- **Trend Detection**: Identify popular tracks and genres

### 6. Deployment Strategy

#### 6.1 Local Development
```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate
pip install strands-agents strands-agents-tools

# Configuration
cp .env.example .env
# Configure: DEEZER_ARL, SPOTIFY_CREDENTIALS, AWS_CREDENTIALS

# Run agent locally
python music_agent.py
```

#### 6.2 AWS AgentCore Deployment

**Infrastructure Requirements**:
- **Amazon Bedrock**: Model access (Claude 3.5 Haiku/Sonnet)
- **AWS Lambda**: Agent runtime environment
- **Amazon S3**: Configuration and cache storage
- **Amazon CloudWatch**: Logging and monitoring
- **AWS IAM**: Secure service access

**Deployment Process**:
```yaml
# agentcore.config.yaml
agent:
  name: music-discovery-agent
  description: "AI agent for multi-platform music discovery and management"
  model_provider: amazon-bedrock
  model_name: anthropic.claude-3-5-haiku-20241022-v1:0
  tools:
    - http_request
    - python_repl
    - shell
    - use_aws
  environment:
    DEEZER_ARL: ${DEEZER_ARL_SECRET}
    LANGFUSE_HOST: ${LANGFUSE_HOST}
    DATABASE_URL: ${DATABASE_URL}
```

```bash
# Deploy to AgentCore
agentcore configure --config agentcore.config.yaml
agentcore deploy --region us-east-1
```

#### 6.3 Observability Integration

**Using existing MCP observability stack**:
- **Langfuse Integration**: Automatic tracing of all agent interactions
- **Session Tracking**: Link music queries to user sessions
- **Performance Monitoring**: Track API response times and success rates
- **Cost Tracking**: Monitor AWS Bedrock usage and costs

### 7. Security and Compliance

#### 7.1 Credential Management
- **AWS Secrets Manager**: Store Deezer ARL and Spotify credentials
- **Environment Variables**: Secure configuration management
- **IAM Roles**: Least privilege access for AgentCore

#### 7.2 Data Privacy
- **Local Processing**: Music metadata processing without external transmission
- **User Consent**: Explicit consent for data collection and storage
- **Data Retention**: Configurable retention policies for user data

#### 7.3 Platform Compliance
- **Terms of Service**: Ensure compliance with Deezer, Spotify, YouTube ToS
- **Rate Limiting**: Implement proper API rate limiting
- **Fair Use**: Educational and personal use focus

### 8. Implementation Phases

#### Phase 1: Core Foundation (Week 1-2)
- [ ] Set up Strands Agents development environment
- [ ] Implement basic Deezer integration using existing APIs
- [ ] Create SQLite database schema and basic operations
- [ ] Develop core search and retrieval tools

#### Phase 2: Multi-Platform Integration (Week 3-4)
- [ ] Add Spotify integration with authentication
- [ ] Implement YouTube integration via yt-dlp
- [ ] Create cross-platform track matching logic
- [ ] Develop playlist management capabilities

#### Phase 3: Agent Intelligence (Week 5-6)
- [ ] Implement natural language query processing
- [ ] Add analytics and trend analysis features
- [ ] Create recommendation engine
- [ ] Develop export/import functionality

#### Phase 4: Deployment and Optimization (Week 7-8)
- [ ] Configure AWS AgentCore deployment
- [ ] Implement observability with Langfuse
- [ ] Performance optimization and testing
- [ ] Documentation and user guides

### 9. Testing Strategy

#### 9.1 Unit Testing
- Individual tool testing with mock API responses
- Database operation testing
- Authentication flow testing

#### 9.2 Integration Testing
- End-to-end music search and retrieval
- Cross-platform playlist creation
- AgentCore deployment testing

#### 9.3 Performance Testing
- API rate limit handling
- Large playlist processing
- Concurrent user scenarios

### 10. Monitoring and Maintenance

#### 10.1 Health Checks
- Platform API availability monitoring
- Database connection health
- Authentication token validity

#### 10.2 Error Handling
- Graceful degradation when services unavailable
- Retry mechanisms with exponential backoff
- Clear error messages for users

#### 10.3 Updates and Maintenance
- Regular dependency updates
- Platform API changes monitoring
- Performance optimization reviews

## Expected Outcomes

1. **Unified Music Discovery**: Single interface to query multiple music platforms
2. **Intelligent Recommendations**: AI-powered music suggestions based on user patterns
3. **Cross-Platform Playlists**: Seamless playlist creation across Deezer, Spotify, YouTube
4. **Production-Ready Deployment**: Scalable agent running on AWS AgentCore
5. **Rich Analytics**: Insights into music consumption patterns and platform coverage

## Next Steps

1. Review and approve this architecture plan
2. Set up development environment with Strands Agents SDK
3. Clone and examine deezer-downloader repository APIs
4. Begin Phase 1 implementation with core foundation
5. Configure AWS environment for AgentCore deployment

This architecture leverages the full power of AWS Strands Agents framework while building on proven music service integration patterns from the deezer-downloader project.