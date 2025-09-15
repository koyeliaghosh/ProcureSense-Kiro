"""
Context management data models for layered context architecture
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from src.context.token_counter import TokenCounter

@dataclass
class PolicyContext:
    okrs: List[str]
    prohibited_clauses: List[str]
    required_clauses: List[str]
    budget_thresholds: Dict[str, float]
    compliance_rules: List[str]
    token_budget: int

@dataclass
class GlobalPolicyContext:
    """Global Policy Context (GPC) - 25% Budget, Never Pruned"""
    enterprise_okrs: List[str] = field(default_factory=list)
    prohibited_clauses: List[str] = field(default_factory=list)
    required_clauses: List[str] = field(default_factory=list)
    budget_thresholds: Dict[str, float] = field(default_factory=dict)
    compliance_guardrails: List[str] = field(default_factory=list)
    legal_requirements: List[str] = field(default_factory=list)
    token_count: int = 0
    
    def calculate_tokens(self) -> int:
        """Calculate total tokens for this context layer"""
        total = 0
        total += TokenCounter.count_list_tokens(self.enterprise_okrs, 'text')
        total += TokenCounter.count_list_tokens(self.prohibited_clauses, 'technical')
        total += TokenCounter.count_list_tokens(self.required_clauses, 'technical')
        total += TokenCounter.count_dict_tokens(self.budget_thresholds, 'json')
        total += TokenCounter.count_list_tokens(self.compliance_guardrails, 'technical')
        total += TokenCounter.count_list_tokens(self.legal_requirements, 'technical')
        self.token_count = total
        return total

@dataclass
class DomainStrategyContext:
    """Domain Strategy Context (DSC) - 25% Budget, Summarized"""
    category_playbooks: Dict[str, str] = field(default_factory=dict)
    vendor_guidelines: List[str] = field(default_factory=list)
    market_intelligence: List[str] = field(default_factory=list)
    historical_patterns: List[str] = field(default_factory=list)
    token_count: int = 0
    
    def calculate_tokens(self) -> int:
        """Calculate total tokens for this context layer"""
        total = 0
        total += TokenCounter.count_dict_tokens(self.category_playbooks, 'text')
        total += TokenCounter.count_list_tokens(self.vendor_guidelines, 'text')
        total += TokenCounter.count_list_tokens(self.market_intelligence, 'text')
        total += TokenCounter.count_list_tokens(self.historical_patterns, 'text')
        self.token_count = total
        return total

@dataclass
class TaskSessionContext:
    """Task/Session Context (TSC) - 40% Budget, Rolling Summaries"""
    conversation_turns: List[str] = field(default_factory=list)
    tool_interactions: List[str] = field(default_factory=list)
    session_findings: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    
    def calculate_tokens(self) -> int:
        """Calculate total tokens for this context layer"""
        total = 0
        total += TokenCounter.count_list_tokens(self.conversation_turns, 'text')
        total += TokenCounter.count_list_tokens(self.tool_interactions, 'technical')
        total += TokenCounter.count_list_tokens(self.session_findings, 'text')
        total += TokenCounter.count_dict_tokens(self.user_preferences, 'json')
        self.token_count = total
        return total

@dataclass
class EphemeralToolContext:
    """Ephemeral Tool Context (ETC) - 10% Budget, First Pruned"""
    quotes: List[str] = field(default_factory=list)
    budgets: List[str] = field(default_factory=list)
    vendor_data: List[str] = field(default_factory=list)
    api_responses: List[str] = field(default_factory=list)
    token_count: int = 0
    
    def calculate_tokens(self) -> int:
        """Calculate total tokens for this context layer"""
        total = 0
        total += TokenCounter.count_list_tokens(self.quotes, 'json')
        total += TokenCounter.count_list_tokens(self.budgets, 'json')
        total += TokenCounter.count_list_tokens(self.vendor_data, 'json')
        total += TokenCounter.count_list_tokens(self.api_responses, 'json')
        self.token_count = total
        return total

@dataclass
class LayeredContext:
    gpc: GlobalPolicyContext = field(default_factory=GlobalPolicyContext)
    dsc: DomainStrategyContext = field(default_factory=DomainStrategyContext)
    tsc: TaskSessionContext = field(default_factory=TaskSessionContext)
    etc: EphemeralToolContext = field(default_factory=EphemeralToolContext)
    total_tokens: int = 0
    budget_compliance: bool = True
    
    def calculate_total_tokens(self) -> int:
        """Calculate total tokens across all context layers"""
        total = 0
        total += self.gpc.calculate_tokens()
        total += self.dsc.calculate_tokens()
        total += self.tsc.calculate_tokens()
        total += self.etc.calculate_tokens()
        self.total_tokens = total
        return total
    
    def get_layer_tokens(self) -> Dict[str, int]:
        """Get token count for each layer"""
        return {
            'gpc': self.gpc.token_count,
            'dsc': self.dsc.token_count,
            'tsc': self.tsc.token_count,
            'etc': self.etc.token_count,
            'total': self.total_tokens
        }
    
    def validate_budgets(self, budget_config) -> Dict[str, bool]:
        """Validate each layer against budget constraints"""
        from src.context.budget_config import ContextBudgetConfig
        
        if not isinstance(budget_config, ContextBudgetConfig):
            raise ValueError("budget_config must be ContextBudgetConfig instance")
        
        # Ensure tokens are calculated
        self.calculate_total_tokens()
        
        validation_results = {
            'gpc': budget_config.validate_layer_budget('gpc', self.gpc.token_count),
            'dsc': budget_config.validate_layer_budget('dsc', self.dsc.token_count),
            'tsc': budget_config.validate_layer_budget('tsc', self.tsc.token_count),
            'etc': budget_config.validate_layer_budget('etc', self.etc.token_count),
            'total': self.total_tokens <= budget_config.total_budget
        }
        
        # Update budget compliance status
        self.budget_compliance = all(validation_results.values())
        
        return validation_results