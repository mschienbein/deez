"""Configuration management for music agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# ====================================
# Database Configurations
# ====================================

class Neo4jConfig(BaseModel):
    """Neo4j/Graphiti configuration."""
    
    uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    username: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="deezmusic123", description="Neo4j password")
    database: str = Field(default="music", description="Neo4j database name")
    auth: str = Field(default="neo4j/deezmusic123", description="Neo4j auth string")


class PostgresConfig(BaseModel):
    """PostgreSQL configuration."""
    
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    user: str = Field(default="music_agent", description="PostgreSQL user")
    password: str = Field(default="music123", description="PostgreSQL password")
    database: str = Field(default="music_catalog", description="PostgreSQL database")
    
    @property
    def url(self) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    """Redis configuration."""
    
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    password: Optional[str] = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")
    
    @property
    def url(self) -> str:
        """Get Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class MinioConfig(BaseModel):
    """MinIO/S3 configuration."""
    
    endpoint: str = Field(default="localhost:9000", description="MinIO endpoint")
    access_key: str = Field(default="minioadmin", description="MinIO access key")
    secret_key: str = Field(default="minioadmin123", description="MinIO secret key")
    bucket: str = Field(default="music-files", description="Default bucket name")
    secure: bool = Field(default=False, description="Use HTTPS")


# ====================================
# Music Service Configurations
# ====================================

class DeezerConfig(BaseModel):
    """Deezer configuration."""
    
    arl: Optional[str] = Field(default=None, description="Deezer ARL cookie")
    rate_limit: int = Field(default=10, description="Requests per second")
    download_quality: str = Field(default="mp3_320", description="Download quality")


class SpotifyConfig(BaseModel):
    """Spotify configuration."""
    
    username: Optional[str] = Field(default=None, description="Spotify username")
    password: Optional[str] = Field(default=None, description="Spotify password")
    totp_secret: Optional[str] = Field(default=None, description="TOTP secret for 2FA")
    client_id: Optional[str] = Field(default=None, description="Spotify client ID")
    client_secret: Optional[str] = Field(default=None, description="Spotify client secret")
    redirect_uri: str = Field(default="http://localhost:8888/callback", description="OAuth redirect URI")
    rate_limit: int = Field(default=10, description="Requests per second")


class YouTubeConfig(BaseModel):
    """YouTube configuration."""
    
    cookies_file: Optional[str] = Field(default=None, description="Path to cookies file")
    api_key: Optional[str] = Field(default=None, description="YouTube API key")
    rate_limit: int = Field(default=5, description="Requests per second")
    audio_format: str = Field(default="mp3", description="Audio format for downloads")
    audio_quality: str = Field(default="192", description="Audio quality in kbps")


class SoulseekConfig(BaseModel):
    """Soulseek/slskd configuration."""
    
    host: str = Field(default="http://localhost:5030", description="slskd host URL")
    api_key: str = Field(default="deez-slskd-api-key-2024", description="slskd API key")
    username: Optional[str] = Field(default=None, description="Soulseek username")
    password: Optional[str] = Field(default=None, description="Soulseek password")
    url_base: str = Field(default="", description="slskd URL base path")
    downloads_path: str = Field(default="./slskd/downloads", description="Downloads directory")
    shares_path: str = Field(default="./slskd/shared", description="Shared files directory")


class RekordboxConfig(BaseModel):
    """Rekordbox configuration."""
    
    db_path: str = Field(
        default="~/Library/Pioneer/rekordbox/master.db",
        description="Path to Rekordbox database"
    )
    encryption_key: str = Field(
        default="402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497",
        description="Rekordbox database encryption key"
    )
    skip_graphiti: bool = Field(default=False, description="Skip Graphiti sync for faster processing")


class BeatportConfig(BaseModel):
    """Beatport configuration."""
    
    api_key: Optional[str] = Field(default=None, description="Beatport API key")
    api_secret: Optional[str] = Field(default=None, description="Beatport API secret")
    username: Optional[str] = Field(default=None, description="Beatport username")
    password: Optional[str] = Field(default=None, description="Beatport password")


class DiscogsConfig(BaseModel):
    """Discogs configuration."""
    
    consumer_key: Optional[str] = Field(default=None, description="Discogs OAuth consumer key")
    consumer_secret: Optional[str] = Field(default=None, description="Discogs OAuth consumer secret")
    request_token_url: str = Field(
        default="https://api.discogs.com/oauth/request_token",
        description="OAuth request token URL"
    )
    authorize_url: str = Field(
        default="https://www.discogs.com/oauth/authorize", 
        description="OAuth authorize URL"
    )
    access_token_url: str = Field(
        default="https://api.discogs.com/oauth/access_token",
        description="OAuth access token URL"
    )
    user_agent: str = Field(default="DeezMusicAgent/1.0", description="User agent for API requests")
    user_token: Optional[str] = Field(default=None, description="Discogs personal access token")
    rate_limit: int = Field(default=60, description="Requests per minute")


