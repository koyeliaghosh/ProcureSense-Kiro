"""
Global Policy Context (GPC) Manager
Handles loading, validation, and management of enterprise policies
"""
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import logging
from src.models.context_types import GlobalPolicyContext
from src.models.base_types import PolicyViolation, ComplianceRule
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

@dataclass
class PolicyValidationResult:
    """Result of policy validation check"""
    is_valid: bool
    violations: List[PolicyViolation]
    compliance_score: float
    flagged_clauses: List[str]

class GPCManager:
    """
    Global Policy Context Manager
    Loads enterprise policies from configuration and provides validation utilities
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._gpc_context: Optional[GlobalPolicyContext] = None
        self._compliance_rules: List[ComplianceRule] = []
        self._load_policies()
    
    def _load_policies(self) -> None:
        """Load enterprise policies from configuration"""
        try:
            # Load basic policy data from settings
            prohibited_clauses = self.settings.prohibited_clauses_list
            required_clauses = self.settings.required_clauses_list
            budget_thresholds = self.settings.budget_thresholds_dict
            
            # Create enterprise OKRs (these would typically come from config or database)
            enterprise_okrs = self._load_enterprise_okrs()
            
            # Create compliance guardrails
            compliance_guardrails = self._load_compliance_guardrails()
            
            # Create legal requirements
            legal_requirements = self._load_legal_requirements()
            
            # Create GPC context
            self._gpc_context = GlobalPolicyContext(
                enterprise_okrs=enterprise_okrs,
                prohibited_clauses=prohibited_clauses,
                required_clauses=required_clauses,
                budget_thresholds=budget_thresholds,
                compliance_guardrails=compliance_guardrails,
                legal_requirements=legal_requirements
            )
            
            # Calculate tokens for the context
            self._gpc_context.calculate_tokens()
            
            # Load compliance rules
            self._compliance_rules = self._load_compliance_rules()
            
            logger.info(f"GPC loaded successfully with {self._gpc_context.token_count} tokens")
            
        except Exception as e:
            logger.error(f"Failed to load GPC policies: {e}")
            raise
    
    def _load_enterprise_okrs(self) -> List[str]:
        """Load enterprise OKRs (Objectives and Key Results)"""
        # In a real implementation, these would come from configuration or database
        return [
            "Reduce procurement costs by 15% while maintaining quality standards",
            "Achieve 95% contract compliance across all vendor agreements",
            "Implement sustainable procurement practices for 80% of suppliers",
            "Maintain vendor relationship satisfaction score above 4.2/5.0",
            "Ensure 100% data protection compliance in all vendor contracts"
        ]
    
    def _load_compliance_guardrails(self) -> List[str]:
        """Load compliance guardrails"""
        return [
            "All contracts must include data protection clauses per GDPR requirements",
            "Liability caps must not exceed 2x annual contract value",
            "Termination clauses must allow 30-day notice period minimum",
            "Warranty periods must be minimum 12 months for hardware, 6 months for software",
            "Payment terms must not exceed 60 days from invoice receipt"
        ]
    
    def _load_legal_requirements(self) -> List[str]:
        """Load legal requirements"""
        return [
            "Contracts must comply with local jurisdiction laws",
            "Intellectual property rights must be clearly defined",
            "Confidentiality agreements must be mutual and time-bound",
            "Force majeure clauses must include pandemic and cyber security events",
            "Dispute resolution must specify arbitration process and jurisdiction"
        ]
    
    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load compliance rules for validation"""
        return [
            ComplianceRule(
                rule_id="CR001",
                description="Prohibited clauses must not appear in contracts",
                category="prohibited_content",
                enforcement_level="error"
            ),
            ComplianceRule(
                rule_id="CR002", 
                description="Required clauses must be present in all contracts",
                category="required_content",
                enforcement_level="error"
            ),
            ComplianceRule(
                rule_id="CR003",
                description="Budget thresholds must not be exceeded without approval",
                category="budget_compliance",
                enforcement_level="warning"
            ),
            ComplianceRule(
                rule_id="CR004",
                description="Liability waivers are strictly prohibited",
                category="liability_protection",
                enforcement_level="block"
            ),
            ComplianceRule(
                rule_id="CR005",
                description="Data protection clauses are mandatory for all vendors",
                category="data_privacy",
                enforcement_level="error"
            )
        ]
    
    def get_gpc_context(self) -> GlobalPolicyContext:
        """Get the loaded GPC context"""
        if self._gpc_context is None:
            raise RuntimeError("GPC context not loaded. Call _load_policies() first.")
        return self._gpc_context
    
    def get_compliance_rules(self) -> List[ComplianceRule]:
        """Get the loaded compliance rules"""
        return self._compliance_rules.copy()
    
    def validate_contract_text(self, contract_text: str) -> PolicyValidationResult:
        """
        Validate contract text against enterprise policies
        
        Args:
            contract_text: The contract text to validate
            
        Returns:
            PolicyValidationResult with validation details
        """
        violations = []
        flagged_clauses = []
        
        # Convert to lowercase for case-insensitive matching
        text_lower = contract_text.lower()
        
        # Check for prohibited clauses
        for prohibited_clause in self._gpc_context.prohibited_clauses:
            if prohibited_clause.lower() in text_lower:
                violations.append(PolicyViolation(
                    violation_type="prohibited_clause",
                    description=f"Contract contains prohibited clause: {prohibited_clause}",
                    severity="high",
                    auto_fixable=True
                ))
                flagged_clauses.append(prohibited_clause)
        
        # Check for missing required clauses
        for required_clause in self._gpc_context.required_clauses:
            if required_clause.lower() not in text_lower:
                violations.append(PolicyViolation(
                    violation_type="missing_required_clause",
                    description=f"Contract missing required clause: {required_clause}",
                    severity="high", 
                    auto_fixable=True
                ))
        
        # Calculate compliance score (0.0 to 1.0)
        total_checks = len(self._gpc_context.prohibited_clauses) + len(self._gpc_context.required_clauses)
        violation_count = len(violations)
        compliance_score = max(0.0, (total_checks - violation_count) / total_checks) if total_checks > 0 else 1.0
        
        return PolicyValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            compliance_score=compliance_score,
            flagged_clauses=flagged_clauses
        )
    
    def validate_budget_request(self, category: str, amount: float) -> PolicyValidationResult:
        """
        Validate budget request against thresholds
        
        Args:
            category: Budget category (e.g., 'software', 'hardware', 'services')
            amount: Requested amount
            
        Returns:
            PolicyValidationResult with validation details
        """
        violations = []
        
        # Check if category has a threshold
        if category in self._gpc_context.budget_thresholds:
            threshold = self._gpc_context.budget_thresholds[category]
            
            if amount > threshold:
                violations.append(PolicyViolation(
                    violation_type="budget_threshold_exceeded",
                    description=f"Budget request ${amount:,.2f} exceeds threshold ${threshold:,.2f} for category '{category}'",
                    severity="medium",
                    auto_fixable=False
                ))
        
        # Calculate compliance score
        compliance_score = 1.0 if len(violations) == 0 else 0.5
        
        return PolicyValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            compliance_score=compliance_score,
            flagged_clauses=[]
        )
    
    def get_policy_summary(self) -> Dict[str, any]:
        """Get a summary of loaded policies"""
        if self._gpc_context is None:
            return {"error": "GPC context not loaded"}
        
        return {
            "enterprise_okrs_count": len(self._gpc_context.enterprise_okrs),
            "prohibited_clauses": self._gpc_context.prohibited_clauses,
            "required_clauses": self._gpc_context.required_clauses,
            "budget_thresholds": self._gpc_context.budget_thresholds,
            "compliance_guardrails_count": len(self._gpc_context.compliance_guardrails),
            "legal_requirements_count": len(self._gpc_context.legal_requirements),
            "total_tokens": self._gpc_context.token_count,
            "compliance_rules_count": len(self._compliance_rules)
        }
    
    def reload_policies(self) -> None:
        """Reload policies from configuration"""
        logger.info("Reloading GPC policies from configuration")
        self._load_policies()
    
    def check_clause_compliance(self, clause_text: str) -> List[PolicyViolation]:
        """
        Check a specific clause for policy violations
        
        Args:
            clause_text: The clause text to check
            
        Returns:
            List of policy violations found
        """
        violations = []
        clause_lower = clause_text.lower()
        
        # Check against prohibited clauses
        for prohibited in self._gpc_context.prohibited_clauses:
            if prohibited.lower() in clause_lower:
                violations.append(PolicyViolation(
                    violation_type="prohibited_clause",
                    description=f"Clause contains prohibited content: {prohibited}",
                    severity="high",
                    auto_fixable=True
                ))
        
        return violations
    
    def suggest_required_clauses(self, existing_clauses: List[str]) -> List[str]:
        """
        Suggest required clauses that are missing from existing clauses
        
        Args:
            existing_clauses: List of existing clause texts
            
        Returns:
            List of required clauses that should be added
        """
        existing_text = " ".join(existing_clauses).lower()
        missing_clauses = []
        
        for required in self._gpc_context.required_clauses:
            if required.lower() not in existing_text:
                missing_clauses.append(required)
        
        return missing_clauses
    
    def validate_comprehensive(self, text: str, category: Optional[str] = None, 
                             amount: Optional[float] = None) -> PolicyValidationResult:
        """
        Perform comprehensive policy validation combining contract text and budget validation
        
        Args:
            text: Contract text to validate
            category: Optional spending category for budget validation
            amount: Optional spending amount for budget validation
            
        Returns:
            PolicyValidationResult: Combined validation results
        """
        # Start with contract text validation
        text_result = self.validate_contract_text(text)
        
        # If budget parameters provided, also validate budget
        if category and amount is not None:
            budget_result = self.validate_budget_request(category, amount)
            
            # Combine results
            combined_violations = text_result.violations + budget_result.violations
            combined_flagged = text_result.flagged_clauses + budget_result.flagged_clauses
            combined_valid = text_result.is_valid and budget_result.is_valid
            combined_score = min(text_result.compliance_score, budget_result.compliance_score)
            
            return PolicyValidationResult(
                is_valid=combined_valid,
                violations=combined_violations,
                compliance_score=combined_score,
                flagged_clauses=combined_flagged
            )
        
        return text_result