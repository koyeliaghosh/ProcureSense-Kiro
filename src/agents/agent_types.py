"""
Agent type definitions and enums for the ProcureSense system
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
from src.models.base_types import AgentType, RequestPriority, ComplianceStatus, PolicyViolation

class AgentRequest(BaseModel):
    """
    Standard request format for all agents in the system
    """
    agent_type: AgentType
    payload: Dict[str, Any] = Field(..., description="Agent-specific request data")
    session_id: str = Field(..., description="Unique session identifier")
    user_context: Optional[str] = Field(None, description="Optional user context information")
    priority: RequestPriority = Field(default=RequestPriority.NORMAL, description="Request priority level")
    
    class Config:
        json_encoders = {
            AgentType: lambda v: v.value,
            RequestPriority: lambda v: v.value
        }

class AgentResponse(BaseModel):
    """
    Standard response format for all agents in the system
    """
    agent_response: str = Field(..., description="Main agent response content")
    compliance_status: ComplianceStatus = Field(..., description="Policy compliance status")
    policy_violations: List[str] = Field(default_factory=list, description="List of policy violations detected")
    recommendations: List[str] = Field(default_factory=list, description="Agent recommendations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the response")
    context_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage by context layer")
    
    class Config:
        json_encoders = {
            ComplianceStatus: lambda v: v.value
        }

@dataclass
class AgentCapabilities:
    """
    Defines the capabilities and constraints of an agent
    """
    agent_type: AgentType
    supported_operations: List[str]
    required_context_layers: List[str]
    max_response_tokens: int
    requires_gpc_validation: bool = True
    supports_auto_revision: bool = True

class ValidationResult(BaseModel):
    """
    Result of agent output validation
    """
    is_compliant: bool = Field(..., description="Whether the output is compliant")
    violations: List[PolicyViolation] = Field(default_factory=list, description="Policy violations found")
    auto_fixes: List[str] = Field(default_factory=list, description="Available automatic fixes")
    manual_review_required: bool = Field(default=False, description="Whether manual review is needed")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Validation confidence score")

class AgentMetrics(BaseModel):
    """
    Performance and usage metrics for agents
    """
    total_requests: int = 0
    successful_responses: int = 0
    policy_violations: int = 0
    auto_revisions: int = 0
    average_response_time: float = 0.0
    average_confidence_score: float = 0.0
    context_token_usage: Dict[str, int] = Field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_responses / self.total_requests) * 100.0
    
    @property
    def violation_rate(self) -> float:
        """Calculate policy violation rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.policy_violations / self.total_requests) * 100.0