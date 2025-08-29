"""Configuration management for music agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


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
    rate_limit: int = Field(default=10, description="Requests per second")


class YouTubeConfig(BaseModel):
    """YouTube configuration."""
    
    cookies_file: Optional[str] = Field(default=None, description="Path to cookies file")
    rate_limit: int = Field(default=5, description="Requests per second")
    audio_format: str = Field(default="mp3", description="Audio format for downloads")
    audio_quality: str = Field(default="192", description="Audio quality in kbps")


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    base_url: Optional[str] = Field(default=None, description="Custom OpenAI base URL")
    organization: Optional[str] = Field(default=None, description="OpenAI organization")


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


class DatabaseConfig(BaseModel):
    """Database configuration."""
    
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
    cache_dir: Path = Field(default=Path(".cache"), description="Cache directory")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    primary_provider: str = Field(default="openai", description="Primary model provider (openai or bedrock)")
    fallback_provider: str = Field(default="bedrock", description="Fallback model provider")


class Config(BaseModel):
    """Main configuration."""
    
    deezer: DeezerConfig
    spotify: SpotifyConfig
    youtube: YouTubeConfig
    openai: OpenAIConfig
    aws: AWSConfig
    database: DatabaseConfig
    agent: AgentConfig
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        return cls(
            deezer=DeezerConfig(
                arl=os.getenv("DEEZER_ARL"),
                rate_limit=int(os.getenv("DEEZER_RATE_LIMIT", "10")),
            ),
            spotify=SpotifyConfig(
                username=os.getenv("SPOTIFY_USERNAME"),
                password=os.getenv("SPOTIFY_PASSWORD"),
                totp_secret=os.getenv("SPOTIFY_TOTP_SECRET"),
                rate_limit=int(os.getenv("SPOTIFY_RATE_LIMIT", "10")),
            ),
            youtube=YouTubeConfig(
                cookies_file=os.getenv("YOUTUBE_COOKIES_FILE"),
                rate_limit=int(os.getenv("YOUTUBE_RATE_LIMIT", "5")),
            ),
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                organization=os.getenv("OPENAI_ORGANIZATION"),
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
            database=DatabaseConfig(
                url=os.getenv("DATABASE_URL", "sqlite:///music_agent.db"),
            ),
            agent=AgentConfig(
                name=os.getenv("AGENT_NAME", "music-discovery-agent"),
                log_level=os.getenv("AGENT_LOG_LEVEL", "INFO"),
                cache_dir=Path(os.getenv("CACHE_DIR", ".cache")),
                cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
                primary_provider=os.getenv("PRIMARY_MODEL_PROVIDER", "openai"),
                fallback_provider=os.getenv("FALLBACK_MODEL_PROVIDER", "bedrock"),
            ),
        )


# Global configuration instance
config = Config.from_env()