"""
Workflow orchestration for ProcureSense.

This module provides workflow orchestration for agent-to-GPCritic integration
and end-to-end processing pipelines.
"""

from .agent_workflow import AgentWorkflow, WorkflowResult
from .integration_manager import IntegrationManager

__all__ = [
    'AgentWorkflow',
    'WorkflowResult',
    'IntegrationManager'
]