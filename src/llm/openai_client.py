"""
OpenAI-Compatible LLM Client Implementation
Supports OpenAI, Anthropic, and other OpenAI-compatible APIs.
"""
import logging
from typing import Dict, Any, Optional

import httpx

from src.models.llm_types import (
    LLMRequest, LLMResponse, LLMConfig, ConnectionError, ModelError, ValidationError
)
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI-compatible LLM client for external APIs."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_base = config.api_base or "https://api.openai.com/v1"
        self.chat_url = f"{self.api_base}/chat/completions"
        self.models_url = f"{self.api_base}/models"
        
        if not config.api_key:
            raise ValidationError("API key is required for OpenAI-compatible clients", config.provider.value)
        
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add provider-specific headers
        if config.provider.value == "anthropic":
            self.headers["anthropic-version"] = "2023-06-01"
    
    async def verify_connection(self) -> bool:
        """Verify connection to OpenAI-compatible API."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                # Try to list models to verify connection and auth
                response = await client.get(self.models_url, headers=self.headers)
                
                if response.status_code == 200:
                    logger.info(f"Successfully connected to {self.config.provider} API")
                    return True
                elif response.status_code == 401:
                    logger.error("API authentication failed - check API key")
                    return False
                else:
                    logger.error(f"API connection failed: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to {self.config.provider} API: {e}")
            return False
    
    async def verify_model(self) -> bool:
        """Verify that the specified model is available."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(self.models_url, headers=self.headers)
                
                if response.status_code != 200:
                    logger.warning(f"Could not verify model availability: HTTP {response.status_code}")
                    # For some providers, model listing might not be available
                    # We'll assume the model is valid and let the actual request fail if not
                    return True
                
                data = response.json()
                available_models = [model["id"] for model in data.get("data", [])]
                
                if self.config.model in available_models:
                    logger.info(f"Model {self.config.model} is available")
                    return True
                else:
                    logger.warning(f"Model {self.config.model} not found in model list")
                    # Some providers don't list all models, so we'll proceed anyway
                    return True
                    
        except Exception as e:
            logger.warning(f"Could not verify model: {e}. Proceeding anyway.")
            return True
    
    async def _make_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to OpenAI-compatible API."""
        payload = {
            "model": request.model or self.config.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or 0.7
        }
        
        # Provider-specific adjustments
        if self.config.provider.value == "anthropic":
            # Anthropic uses different parameter names
            payload["max_tokens"] = payload.pop("max_tokens")
            # Anthropic requires system messages to be separate
            payload = self._adapt_for_anthropic(payload)
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(self.chat_url, json=payload, headers=self.headers)
            
            if response.status_code != 200:
                error_text = response.text
                if response.status_code == 401:
                    raise ConnectionError("Authentication failed - check API key", self.config.provider.value)
                elif response.status_code == 429:
                    raise ConnectionError("Rate limit exceeded", self.config.provider.value)
                elif response.status_code == 400:
                    raise ValidationError(f"Invalid request: {error_text}", self.config.provider.value)
                else:
                    raise ConnectionError(
                        f"API request failed: HTTP {response.status_code} - {error_text}",
                        self.config.provider.value
                    )
            
            data = response.json()
            
            # Handle provider-specific response formats
            if self.config.provider.value == "anthropic":
                return self._parse_anthropic_response(data)
            else:
                return self._parse_openai_response(data)
    
    def _adapt_for_anthropic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt request payload for Anthropic API format."""
        messages = payload["messages"]
        system_message = None
        
        # Extract system message if present
        if messages and messages[0]["role"] == "system":
            system_message = messages[0]["content"]
            messages = messages[1:]
        
        adapted_payload = {
            "model": payload["model"],
            "max_tokens": payload["max_tokens"],
            "temperature": payload["temperature"],
            "messages": messages
        }
        
        if system_message:
            adapted_payload["system"] = system_message
        
        return adapted_payload
    
    def _parse_anthropic_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse Anthropic API response format."""
        if "content" not in data or not data["content"]:
            raise ValidationError("Invalid Anthropic response format", "anthropic")
        
        # Anthropic returns content as a list
        content = data["content"][0]["text"] if isinstance(data["content"], list) else data["content"]
        
        return LLMResponse(
            content=content,
            model=data.get("model", self.config.model),
            tokens_used=data.get("usage", {}).get("total_tokens"),
            finish_reason=data.get("stop_reason"),
            provider="anthropic"
        )
    
    def _parse_openai_response(self, data: Dict[str, Any]) -> LLMResponse:
        """Parse OpenAI API response format."""
        if "choices" not in data or not data["choices"]:
            raise ValidationError("Invalid OpenAI response format", self.config.provider.value)
        
        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.config.model),
            tokens_used=data.get("usage", {}).get("total_tokens"),
            finish_reason=choice.get("finish_reason"),
            provider=self.config.provider.value
        )