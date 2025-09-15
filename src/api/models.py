"""
Pydantic models for FastAPI request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ComplianceStatus(str, Enum):
    """Compliance status values."""
    COMPLIANT = "compliant"
    REVISED = "revised"
    FLAGGED = "flagged"


class NegotiationRequest(BaseModel):
    """Request model for negotiation agent endpoint."""
    vendor: str = Field(..., description="Vendor name", min_length=1, max_length=100)
    target_discount_pct: float = Field(..., description="Target discount percentage (0-100)", ge=0, le=100)
    category: str = Field(..., description="Procurement category", min_length=1, max_length=50)
    context: Optional[str] = Field(None, description="Additional context", max_length=1000)
    
    @validator('target_discount_pct')
    def validate_discount(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Discount percentage must be between 0 and 100')
        # Convert percentage to decimal for internal use
        return v / 100.0 if v > 1 else v


class ComplianceRequest(BaseModel):
    """Request model for compliance agent endpoint."""
    clause: str = Field(..., description="Contract clause to analyze", min_length=1, max_length=5000)
    contract_type: Optional[str] = Field(None, description="Type of contract", max_length=50)
    risk_tolerance: Optional[str] = Field(None, description="Risk tolerance level", max_length=20)
    
    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if v is not None and v.lower() not in ['low', 'medium', 'high']:
            raise ValueError('Risk tolerance must be low, medium, or high')
        return v


class ForecastRequest(BaseModel):
    """Request model for forecast agent endpoint."""
    category: str = Field(..., description="Spending category", min_length=1, max_length=50)
    quarter: str = Field(..., description="Quarter (e.g., Q1 2024)", min_length=1, max_length=20)
    planned_spend: float = Field(..., description="Planned spending amount", ge=0)
    current_budget: Optional[float] = Field(None, description="Current budget allocation", ge=0)
    
    @validator('quarter')
    def validate_quarter(cls, v):
        # Basic quarter format validation
        if not v or len(v.strip()) == 0:
            raise ValueError('Quarter cannot be empty')
        return v.strip()


class ContextUsage(BaseModel):
    """Context usage information."""
    gpc_tokens: int = Field(..., description="Global Policy Context tokens used")
    dsc_tokens: int = Field(..., description="Domain Strategy Context tokens used")
    tsc_tokens: int = Field(..., description="Task/Session Context tokens used")
    etc_tokens: int = Field(..., description="Ephemeral Tool Context tokens used")
    total_tokens: int = Field(..., description="Total tokens used")


class PolicyViolationInfo(BaseModel):
    """Policy violation information."""
    violation_type: str = Field(..., description="Type of policy violation")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Description of the violation")
    auto_fixable: bool = Field(..., description="Whether violation can be auto-fixed")


class AgentResponse(BaseModel):
    """Standard response model for all agent endpoints."""
    agent_response: str = Field(..., description="Agent's response content")
    compliance_status: ComplianceStatus = Field(..., description="Compliance validation status")
    policy_violations: List[PolicyViolationInfo] = Field(default_factory=list, description="Detected policy violations")
    recommendations: List[str] = Field(default_factory=list, description="Agent recommendations")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0)", ge=0.0, le=1.0)
    context_usage: ContextUsage = Field(..., description="Context token usage information")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    request_id: str = Field(..., description="Unique request identifier")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier if available")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Current timestamp")
    components: Dict[str, str] = Field(..., description="Component health status")


class AgentStatusResponse(BaseModel):
    """Agent status response model."""
    agent_type: str = Field(..., description="Type of agent")
    status: str = Field(..., description="Agent status")
    last_request: Optional[str] = Field(None, description="Last request timestamp")
    total_requests: int = Field(..., description="Total requests processed")
    average_response_time_ms: float = Field(..., description="Average response time")