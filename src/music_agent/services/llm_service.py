"""
General LLM service for the Music Agent.

Provides a reusable interface for LLM operations throughout the application,
including structured data extraction, text generation, and analysis.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Union, Type
from enum import Enum
from dataclasses import dataclass

import openai
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class LLMModel(Enum):
    """Available LLM models."""
    GPT5 = "gpt-5"
    GPT5_NANO = "gpt-5-nano"
    GPT4O = "gpt-4o"
    GPT4O_MINI = "gpt-4o-mini"
    GPT35_TURBO = "gpt-3.5-turbo"


class ResponseFormat(Enum):
    """Response format types."""
    TEXT = "text"
    JSON = "json_object"
    STRUCTURED = "structured"


@dataclass
class LLMResponse:
    """Response from LLM service."""
    content: Union[str, Dict[str, Any]]
    model: str
    tokens_used: int
    finish_reason: str
    
    @property
    def is_json(self) -> bool:
        """Check if response is JSON."""
        return isinstance(self.content, dict)
    
    def get_json(self) -> Dict[str, Any]:
        """Get JSON content or parse if string."""
        if isinstance(self.content, dict):
            return self.content
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:
            return {}


class LLMService:
    """
    General LLM service for the application.
    
    Features:
    - Multiple model support
    - Structured output with Pydantic
    - Automatic retries with exponential backoff
    - Token usage tracking
    - Conversation history management
    """
    
    def __init__(self, model: Optional[LLMModel] = None):
        """
        Initialize LLM service.
        
        Args:
            model: Default model to use (defaults to config)
        """
        config = get_config()
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(
            api_key=config.openai.api_key,
            base_url=config.openai.base_url,
            organization=config.openai.organization
        )
        
        # Set default model - use gpt-5 as requested
        self.default_model = model or LLMModel.GPT5
        
        # Default parameters
        self.default_temperature = config.openai.temperature
        self.default_max_tokens = config.openai.max_tokens
        
        # Token tracking
        self.total_tokens_used = 0
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.RateLimitError))
    )
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[LLMModel] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Get completion from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            response_format: Expected response format
            messages: Full conversation history (overrides prompt)
            **kwargs: Additional OpenAI parameters
        
        Returns:
            LLM response with content and metadata
        """
        # Build messages
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
        
        # Set parameters
        model_name = (model or self.default_model).value
        temperature = temperature or self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens
        
        # Handle response format
        api_params = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        if response_format == ResponseFormat.JSON:
            api_params["response_format"] = {"type": "json_object"}
            # Add JSON instruction to last message if not present
            if "json" not in messages[-1]["content"].lower():
                messages[-1]["content"] += "\n\nReturn your response as valid JSON."
        
        try:
            # Make API call
            response = await self.client.chat.completions.create(**api_params)
            
            # Parse response
            choice = response.choices[0]
            content = choice.message.content
            
            # Track tokens
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
            else:
                tokens_used = 0
            
            # Parse JSON if expected
            if response_format == ResponseFormat.JSON:
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON response, returning as text")
            
            return LLMResponse(
                content=content,
                model=model_name,
                tokens_used=tokens_used,
                finish_reason=choice.finish_reason
            )
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise
    
    async def extract_structured_data(
        self,
        text: str,
        schema: Type[BaseModel],
        extraction_prompt: Optional[str] = None,
        model: Optional[LLMModel] = None,
        **kwargs
    ) -> BaseModel:
        """
        Extract structured data from text using a Pydantic schema.
        
        Args:
            text: Input text to extract from
            schema: Pydantic model defining the structure
            extraction_prompt: Custom extraction instructions
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            Populated Pydantic model instance
        """
        # Build schema description
        schema_json = schema.schema()
        
        # Build extraction prompt
        system_prompt = """You are a data extraction expert. 
        Extract structured information from the provided text according to the schema.
        Be precise and only extract information that is clearly present."""
        
        if extraction_prompt:
            system_prompt += f"\n\nAdditional instructions: {extraction_prompt}"
        
        user_prompt = f"""Extract data from this text according to the schema:

Schema:
{json.dumps(schema_json, indent=2)}

Text:
{text}

Return valid JSON matching the schema."""
        
        # Get completion
        response = await self.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            response_format=ResponseFormat.JSON,
            temperature=0.1,  # Low temperature for extraction
            **kwargs
        )
        
        # Parse into schema
        try:
            if isinstance(response.content, dict):
                return schema(**response.content)
            else:
                data = json.loads(response.content)
                return schema(**data)
        except Exception as e:
            logger.error(f"Failed to parse structured data: {e}")
            raise
    
    async def analyze(
        self,
        data: Union[str, Dict, List],
        analysis_type: str,
        instructions: str,
        model: Optional[LLMModel] = None,
        return_json: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Analyze data with specific instructions.
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis (e.g., "sentiment", "summary", "pattern")
            instructions: Specific analysis instructions
            model: Model to use
            return_json: Whether to return JSON response
            **kwargs: Additional parameters
        
        Returns:
            Analysis result as text or structured data
        """
        system_prompt = f"""You are performing {analysis_type} analysis.
        Follow the instructions precisely and provide clear, actionable insights."""
        
        # Convert data to string if needed
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = str(data)
        
        user_prompt = f"""{instructions}

Data to analyze:
{data_str}"""
        
        response = await self.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            response_format=ResponseFormat.JSON if return_json else ResponseFormat.TEXT,
            **kwargs
        )
        
        return response.content
    
    async def classify(
        self,
        text: str,
        categories: List[str],
        model: Optional[LLMModel] = None,
        multi_label: bool = False,
        confidence_scores: bool = False,
        **kwargs
    ) -> Union[str, List[str], Dict[str, float]]:
        """
        Classify text into categories.
        
        Args:
            text: Text to classify
            categories: Available categories
            model: Model to use
            multi_label: Allow multiple categories
            confidence_scores: Return confidence scores
            **kwargs: Additional parameters
        
        Returns:
            Category, list of categories, or dict with confidence scores
        """
        system_prompt = """You are a classification expert.
        Classify the provided text into the given categories."""
        
        if confidence_scores:
            instruction = "Return confidence scores (0-1) for each category as JSON."
            response_format = ResponseFormat.JSON
        elif multi_label:
            instruction = "Return all applicable categories as a JSON array."
            response_format = ResponseFormat.JSON
        else:
            instruction = "Return the single most appropriate category."
            response_format = ResponseFormat.TEXT
        
        user_prompt = f"""{instruction}

Categories: {', '.join(categories)}

Text to classify:
{text}"""
        
        response = await self.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
            response_format=response_format,
            temperature=0.1,
            **kwargs
        )
        
        if confidence_scores:
            # Ensure all categories are present
            scores = response.get_json()
            for category in categories:
                if category not in scores:
                    scores[category] = 0.0
            return scores
        elif multi_label:
            return response.get_json()
        else:
            return response.content.strip()
    
    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def moderate(self, text: str) -> Dict[str, Any]:
        """
        Check content for policy violations.
        
        Args:
            text: Text to moderate
        
        Returns:
            Moderation results
        """
        try:
            response = await self.client.moderations.create(input=text)
            return response.results[0].dict()
        except Exception as e:
            logger.error(f"Moderation failed: {e}")
            return {"error": str(e)}
    
    def get_token_usage(self) -> int:
        """Get total tokens used in this session."""
        return self.total_tokens_used
    
    def reset_token_usage(self):
        """Reset token usage counter."""
        self.total_tokens_used = 0


# Singleton instance for the application
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


# Convenience functions for common operations
async def quick_complete(prompt: str, **kwargs) -> str:
    """Quick text completion."""
    service = get_llm_service()
    response = await service.complete(prompt, **kwargs)
    return response.content if isinstance(response.content, str) else json.dumps(response.content)


async def quick_extract(text: str, schema: Type[BaseModel], **kwargs) -> BaseModel:
    """Quick structured extraction."""
    service = get_llm_service()
    return await service.extract_structured_data(text, schema, **kwargs)


async def quick_analyze(data: Any, analysis_type: str, instructions: str, **kwargs) -> Any:
    """Quick data analysis."""
    service = get_llm_service()
    return await service.analyze(data, analysis_type, instructions, **kwargs)