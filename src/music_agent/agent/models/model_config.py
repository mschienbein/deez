"""
Model configuration and provider management.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = "openai"
    BEDROCK = "bedrock"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    provider: ModelProvider
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    region: Optional[str] = None
    temperature: float = 1.0
    max_tokens: int = 4000
    timeout: int = 30
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}
    
    @classmethod
    def from_openai_config(
        cls, 
        model_id: str,
        api_key: str,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs
    ) -> 'ModelConfig':
        """Create OpenAI model configuration."""
        return cls(
            provider=ModelProvider.OPENAI,
            model_id=model_id,
            api_key=api_key,
            base_url=base_url,
            organization=organization,
            **kwargs
        )
    
    @classmethod
    def from_bedrock_config(
        cls,
        model_id: str,
        region: str = "us-east-1",
        **kwargs
    ) -> 'ModelConfig':
        """Create Bedrock model configuration."""
        return cls(
            provider=ModelProvider.BEDROCK,
            model_id=model_id,
            region=region,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "provider": self.provider.value,
            "model_id": self.model_id,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "organization": self.organization,
            "region": self.region,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "additional_params": self.additional_params
        }