"""
Model management and initialization.
"""

import logging
from typing import Optional, Dict, Any
from strands import Agent
from strands.models.openai import OpenAIModel

from .model_config import ModelConfig, ModelProvider

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model initialization and configuration."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the AI model based on configuration.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.config.provider == ModelProvider.OPENAI:
                self.model = self._create_openai_model()
            elif self.config.provider == ModelProvider.BEDROCK:
                self.model = self._create_bedrock_model()
            else:
                raise ValueError(f"Unsupported model provider: {self.config.provider}")
            
            self._initialized = True
            logger.info(f"Initialized {self.config.provider.value} model: {self.config.model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            return False
    
    def _create_openai_model(self):
        """Create OpenAI model instance."""
        if not self.config.api_key:
            raise RuntimeError("OpenAI API key is required")
        
        client_args = {
            "api_key": self.config.api_key,
        }
        
        if self.config.base_url:
            client_args["base_url"] = self.config.base_url
        
        if self.config.organization:
            client_args["organization"] = self.config.organization
        
        model_params = {
            "temperature": self.config.temperature,
            "max_completion_tokens": self.config.max_tokens,
        }
        model_params.update(self.config.additional_params)
        
        return OpenAIModel(
            client_args=client_args,
            model_id=self.config.model_id,
            params=model_params
        )
    
    def _create_bedrock_model(self):
        """Create Bedrock model instance."""
        # TODO: Implement Bedrock model creation
        raise NotImplementedError("Bedrock models not yet implemented")
    
    def create_agent(self, tools: list, system_prompt: str) -> Optional[Agent]:
        """
        Create an agent with the initialized model.
        
        Args:
            tools: List of tools to provide to the agent
            system_prompt: System prompt for the agent
        
        Returns:
            Agent instance or None if failed
        """
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            agent = Agent(
                model=self.model,
                tools=tools,
                system_prompt=system_prompt
            )
            
            logger.info(f"Created agent with {len(tools)} tools")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.config.provider.value,
            "model_id": self.config.model_id,
            "initialized": self._initialized,
            "base_url": self.config.base_url,
            "organization": self.config.organization,
            "region": self.config.region,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }