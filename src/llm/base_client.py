"""
Base LLM Client Interface
Defines the abstract interface for LLM providers with connection management and retry logic.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

from src.models.llm_types import LLMRequest, LLMResponse, LLMConfig, ConnectionError

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients with retry and connection management."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._connection_verified = False
        
    @abstractmethod
    async def _make_request(self, request: LLMRequest) -> LLMResponse:
        """Make the actual LLM request. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def verify_connection(self) -> bool:
        """Verify connection to LLM provider. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def verify_model(self) -> bool:
        """Verify model availability. Must be implemented by subclasses."""
        pass
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate response with retry logic and connection management.
        
        Args:
            request: LLM request with messages and parameters
            
        Returns:
            LLM response with generated content
            
        Raises:
            ConnectionError: If connection fails after retries
            ModelError: If model is not available
            ValidationError: If request/response validation fails
        """
        # Verify connection if not already done
        if not self._connection_verified:
            if not await self.verify_connection():
                raise ConnectionError(
                    f"Failed to connect to {self.config.provider} at {self.config.host}",
                    self.config.provider.value
                )
            self._connection_verified = True
        
        # Retry logic with exponential backoff
        last_exception = None
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._make_request(request)
                logger.info(f"LLM request successful on attempt {attempt + 1}")
                return response
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM request failed (attempt {attempt + 1}/{self.config.retry_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"LLM request failed after {self.config.retry_attempts} attempts: {e}")
        
        # If we get here, all retries failed
        if isinstance(last_exception, ConnectionError):
            raise last_exception
        else:
            raise ConnectionError(
                f"Failed to generate response after {self.config.retry_attempts} attempts: {last_exception}",
                self.config.provider.value
            )
    
    def reset_connection(self):
        """Reset connection verification status to force reconnection."""
        self._connection_verified = False