# ====================================
# AI/LLM Configurations
# ====================================

class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="gpt-5-nano", description="OpenAI model to use")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")
    base_url: Optional[str] = Field(default=None, description="Custom OpenAI base URL")
    organization: Optional[str] = Field(default=None, description="OpenAI organization")
    max_tokens: int = Field(default=200000, description="Max tokens for completion")
    temperature: float = Field(default=0.7, description="Temperature for completion")


class AWSConfig(BaseModel):
    """AWS configuration."""
    
    region: str = Field(default="us-east-1", description="AWS region")
    access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-5-haiku-20241022-v1:0",
        description="Bedrock model ID"
    )
    bedrock_region: str = Field(default="us-east-1", description="Bedrock region")


# ====================================
# Application Configuration
# ====================================

class DatabaseConfig(BaseModel):
    """Database configuration (legacy SQLite)."""
    
    url: str = Field(default="sqlite:///music_agent.db", description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL statements")


class AgentConfig(BaseModel):
    """Agent configuration."""
    
    name: str = Field(default="music-discovery-agent", description="Agent name")
    description: str = Field(
        default="AI agent for multi-platform music discovery and management",
        description="Agent description"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/music_agent.log", description="Log file path")
    cache_dir: Path = Field(default=Path(".cache"), description="Cache directory")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    primary_provider: str = Field(default="openai", description="Primary model provider (openai or bedrock)")
    fallback_provider: str = Field(default="bedrock", description="Fallback model provider")
    
    # Performance settings
    max_search_results: int = Field(default=20, description="Maximum search results")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    concurrent_requests: int = Field(default=5, description="Maximum concurrent requests")
    
    # Feature flags
    enable_downloads: bool = Field(default=True, description="Enable file downloads")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    enable_analytics: bool = Field(default=True, description="Enable usage analytics")
    enable_cross_platform_search: bool = Field(default=True, description="Enable multi-platform search")
    
    # Audio preferences
    preferred_audio_quality: str = Field(default="FLAC", description="Preferred audio quality")
    default_download_format: str = Field(default="mp3", description="Default download format")


# ====================================
# Main Configuration Class
# ====================================

class Config(BaseModel):
    """Main configuration."""
    
    # Databases
    neo4j: Neo4jConfig
    postgres: PostgresConfig
    redis: RedisConfig
    minio: MinioConfig
    database: DatabaseConfig  # Legacy SQLite
    
    # Music services
    deezer: DeezerConfig
    spotify: SpotifyConfig
    youtube: YouTubeConfig
    soulseek: SoulseekConfig
    rekordbox: RekordboxConfig
    beatport: BeatportConfig
    discogs: DiscogsConfig
    
    # AI/LLM
    openai: OpenAIConfig
    aws: AWSConfig
    
    # Application
    agent: AgentConfig
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        return cls(
            # Databases
            neo4j=Neo4jConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                username=os.getenv("NEO4J_USERNAME", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "deezmusic123"),
                database=os.getenv("NEO4J_DATABASE", "music"),
                auth=os.getenv("NEO4J_AUTH", "neo4j/deezmusic123"),
            ),
            postgres=PostgresConfig(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                user=os.getenv("POSTGRES_USER", "music_agent"),
                password=os.getenv("POSTGRES_PASSWORD", "music123"),
                database=os.getenv("POSTGRES_DB", "music_catalog"),
            ),
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD") or None,
                db=int(os.getenv("REDIS_DB", "0")),
            ),
            minio=MinioConfig(
                endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
                bucket=os.getenv("MINIO_BUCKET", "music-files"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            ),
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL", "sqlite:///music_agent.db"),
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            ),
            
            # Music services
            deezer=DeezerConfig(
                arl=os.getenv("DEEZER_ARL"),
                rate_limit=int(os.getenv("DEEZER_RATE_LIMIT", "10")),
                download_quality=os.getenv("DEEZER_DOWNLOAD_QUALITY", "mp3_320"),
            ),
            spotify=SpotifyConfig(
                username=os.getenv("SPOTIFY_USERNAME"),
                password=os.getenv("SPOTIFY_PASSWORD"),
                totp_secret=os.getenv("SPOTIFY_TOTP_SECRET"),
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
                rate_limit=int(os.getenv("SPOTIFY_RATE_LIMIT", "10")),
            ),
            youtube=YouTubeConfig(
                cookies_file=os.getenv("YOUTUBE_COOKIES_FILE"),
                api_key=os.getenv("YOUTUBE_API_KEY"),
                rate_limit=int(os.getenv("YOUTUBE_RATE_LIMIT", "5")),
                audio_format=os.getenv("YOUTUBE_AUDIO_FORMAT", "mp3"),
                audio_quality=os.getenv("YOUTUBE_AUDIO_QUALITY", "192"),
            ),
            soulseek=SoulseekConfig(
                host=os.getenv("SLSKD_HOST", "http://localhost:5030"),
                api_key=os.getenv("SLSKD_API_KEY", "deez-slskd-api-key-2024"),
                username=os.getenv("SLSKD_USERNAME"),
                password=os.getenv("SLSKD_PASSWORD"),
                url_base=os.getenv("SLSKD_URL_BASE", ""),
                downloads_path=os.getenv("MUSIC_DOWNLOADS_PATH", "./slskd/downloads"),
                shares_path=os.getenv("MUSIC_SHARES_PATH", "./slskd/shared"),
            ),
            rekordbox=RekordboxConfig(
                db_path=os.path.expanduser(
                    os.getenv("REKORDBOX_DB_PATH", "~/Library/Pioneer/rekordbox/master.db")
                ),
                encryption_key=os.getenv(
                    "REKORDBOX_ENCRYPTION_KEY",
                    "402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497"
                ),
                skip_graphiti=os.getenv("SKIP_GRAPHITI", "false").lower() == "true",
            ),
            beatport=BeatportConfig(
                api_key=os.getenv("BEATPORT_API_KEY"),
                api_secret=os.getenv("BEATPORT_API_SECRET"),
                username=os.getenv("BEATPORT_USERNAME"),
                password=os.getenv("BEATPORT_PASSWORD"),
            ),
            discogs=DiscogsConfig(
                consumer_key=os.getenv("DISCOGS_CONSUMER_KEY"),
                consumer_secret=os.getenv("DISCOGS_CONSUMER_SECRET"),
                request_token_url=os.getenv("DISCOGS_REQUEST_TOKEN_URL", "https://api.discogs.com/oauth/request_token"),
                authorize_url=os.getenv("DISCOGS_AUTHORIZE_URL", "https://www.discogs.com/oauth/authorize"),
                access_token_url=os.getenv("DISCOGS_ACCESS_TOKEN_URL", "https://api.discogs.com/oauth/access_token"),
                user_agent=os.getenv("DISCOGS_USER_AGENT", "DeezMusicAgent/1.0"),
                user_token=os.getenv("DISCOGS_USER_TOKEN"),
                rate_limit=int(os.getenv("DISCOGS_RATE_LIMIT", "60")),
            ),
            
            # AI/LLM
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-5"),
                embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                organization=os.getenv("OPENAI_ORGANIZATION"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "200000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            ),
            aws=AWSConfig(
                region=os.getenv("AWS_REGION", "us-east-1"),
                access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                bedrock_model_id=os.getenv(
                    "BEDROCK_MODEL_ID",
                    "anthropic.claude-3-5-haiku-20241022-v1:0"
                ),
                bedrock_region=os.getenv("BEDROCK_REGION", "us-east-1"),
            ),
            
            # Application
            agent=AgentConfig(
                name=os.getenv("AGENT_NAME", "music-discovery-agent"),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE", "./logs/music_agent.log"),
                cache_dir=Path(os.getenv("AGENT_CACHE_DIR", ".cache")),
                cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
                primary_provider=os.getenv("PRIMARY_MODEL_PROVIDER", "openai"),
                fallback_provider=os.getenv("FALLBACK_MODEL_PROVIDER", "bedrock"),
                max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "20")),
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
                concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "5")),
                enable_downloads=os.getenv("ENABLE_DOWNLOADS", "true").lower() == "true",
                enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
                enable_analytics=os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
                enable_cross_platform_search=os.getenv("ENABLE_CROSS_PLATFORM_SEARCH", "true").lower() == "true",
                preferred_audio_quality=os.getenv("PREFERRED_AUDIO_QUALITY", "FLAC"),
                default_download_format=os.getenv("DEFAULT_DOWNLOAD_FORMAT", "mp3"),
            ),
        )


# Global configuration instance
config = Config.from_env()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config