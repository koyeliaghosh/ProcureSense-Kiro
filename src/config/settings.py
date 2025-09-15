"""
Environment configuration loading for ProcureSense
"""
from pydantic_settings import BaseSettings
from typing import List, Dict
from functools import lru_cache

class Settings(BaseSettings):
    # FastAPI Server Configuration
    server_host: str = "localhost"
    server_port: int = 8000
    
    # LLM Configuration
    llm_provider: str = "ollama"  # ollama, openai, anthropic
    ollama_host: str = "localhost:11434"
    ollama_model: str = "llama3.1:8b"  # Default to smaller model
    ollama_timeout: int = 30
    ollama_max_tokens: int = 4096
    
    # OpenAI Configuration (if using OpenAI provider)
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    
    # Context Budget Configuration (tokens)
    context_budget_total: int = 2000  # Adjusted for smaller models
    context_budget_gpc: int = 500     # 25% for Global Policy Context
    context_budget_dsc: int = 500     # 25% for Domain Strategy Context
    context_budget_tsc: int = 800     # 40% for Task/Session Context
    context_budget_etc: int = 200     # 10% for Ephemeral Tool Context
    
    # Enterprise Policy Configuration
    prohibited_clauses: str = "liability_waiver,indemnification,unlimited_liability"
    required_clauses: str = "warranty,data_protection,termination_rights"
    budget_thresholds: str = "software:50000,hardware:100000,services:25000"
    
    # Compliance Configuration
    variance_threshold: float = 0.15  # 15% budget variance threshold
    auto_revision_enabled: bool = True
    audit_logging_enabled: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file
    
    @property
    def prohibited_clauses_list(self) -> List[str]:
        return [clause.strip() for clause in self.prohibited_clauses.split(",")]
    
    @property
    def required_clauses_list(self) -> List[str]:
        return [clause.strip() for clause in self.required_clauses.split(",")]
    
    @property
    def budget_thresholds_dict(self) -> Dict[str, float]:
        thresholds = {}
        try:
            for item in self.budget_thresholds.split(","):
                if ":" in item:
                    category, threshold = item.strip().split(":", 1)
                    # Clean up any extra characters
                    threshold = threshold.strip().rstrip('}').rstrip()
                    thresholds[category.strip()] = float(threshold)
        except (ValueError, AttributeError) as e:
            # Return default thresholds if parsing fails
            print(f"Warning: Failed to parse budget thresholds: {e}")
            thresholds = {
                "software": 50000.0,
                "hardware": 100000.0,
                "services": 25000.0
            }
        return thresholds

@lru_cache()
def get_settings() -> Settings:
    return Settings()