"""
Ollama LLM Client Implementation
Supports both native Ollama API and OpenAI-compatible endpoints with fallback.
"""
import json
import logging
from typing import Dict, Any, Optional

import httpx

from src.models.llm_types import (
    LLMRequest, LLMResponse, LLMConfig, ConnectionError, ModelError, ValidationError
)
from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Ollama LLM client with native and OpenAI-compatible API support."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = f"http://{config.host}"
        self.openai_url = f"{self.base_url}/v1/chat/completions"
        self.native_url = f"{self.base_url}/api/chat"
        self.models_url = f"{self.base_url}/api/tags"
        self._use_openai_format = True  # Try OpenAI format first
        
    async def verify_connection(self) -> bool:
        """Verify connection to Ollama server."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                # Try to get model list to verify connection
                response = await client.get(self.models_url)
                if response.status_code == 200:
                    logger.info(f"Successfully connected to Ollama at {self.config.host}")
                    return True
                else:
                    logger.error(f"Ollama connection failed: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def verify_model(self) -> bool:
        """Verify that the specified model is available in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(self.models_url)
                if response.status_code != 200:
                    return False
                
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]
                
                if self.config.model in available_models:
                    logger.info(f"Model {self.config.model} is available")
                    return True
                else:
                    logger.warning(f"Model {self.config.model} not found. Available: {available_models}")
                    # Try to pull the model
                    return await self._pull_model()
                    
        except Exception as e:
            logger.error(f"Failed to verify model: {e}")
            return False
    
    async def _pull_model(self) -> bool:
        """Attempt to pull the model if it's not available."""
        try:
            pull_url = f"{self.base_url}/api/pull"
            async with httpx.AsyncClient(timeout=300) as client:  # Longer timeout for model pull
                logger.info(f"Attempting to pull model {self.config.model}...")
                response = await client.post(
                    pull_url,
                    json={"name": self.config.model}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully pulled model {self.config.model}")
                    return True
                else:
                    logger.error(f"Failed to pull model: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False
    
    async def _make_request(self, request: LLMRequest) -> LLMResponse:
        """Make request to Ollama with fallback between OpenAI and native formats."""
        # Try OpenAI-compatible format first, then fallback to native
        if self._use_openai_format:
            try:
                return await self._make_openai_request(request)
            except Exception as e:
                logger.warning(f"OpenAI format failed, falling back to native: {e}")
                self._use_openai_format = False
                return await self._make_native_request(request)
        else:
            return await self._make_native_request(request)
    
    async def _make_openai_request(self, request: LLMRequest) -> LLMResponse:
        """Make request using OpenAI-compatible format."""
        payload = {
            "model": request.model or self.config.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature or 0.7,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(self.openai_url, json=payload)
            
            if response.status_code != 200:
                raise ConnectionError(
                    f"Ollama OpenAI API request failed: HTTP {response.status_code} - {response.text}",
                    "ollama"
                )
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise ValidationError("Invalid OpenAI response format", "ollama")
            
            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.config.model),
                tokens_used=data.get("usage", {}).get("total_tokens"),
                finish_reason=choice.get("finish_reason"),
                provider="ollama"
            )
    
    async def _make_native_request(self, request: LLMRequest) -> LLMResponse:
        """Make request using Ollama native format."""
        # Convert messages to Ollama native format
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        payload = {
            "model": request.model or self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or 0.7
            }
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(self.native_url, json=payload)
            
            if response.status_code != 200:
                raise ConnectionError(
                    f"Ollama native API request failed: HTTP {response.status_code} - {response.text}",
                    "ollama"
                )
            
            data = response.json()
            
            if "message" not in data:
                raise ValidationError("Invalid Ollama native response format", "ollama")
            
            return LLMResponse(
                content=data["message"]["content"],
                model=data.get("model", self.config.model),
                tokens_used=data.get("eval_count"),  # Ollama native token count field
                finish_reason=data.get("done_reason"),
                provider="ollama"
            )