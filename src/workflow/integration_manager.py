"""
Integration manager for ProcureSense agent-to-GPCritic workflows.

Provides centralized management of agent workflows with comprehensive
monitoring, reporting, and compliance tracking.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .agent_workflow import AgentWorkflow, WorkflowResult
from ..agents import NegotiationAgent, ComplianceAgent, ForecastAgent
from ..critic.gp_critic import GlobalPolicyCritic
from ..context.context_manager import ContextManager


@dataclass
class IntegrationMetrics:
    """Comprehensive integration metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    compliance_violations: int = 0
    auto_revisions: int = 0
    manual_reviews_required: int = 0
    
    # Per-agent metrics
    negotiation_requests: int = 0
    compliance_requests: int = 0
    forecast_requests: int = 0
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    average_agent_time_ms: float = 0.0
    average_critic_time_ms: float = 0.0
    
    # Context usage metrics
    total_tokens_used: int = 0
    gpc_tokens_used: int = 0
    dsc_tokens_used: int = 0
    
    # Time tracking
    start_time: datetime = field(default_factory=datetime.now)
    last_request_time: Optional[datetime] = None


class IntegrationManager:
    """
    Manages integration between agents and GPCritic with comprehensive monitoring.
    
    Provides centralized workflow orchestration, metrics collection,
    and compliance reporting for the entire ProcureSense system.
    """
    
    def __init__(
        self,
        negotiation_agent: NegotiationAgent,
        compliance_agent: ComplianceAgent,
        forecast_agent: ForecastAgent,
        gp_critic: GlobalPolicyCritic,
        context_manager: ContextManager
    ):
        """
        Initialize the integration manager.
        
        Args:
            negotiation_agent: Negotiation agent instance
            compliance_agent: Compliance agent instance
            forecast_agent: Forecast agent instance
            gp_critic: Global Policy Critic instance
            context_manager: Context manager instance
        """
        self.agents = {
            "negotiation": negotiation_agent,
            "compliance": compliance_agent,
            "forecast": forecast_agent
        }
        
        self.gp_critic = gp_critic
        self.context_manager = context_manager
        
        # Create workflow orchestrator
        self.workflow = AgentWorkflow(gp_critic, context_manager)
        
        # Metrics and monitoring
        self.metrics = IntegrationMetrics()
        self.recent_results: List[WorkflowResult] = []
        self.max_recent_results = 100
        
        # Configuration
        self.enable_detailed_logging = True
        self.enable_metrics_collection = True
    
    async def process_request(
        self,
        agent_type: str,
        request_data: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Process a request through the complete agent-to-GPCritic workflow.
        
        Args:
            agent_type: Type of agent (negotiation, compliance, forecast)
            request_data: Request data for processing
            request_id: Optional request ID
            
        Returns:
            WorkflowResult with complete processing results
            
        Raises:
            ValueError: If agent_type is not supported
        """
        if agent_type not in self.agents:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        agent = self.agents[agent_type]
        
        # Execute workflow
        result = await self.workflow.execute_workflow(
            agent=agent,
            request_data=request_data,
            agent_type=agent_type,
            request_id=request_id
        )
        
        # Update metrics
        if self.enable_metrics_collection:
            self._update_metrics(result)
        
        # Store recent result
        self._store_recent_result(result)
        
        # Log if enabled
        if self.enable_detailed_logging:
            self._log_workflow_result(result)
        
        return result
    
    async def process_batch_requests(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[WorkflowResult]:
        """
        Process multiple requests concurrently.
        
        Args:
            requests: List of request dictionaries with 'agent_type' and 'data' keys
            
        Returns:
            List of WorkflowResults
        """
        tasks = []
        
        for request in requests:
            agent_type = request.get("agent_type")
            request_data = request.get("data", {})
            request_id = request.get("request_id")
            
            task = self.process_request(agent_type, request_data, request_id)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get comprehensive integration metrics."""
        workflow_stats = self.workflow.get_workflow_statistics()
        
        # Calculate rates and percentages
        total_requests = self.metrics.total_requests
        success_rate = (self.metrics.successful_requests / total_requests * 100) if total_requests > 0 else 0
        violation_rate = (self.metrics.compliance_violations / total_requests * 100) if total_requests > 0 else 0
        revision_rate = (self.metrics.auto_revisions / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate uptime
        uptime = datetime.now() - self.metrics.start_time
        
        return {
            "overview": {
                "total_requests": total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate_pct": round(success_rate, 2),
                "uptime_hours": round(uptime.total_seconds() / 3600, 2)
            },
            "compliance": {
                "violations_detected": self.metrics.compliance_violations,
                "auto_revisions_applied": self.metrics.auto_revisions,
                "manual_reviews_required": self.metrics.manual_reviews_required,
                "violation_rate_pct": round(violation_rate, 2),
                "revision_rate_pct": round(revision_rate, 2)
            },
            "performance": {
                "average_processing_time_ms": round(self.metrics.average_processing_time_ms, 2),
                "average_agent_time_ms": round(self.metrics.average_agent_time_ms, 2),
                "average_critic_time_ms": round(self.metrics.average_critic_time_ms, 2)
            },
            "agents": {
                "negotiation_requests": self.metrics.negotiation_requests,
                "compliance_requests": self.metrics.compliance_requests,
                "forecast_requests": self.metrics.forecast_requests
            },
            "context_usage": {
                "total_tokens_used": self.metrics.total_tokens_used,
                "gpc_tokens_used": self.metrics.gpc_tokens_used,
                "dsc_tokens_used": self.metrics.dsc_tokens_used
            },
            "workflow_stats": workflow_stats
        }
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow results."""
        recent = self.recent_results[-limit:] if limit > 0 else self.recent_results
        
        return [
            {
                "request_id": result.request_id,
                "agent_type": result.agent_type,
                "compliance_status": result.compliance_status,
                "success": result.success,
                "processing_time_ms": result.metrics.total_processing_time_ms,
                "violations_detected": result.metrics.violations_detected,
                "auto_revisions": result.metrics.auto_revisions_applied,
                "timestamp": result.timestamp.isoformat()
            }
            for result in recent
        ]
    
    def get_compliance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate compliance report for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent results by time
        recent_results = [
            r for r in self.recent_results 
            if r.timestamp >= cutoff_time
        ]
        
        if not recent_results:
            return {"message": "No data available for the specified time period"}
        
        # Calculate compliance statistics
        total_requests = len(recent_results)
        compliant_requests = len([r for r in recent_results if r.compliance_status == "COMPLIANT"])
        revised_requests = len([r for r in recent_results if r.compliance_status == "REVISED"])
        flagged_requests = len([r for r in recent_results if r.compliance_status == "FLAGGED"])
        
        total_violations = sum(r.metrics.violations_detected for r in recent_results)
        total_revisions = sum(r.metrics.auto_revisions_applied for r in recent_results)
        
        return {
            "time_period_hours": hours,
            "total_requests": total_requests,
            "compliance_breakdown": {
                "compliant": compliant_requests,
                "revised": revised_requests,
                "flagged": flagged_requests,
                "compliant_pct": round(compliant_requests / total_requests * 100, 2),
                "revised_pct": round(revised_requests / total_requests * 100, 2),
                "flagged_pct": round(flagged_requests / total_requests * 100, 2)
            },
            "violations": {
                "total_violations": total_violations,
                "average_per_request": round(total_violations / total_requests, 2),
                "auto_revisions": total_revisions,
                "revision_success_rate": round(total_revisions / max(total_violations, 1) * 100, 2)
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics and statistics."""
        self.metrics = IntegrationMetrics()
        self.recent_results.clear()
        self.workflow.reset_statistics()
    
    def _update_metrics(self, result: WorkflowResult):
        """Update integration metrics with workflow result."""
        self.metrics.total_requests += 1
        self.metrics.last_request_time = result.timestamp
        
        if result.success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            return  # Don't process failed requests further
        
        # Update agent-specific counters
        if result.agent_type == "negotiation":
            self.metrics.negotiation_requests += 1
        elif result.agent_type == "compliance":
            self.metrics.compliance_requests += 1
        elif result.agent_type == "forecast":
            self.metrics.forecast_requests += 1
        
        # Update compliance metrics
        self.metrics.compliance_violations += result.metrics.violations_detected
        self.metrics.auto_revisions += result.metrics.auto_revisions_applied
        
        if result.compliance_status == "FLAGGED":
            self.metrics.manual_reviews_required += 1
        
        # Update performance metrics (running average)
        total = self.metrics.successful_requests
        self.metrics.average_processing_time_ms = self._update_running_average(
            self.metrics.average_processing_time_ms,
            result.metrics.total_processing_time_ms,
            total
        )
        self.metrics.average_agent_time_ms = self._update_running_average(
            self.metrics.average_agent_time_ms,
            result.metrics.agent_processing_time_ms,
            total
        )
        self.metrics.average_critic_time_ms = self._update_running_average(
            self.metrics.average_critic_time_ms,
            result.metrics.critic_processing_time_ms,
            total
        )
        
        # Update context usage
        context_usage = result.metrics.context_tokens_used
        self.metrics.total_tokens_used += sum(context_usage.values())
        self.metrics.gpc_tokens_used += context_usage.get("gpc", 0)
        self.metrics.dsc_tokens_used += context_usage.get("dsc", 0)
    
    def _update_running_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Update running average with new value."""
        if count <= 1:
            return new_value
        return ((current_avg * (count - 1)) + new_value) / count
    
    def _store_recent_result(self, result: WorkflowResult):
        """Store result in recent results list."""
        self.recent_results.append(result)
        
        # Trim to max size
        if len(self.recent_results) > self.max_recent_results:
            self.recent_results = self.recent_results[-self.max_recent_results:]
    
    def _log_workflow_result(self, result: WorkflowResult):
        """Log workflow result for monitoring."""
        status = "SUCCESS" if result.success else "FAILED"
        
        print(f"[{result.timestamp.isoformat()}] {status} - {result.agent_type.upper()} "
              f"Request {result.request_id[:8]}... - "
              f"Compliance: {result.compliance_status} - "
              f"Time: {result.metrics.total_processing_time_ms}ms")
        
        if result.metrics.violations_detected > 0:
            print(f"  └─ Violations: {result.metrics.violations_detected}, "
                  f"Auto-revisions: {result.metrics.auto_revisions_applied}")
        
        if not result.success:
            print(f"  └─ Error: {result.error_message}")