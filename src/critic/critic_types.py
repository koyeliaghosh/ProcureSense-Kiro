"""
Data types for the Global Policy Critic system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class ViolationType(Enum):
    """Types of policy violations that can be detected."""
    BUDGET_EXCEEDED = "budget_exceeded"
    PROHIBITED_CLAUSE = "prohibited_clause"
    MISSING_WARRANTY = "missing_warranty"
    UNAUTHORIZED_DISCOUNT = "unauthorized_discount"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SECURITY_RISK = "security_risk"
    APPROVAL_REQUIRED = "approval_required"
    INVALID_TERMS = "invalid_terms"


class RevisionAction(Enum):
    """Actions that can be taken to fix policy violations."""
    AUTO_REVISED = "auto_revised"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    REJECTED = "rejected"
    APPROVED = "approved"


@dataclass
class PolicyViolation:
    """Represents a detected policy violation."""
    violation_type: ViolationType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    location: str  # Where in the output the violation was found
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    policy_reference: Optional[str] = None


@dataclass
class CriticResult:
    """Result of GPCritic validation and revision."""
    original_output: str
    revised_output: Optional[str]
    violations: List[PolicyViolation]
    action_taken: RevisionAction
    compliance_score: float  # 0.0 to 1.0
    revision_notes: List[str]
    processing_time_ms: int
    timestamp: datetime


@dataclass
class ComplianceReport:
    """Comprehensive compliance report for audit purposes."""
    request_id: str
    agent_type: str
    original_request: Dict[str, Any]
    critic_result: CriticResult
    policy_checks_performed: List[str]
    gpc_version: str
    dsc_version: str
    final_compliance_status: str  # COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW
    audit_trail: List[Dict[str, Any]]
    generated_at: datetime