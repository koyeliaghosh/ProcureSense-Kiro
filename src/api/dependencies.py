"""
FastAPI dependency injection for ProcureSense components.

Provides dependency injection for agents, GPCritic, and other services.
"""

from functools import lru_cache
from typing import Optional

from ..agents import NegotiationAgent, ComplianceAgent, ForecastAgent
from ..critic import GlobalPolicyCritic
from ..context.gpc_manager import GPCManager
from ..context.context_manager import ContextManager
from ..llm.client_factory import LLMClientFactory
from ..config.settings import get_settings


class AgentService:
    """Service for managing agent instances."""
    
    def __init__(self):
        self.settings = get_settings()
        self._llm_client = None
        self._context_manager = None
        self._gpc_manager = None
        
        # Agent instances (lazy loaded)
        self._negotiation_agent: Optional[NegotiationAgent] = None
        self._compliance_agent: Optional[ComplianceAgent] = None
        self._forecast_agent: Optional[ForecastAgent] = None
    
    def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            try:
                self._llm_client = LLMClientFactory.create_client(self.settings)
            except Exception as e:
                # For now, create a mock client to avoid startup delays
                from ..llm.base_client import BaseLLMClient
                from ..models.llm_types import LLMConfig, LLMProvider
                
                # Create a minimal mock client
                class MockLLMClient(BaseLLMClient):
                    def __init__(self):
                        config = LLMConfig(
                            provider=LLMProvider.OLLAMA,
                            model="mock",
                            host="localhost",
                            timeout=30,
                            max_tokens=4096
                        )
                        super().__init__(config)
                    
                    async def generate(self, request):
                        from ..models.llm_types import LLMResponse
                        return LLMResponse(content="Mock response", usage={"tokens": 100})
                
                self._llm_client = MockLLMClient()
        return self._llm_client
    
    def _get_context_manager(self):
        """Get or create context manager."""
        if self._context_manager is None:
            from ..context.budget_config import ContextBudgetConfig
            budget_config = ContextBudgetConfig(total_budget=1000)
            self._context_manager = ContextManager(budget_config)
        return self._context_manager
    
    def _get_gpc_manager(self):
        """Get or create GPC manager."""
        if self._gpc_manager is None:
            self._gpc_manager = GPCManager()
        return self._gpc_manager
    
    def get_negotiation_agent(self) -> NegotiationAgent:
        """Get negotiation agent instance."""
        if self._negotiation_agent is None:
            self._negotiation_agent = NegotiationAgent(
                context_manager=self._get_context_manager()
            )
        return self._negotiation_agent
    
    def get_compliance_agent(self) -> ComplianceAgent:
        """Get compliance agent instance."""
        if self._compliance_agent is None:
            self._compliance_agent = ComplianceAgent(
                context_manager=self._get_context_manager()
            )
        return self._compliance_agent
    
    def get_forecast_agent(self) -> ForecastAgent:
        """Get forecast agent instance."""
        if self._forecast_agent is None:
            self._forecast_agent = ForecastAgent(
                context_manager=self._get_context_manager()
            )
        return self._forecast_agent


# Global service instances
_agent_service: Optional[AgentService] = None
_gp_critic: Optional[GlobalPolicyCritic] = None
_integration_manager: Optional['IntegrationManager'] = None


@lru_cache()
def get_agent_service() -> AgentService:
    """Dependency for agent service."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@lru_cache()
def get_gp_critic() -> GlobalPolicyCritic:
    """Dependency for Global Policy Critic."""
    global _gp_critic
    if _gp_critic is None:
        # Get dependencies
        agent_service = get_agent_service()
        llm_client = agent_service._get_llm_client()
        gpc_manager = agent_service._get_gpc_manager()
        
        # Create GPCritic
        _gp_critic = GlobalPolicyCritic(
            llm_client=llm_client,
            gpc_manager=gpc_manager,
            dsc_context="Domain strategy context for procurement",
            auto_revision_enabled=True
        )
    return _gp_critic


@lru_cache()
def get_integration_manager():
    """Dependency for Integration Manager."""
    global _integration_manager
    if _integration_manager is None:
        from ..workflow.integration_manager import IntegrationManager
        
        # Get dependencies
        agent_service = get_agent_service()
        gp_critic = get_gp_critic()
        context_manager = agent_service._get_context_manager()
        
        # Create integration manager
        _integration_manager = IntegrationManager(
            negotiation_agent=agent_service.get_negotiation_agent(),
            compliance_agent=agent_service.get_compliance_agent(),
            forecast_agent=agent_service.get_forecast_agent(),
            gp_critic=gp_critic,
            context_manager=context_manager
        )
    return _integration_manager


def reset_dependencies():
    """Reset all dependency instances (useful for testing)."""
    global _agent_service, _gp_critic, _integration_manager
    _agent_service = None
    _gp_critic = None
    _integration_manager = None
    
    # Clear LRU cache
    get_agent_service.cache_clear()
    get_gp_critic.cache_clear()
    get_integration_manager.cache_clear()