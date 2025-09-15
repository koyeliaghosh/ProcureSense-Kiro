"""
LLM Integration Types and Models
Defines data models for LLM requests, responses, and configuration.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMMessage(BaseModel):
    """Standard message format for LLM communication."""
    role: str = Field(description="Message role (system, user, assistant)")
    content: str = Field(description="Message content")


class LLMRequest(BaseModel):
    """Standard LLM request format."""
    messages: List[LLMMessage] = Field(description="Conversation messages")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, description="Sampling temperature")
    model: Optional[str] = Field(default=None, description="Model name override")


class LLMResponse(BaseModel):
    """Standard LLM response format."""
    content: str = Field(description="Generated response content")
    model: str = Field(description="Model used for generation")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    finish_reason: Optional[str] = Field(default=None, description="Completion reason")
    provider: str = Field(description="LLM provider used")


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    
    def __init__(self, message: str, provider: str, error_type: str = "unknown"):
        self.message = message
        self.provider = provider
        self.error_type = error_type
        super().__init__(f"[{provider}] {error_type}: {message}")


class ConnectionError(LLMError):
    """LLM connection or network error."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "connection_error")


class ModelError(LLMError):
    """LLM model loading or availability error."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "model_error")


class ValidationError(LLMError):
    """LLM request or response validation error."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "validation_error")


class LLMConfig(BaseModel):
    """LLM client configuration."""
    provider: LLMProvider
    host: Optional[str] = None
    model: str
    timeout: int = 30
    max_tokens: int = 4096
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0