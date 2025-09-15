"""
Agent workflow orchestration for ProcureSense.

Provides end-to-end workflow management for agent processing with
GPCritic validation and compliance reporting.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..agents.base_agent import BaseAgent
from ..critic.gp_critic import GlobalPolicyCritic
from ..critic.critic_types import CriticResult, RevisionAction
from ..agents.agent_types import AgentResponse
from ..context.context_manager import ContextManager


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""
    agent_processing_time_ms: int
    critic_processing_time_ms: int
    total_processing_time_ms: int
    context_tokens_used: Dict[str, int]
    policy_checks_performed: int
    violations_detected: int
    auto_revisions_applied: int


@dataclass
class WorkflowResult:
    """Result of complete agent-to-GPCritic workflow."""
    request_id: str
    agent_type: str
    original_request: Dict[str, Any]
    agent_response: AgentResponse
    critic_result: CriticResult
    final_output: str
    compliance_status: str
    metrics: WorkflowMetrics
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class AgentWorkflow:
    """
    Orchestrates the complete agent-to-GPCritic workflow.
    
    Manages the end-to-end processing pipeline from agent request
    through GPCritic validation to final compliant output.
    """
    
    def __init__(
        self,
        gp_critic: GlobalPolicyCritic,
        context_manager: Optional[ContextManager] = None
    ):
        """
        Initialize the agent workflow.
        
        Args:
            gp_critic: Global Policy Critic for validation
            context_manager: Context manager for token tracking
        """
        self.gp_critic = gp_critic
        if context_manager is None:
            from ..context.budget_config import ContextBudgetConfig
            budget_config = ContextBudgetConfig(total_budget=1000)
            self.context_manager = ContextManager(budget_config)
        else:
            self.context_manager = context_manager
        
        # Workflow statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_violations = 0
        self.auto_revisions = 0
    
    async def execute_workflow(
        self,
        agent: BaseAgent,
        request_data: Dict[str, Any],
        agent_type: str,
        request_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Execute the complete agent-to-GPCritic workflow.
        
        Args:
            agent: The agent to process the request
            request_data: Request data for the agent
            agent_type: Type of agent (negotiation, compliance, forecast)
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            WorkflowResult with complete processing results
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        workflow_start_time = time.time()
        self.total_requests += 1
        
        try:
            # Step 1: Process request with agent
            agent_start_time = time.time()
            agent_response = agent.process_request(request_data)
            agent_processing_time = int((time.time() - agent_start_time) * 1000)
            
            # Step 2: Validate with GPCritic
            critic_start_time = time.time()
            critic_result = self.gp_critic.validate_output(
                agent_output=agent_response.agent_response,
                original_request=request_data,
                agent_type=agent_type
            )
            critic_processing_time = int((time.time() - critic_start_time) * 1000)
            
            # Step 3: Determine final output and compliance status
            final_output = critic_result.revised_output or agent_response.agent_response
            compliance_status = self._determine_compliance_status(critic_result)
            
            # Step 4: Collect metrics
            metrics = self._collect_metrics(
                agent_processing_time,
                critic_processing_time,
                int((time.time() - workflow_start_time) * 1000),
                agent_response,
                critic_result
            )
            
            # Step 5: Update statistics
            self._update_statistics(critic_result)
            self.successful_requests += 1
            
            return WorkflowResult(
                request_id=request_id,
                agent_type=agent_type,
                original_request=request_data,
                agent_response=agent_response,
                critic_result=critic_result,
                final_output=final_output,
                compliance_status=compliance_status,
                metrics=metrics,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            self.failed_requests += 1
            
            # Create error result
            error_metrics = WorkflowMetrics(
                agent_processing_time_ms=0,
                critic_processing_time_ms=0,
                total_processing_time_ms=int((time.time() - workflow_start_time) * 1000),
                context_tokens_used={},
                policy_checks_performed=0,
                violations_detected=0,
                auto_revisions_applied=0
            )
            
            return WorkflowResult(
                request_id=request_id,
                agent_type=agent_type,
                original_request=request_data,
                agent_response=None,
                critic_result=None,
                final_output="",
                compliance_status="ERROR",
                metrics=error_metrics,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    def _determine_compliance_status(self, critic_result: CriticResult) -> str:
        """Determine compliance status from critic result."""
        if len(critic_result.violations) == 0:
            return "COMPLIANT"
        elif critic_result.action_taken == RevisionAction.AUTO_REVISED:
            return "REVISED"
        elif critic_result.action_taken == RevisionAction.MANUAL_REVIEW_REQUIRED:
            return "FLAGGED"
        else:
            return "NON_COMPLIANT"
    
    def _collect_metrics(
        self,
        agent_time: int,
        critic_time: int,
        total_time: int,
        agent_response: AgentResponse,
        critic_result: CriticResult
    ) -> WorkflowMetrics:
        """Collect workflow execution metrics."""
        
        # Get context usage from agent response
        context_usage = getattr(agent_response, 'context_usage', {})
        
        # Calculate policy checks and violations
        policy_checks = len(self.gp_critic._get_policy_checks_performed())
        violations = len(critic_result.violations)
        auto_revisions = 1 if critic_result.revised_output else 0
        
        return WorkflowMetrics(
            agent_processing_time_ms=agent_time,
            critic_processing_time_ms=critic_time,
            total_processing_time_ms=total_time,
            context_tokens_used=context_usage,
            policy_checks_performed=policy_checks,
            violations_detected=violations,
            auto_revisions_applied=auto_revisions
        )
    
    def _update_statistics(self, critic_result: CriticResult):
        """Update workflow statistics."""
        self.total_violations += len(critic_result.violations)
        if critic_result.revised_output:
            self.auto_revisions += 1
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate_pct": round(success_rate, 2),
            "total_violations_detected": self.total_violations,
            "auto_revisions_applied": self.auto_revisions,
            "average_violations_per_request": round(self.total_violations / max(self.total_requests, 1), 2)
        }
    
    def reset_statistics(self):
        """Reset workflow statistics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_violations = 0
        self.auto_revisions = 0