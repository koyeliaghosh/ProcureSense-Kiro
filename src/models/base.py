"""
Base data models and type definitions for ProcureSense
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentType(str, Enum):
    """Types of procurement agents."""
    NEGOTIATION = "negotiation"
    COMPLIANCE = "compliance"
    FORECAST = "forecast"


class RequestPriority(str, Enum):
    """Request priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ComplianceStatus(str, Enum):
    """Compliance validation status."""
    COMPLIANT = "compliant"
    REVISED = "revised"
    FLAGGED = "flagged"
    VIOLATION = "violation"


class PolicyViolationType(str, Enum):
    """Types of policy violations."""
    PROHIBITED_CLAUSE = "prohibited_clause"
    MISSING_REQUIRED_CLAUSE = "missing_required_clause"
    BUDGET_THRESHOLD_EXCEEDED = "budget_threshold_exceeded"
    VARIANCE_THRESHOLD_EXCEEDED = "variance_threshold_exceeded"
    COMPLIANCE_RULE_VIOLATION = "compliance_rule_violation"


class AgentRequest(BaseModel):
    """Base request model for all agents."""
    agent_type: AgentType
    payload: Dict[str, Any]
    session_id: str = Field(default_factory=lambda: f"session_{datetime.now().isoformat()}")
    user_context: Optional[str] = None
    priority: RequestPriority = RequestPriority.NORMAL


class PolicyViolation(BaseModel):
    """Represents a policy violation detected by GPCritic."""
    violation_type: PolicyViolationType
    description: str
    severity: str = Field(description="low, medium, high, critical")
    auto_fixable: bool = Field(default=False)
    suggested_fix: Optional[str] = None
    context: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of policy validation."""
    is_compliant: bool
    violations: List[PolicyViolation] = Field(default_factory=list)
    auto_fixes: List[str] = Field(default_factory=list)
    manual_review_required: bool = Field(default=False)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ContextUsage(BaseModel):
    """Token usage breakdown by context layer."""
    gpc_tokens: int = Field(ge=0, description="Global Policy Context tokens used")
    dsc_tokens: int = Field(ge=0, description="Domain Strategy Context tokens used")
    tsc_tokens: int = Field(ge=0, description="Task/Session Context tokens used")
    etc_tokens: int = Field(ge=0, description="Ephemeral Tool Context tokens used")
    total_tokens: int = Field(ge=0, description="Total tokens used")
    budget_compliance: bool = Field(description="Whether usage is within budget")


class AgentResponse(BaseModel):
    """Base response model for all agents."""
    agent_response: str
    compliance_status: ComplianceStatus
    policy_violations: List[PolicyViolation] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    context_usage: ContextUsage
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ComplianceRule(BaseModel):
    """Enterprise compliance rule definition."""
    rule_id: str
    description: str
    rule_type: str = Field(description="clause, budget, variance, etc.")
    pattern: Optional[str] = Field(description="Regex pattern for detection")
    threshold: Optional[float] = Field(description="Numeric threshold if applicable")
    severity: str = Field(description="low, medium, high, critical")
    auto_fix_template: Optional[str] = Field(description="Template for automatic fixes")


class ComplianceReport(BaseModel):
    """Compliance validation report from GPCritic."""
    session_id: str
    agent_type: AgentType
    original_request: Dict[str, Any]
    violations_detected: List[PolicyViolation]
    auto_fixes_applied: List[str]
    manual_review_items: List[str]
    final_compliance_status: ComplianceStatus
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)