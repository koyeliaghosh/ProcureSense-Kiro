"""
Base data models and type definitions for ProcureSense
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from dataclasses import dataclass

class AgentType(str, Enum):
    NEGOTIATION = "negotiation"
    COMPLIANCE = "compliance"
    FORECAST = "forecast"

class RequestPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    REVISED = "revised"
    FLAGGED = "flagged"

@dataclass
class PolicyViolation:
    violation_type: str
    description: str
    severity: str
    auto_fixable: bool

@dataclass
class ComplianceRule:
    rule_id: str
    description: str
    category: str
    enforcement_level: str  # "warning", "error", "block"

class AgentRequest(BaseModel):
    agent_type: AgentType
    payload: Dict[str, Any]
    session_id: str
    user_context: Optional[str] = None
    priority: RequestPriority = RequestPriority.NORMAL

class AgentResponse(BaseModel):
    agent_response: str
    compliance_status: ComplianceStatus
    policy_violations: List[str] = []
    recommendations: List[str] = []
    confidence_score: float
    context_usage: Dict[str, int]

class ValidationResult(BaseModel):
    is_compliant: bool
    violations: List[PolicyViolation]
    auto_fixes: List[str]
    manual_review_required: bool
    confidence_score: float