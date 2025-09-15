"""
LLM Client Factory
Creates appropriate LLM clients based on configuration and provider type.
"""
import logging
from typing import Optional

from src.config.settings import Settings
from src.models.llm_types import LLMProvider, LLMConfig, ValidationError
from .base_client import BaseLLMClient
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory for creating LLM clients based on provider configuration."""
    
    @staticmethod
    def create_client(settings: Settings) -> BaseLLMClient:
        """
        Create an LLM client based on settings configuration.
        
        Args:
            settings: Application settings with LLM configuration
            
        Returns:
            Configured LLM client instance
            
        Raises:
            ValidationError: If provider is unsupported or configuration is invalid
        """
        try:
            provider = LLMProvider(settings.llm_provider.lower())
        except ValueError:
            raise ValidationError(
                f"Unsupported LLM provider: {settings.llm_provider}. "
                f"Supported providers: {[p.value for p in LLMProvider]}",
                settings.llm_provider
            )
        
        config = LLMClientFactory._build_config(settings, provider)
        
        if provider == LLMProvider.OLLAMA:
            return OllamaClient(config)
        elif provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            return OpenAIClient(config)
        else:
            raise ValidationError(f"No client implementation for provider: {provider.value}", provider.value)
    
    @staticmethod
    def _build_config(settings: Settings, provider: LLMProvider) -> LLMConfig:
        """Build LLM configuration from settings."""
        if provider == LLMProvider.OLLAMA:
            return LLMConfig(
                provider=provider,
                host=settings.ollama_host,
                model=settings.ollama_model,
                timeout=settings.ollama_timeout,
                max_tokens=settings.ollama_max_tokens,
                retry_attempts=3,
                retry_delay=1.0
            )
        
        elif provider == LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValidationError("OpenAI API key is required", "openai")
            
            return LLMConfig(
                provider=provider,
                model=settings.openai_model or "gpt-4",
                timeout=settings.ollama_timeout,  # Reuse timeout setting
                max_tokens=settings.ollama_max_tokens,  # Reuse max_tokens setting
                api_key=settings.openai_api_key,
                api_base=settings.openai_api_base,
                retry_attempts=3,
                retry_delay=1.0
            )
        
        elif provider == LLMProvider.ANTHROPIC:
            if not settings.openai_api_key:  # Reuse API key field for Anthropic
                raise ValidationError("Anthropic API key is required", "anthropic")
            
            return LLMConfig(
                provider=provider,
                model=settings.openai_model or "claude-3-sonnet-20240229",
                timeout=settings.ollama_timeout,
                max_tokens=settings.ollama_max_tokens,
                api_key=settings.openai_api_key,
                api_base=settings.openai_api_base or "https://api.anthropic.com",
                retry_attempts=3,
                retry_delay=1.0
            )
        
        else:
            raise ValidationError(f"Unknown provider configuration: {provider.value}", provider.value)


class LLMClientManager:
    """Singleton manager for LLM client instances with connection verification."""
    
    _instance: Optional['LLMClientManager'] = None
    _client: Optional[BaseLLMClient] = None
    
    def __new__(cls) -> 'LLMClientManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_client(self, settings: Settings) -> BaseLLMClient:
        """
        Get or create LLM client with connection verification.
        
        Args:
            settings: Application settings
            
        Returns:
            Verified LLM client instance
            
        Raises:
            ConnectionError: If client cannot connect or verify model
        """
        if self._client is None:
            self._client = LLMClientFactory.create_client(settings)
            
            # Verify connection and model availability
            logger.info(f"Initializing {settings.llm_provider} client...")
            
            if not await self._client.verify_connection():
                raise ValidationError(
                    f"Failed to connect to {settings.llm_provider}",
                    settings.llm_provider
                )
            
            if not await self._client.verify_model():
                raise ValidationError(
                    f"Model {self._client.config.model} is not available",
                    settings.llm_provider
                )
            
            logger.info(f"LLM client initialized successfully: {settings.llm_provider}")
        
        return self._client
    
    def reset_client(self):
        """Reset client instance to force reconnection."""
        if self._client:
            self._client.reset_connection()
        self._client = None