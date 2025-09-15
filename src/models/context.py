"""
Context management data models for layered, budgeted context architecture
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class GlobalPolicyContext(BaseModel):
    """Global Policy Context (GPC) - 25% budget, never pruned."""
    okrs: List[str] = Field(description="Enterprise OKRs and strategic objectives")
    prohibited_clauses: List[str] = Field(description="Prohibited contract clauses")
    required_clauses: List[str] = Field(description="Required contract clauses")
    budget_thresholds: Dict[str, float] = Field(description="Budget thresholds by category")
    compliance_rules: List[str] = Field(description="Compliance guardrails and legal requirements")
    token_budget: int = Field(description="Allocated token budget for GPC")
    is_pinned: bool = Field(default=True, description="GPC is never pruned")


class DomainStrategyContext(BaseModel):
    """Domain Strategy Context (DSC) - 25% budget, summarized under pressure."""
    category_playbooks: Dict[str, str] = Field(description="Category-specific procurement playbooks")
    vendor_guidelines: Dict[str, str] = Field(description="Vendor relationship guidelines")
    market_intelligence: List[str] = Field(description="Market intelligence summaries")
    negotiation_patterns: List[str] = Field(description="Historical negotiation patterns")
    token_budget: int = Field(description="Allocated token budget for DSC")
    last_summarized: Optional[datetime] = Field(description="Last summarization timestamp")


class TaskSessionContext(BaseModel):
    """Task/Session Context (TSC) - 40% budget, rolling summaries."""
    conversation_turns: List[Dict[str, str]] = Field(description="Recent conversation with recency bias")
    tool_interactions: List[Dict[str, str]] = Field(description="Tool interaction snippets and results")
    session_findings: List[str] = Field(description="Session findings and decisions")
    user_preferences: Dict[str, str] = Field(description="User preferences and context")
    token_budget: int = Field(description="Allocated token budget for TSC")
    summary_threshold: int = Field(default=10, description="Number of turns before summarization")


class EphemeralToolContext(BaseModel):
    """Ephemeral Tool Context (ETC) - 10% budget, first to be pruned."""
    tool_payloads: List[Dict[str, str]] = Field(description="One-shot payloads (quotes, budgets, vendor data)")
    calculation_results: List[Dict[str, str]] = Field(description="Temporary calculation results")
    api_responses: List[Dict[str, str]] = Field(description="External API responses")
    market_data: List[Dict[str, str]] = Field(description="Real-time market data")
    token_budget: int = Field(description="Allocated token budget for ETC")
    ttl_seconds: int = Field(default=3600, description="Time-to-live for ephemeral data")


class LayeredContext(BaseModel):
    """Complete layered context with budget enforcement."""
    gpc: GlobalPolicyContext
    dsc: DomainStrategyContext
    tsc: TaskSessionContext
    etc: EphemeralToolContext
    total_tokens: int = Field(description="Total tokens across all layers")
    budget_compliance: bool = Field(description="Whether context fits within budget")
    pruning_applied: List[str] = Field(default_factory=list, description="Pruning operations applied")
    build_timestamp: datetime = Field(default_factory=datetime.now)


class ContextConfig(BaseModel):
    """Configuration for context management."""
    total_budget: int = Field(description="Total token budget")
    gpc_budget: int = Field(description="GPC token budget (25%)")
    dsc_budget: int = Field(description="DSC token budget (25%)")
    tsc_budget: int = Field(description="TSC token budget (40%)")
    etc_budget: int = Field(description="ETC token budget (10%)")
    
    def validate_budgets(self) -> bool:
        """Validate that budgets sum to total."""
        allocated = self.gpc_budget + self.dsc_budget + self.tsc_budget + self.etc_budget
        return allocated == self.total_budget