"""
Request and response models for specific agent types
"""
from typing import Optional
from pydantic import BaseModel, Field


class NegotiationRequest(BaseModel):
    """Request model for Negotiation Agent."""
    vendor: str = Field(description="Vendor name or identifier")
    target_discount_pct: float = Field(ge=0.0, le=1.0, description="Target discount percentage (0.0-1.0)")
    category: str = Field(description="Procurement category (software, hardware, services, etc.)")
    context: Optional[str] = Field(default=None, description="Additional context or requirements")


class ComplianceRequest(BaseModel):
    """Request model for Compliance Agent."""
    clause: str = Field(description="Contract clause text to analyze")
    contract_type: Optional[str] = Field(default=None, description="Type of contract (SaaS, hardware, services)")
    risk_tolerance: Optional[str] = Field(default="medium", description="Risk tolerance level (low, medium, high)")


class ForecastRequest(BaseModel):
    """Request model for Forecast Agent."""
    category: str = Field(description="Procurement category")
    quarter: str = Field(description="Target quarter (Q1, Q2, Q3, Q4)")
    planned_spend: float = Field(ge=0.0, description="Planned spending amount")
    current_budget: Optional[float] = Field(default=None, description="Current allocated budget")