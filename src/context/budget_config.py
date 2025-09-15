"""
Context budget configuration and validation
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class ContextBudgetConfig:
    """Configuration for context layer token budgets"""
    
    # Total context budget
    total_budget: int
    
    # Budget percentages for each layer
    gpc_percentage: float = 0.25  # Global Policy Context - 25%
    dsc_percentage: float = 0.25  # Domain Strategy Context - 25%
    tsc_percentage: float = 0.40  # Task/Session Context - 40%
    etc_percentage: float = 0.10  # Ephemeral Tool Context - 10%
    
    def __post_init__(self):
        """Validate budget percentages sum to 1.0"""
        total_percentage = (
            self.gpc_percentage + 
            self.dsc_percentage + 
            self.tsc_percentage + 
            self.etc_percentage
        )
        
        if abs(total_percentage - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(f"Budget percentages must sum to 1.0, got {total_percentage}")
    
    @property
    def gpc_budget(self) -> int:
        """Get GPC token budget"""
        return int(self.total_budget * self.gpc_percentage)
    
    @property
    def dsc_budget(self) -> int:
        """Get DSC token budget"""
        return int(self.total_budget * self.dsc_percentage)
    
    @property
    def tsc_budget(self) -> int:
        """Get TSC token budget"""
        return int(self.total_budget * self.tsc_percentage)
    
    @property
    def etc_budget(self) -> int:
        """Get ETC token budget"""
        return int(self.total_budget * self.etc_percentage)
    
    def get_all_budgets(self) -> Dict[str, int]:
        """Get all layer budgets as dictionary"""
        return {
            'gpc': self.gpc_budget,
            'dsc': self.dsc_budget,
            'tsc': self.tsc_budget,
            'etc': self.etc_budget,
            'total': self.total_budget
        }
    
    def validate_layer_budget(self, layer: str, actual_tokens: int) -> bool:
        """Validate if actual tokens are within layer budget"""
        budgets = {
            'gpc': self.gpc_budget,
            'dsc': self.dsc_budget,
            'tsc': self.tsc_budget,
            'etc': self.etc_budget
        }
        
        if layer not in budgets:
            raise ValueError(f"Unknown layer: {layer}")
            
        return actual_tokens <= budgets[layer]