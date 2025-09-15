"""
Compliance Agent for ProcureSense procurement automation system

Handles contract clause analysis, risk assessment, and automatic compliance
violation detection and rewriting.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
import re
from dataclasses import dataclass
from enum import Enum

from src.agents.base_agent import BaseAgent
from src.agents.agent_types import AgentRequest, AgentCapabilities
from src.models.base_types import AgentType, PolicyViolation
from src.context.context_manager import ContextManager
from src.llm.client_factory import LLMClientFactory

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    """Risk levels for compliance assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ViolationType(str, Enum):
    """Types of compliance violations"""
    PROHIBITED_CLAUSE = "prohibited_clause"
    MISSING_REQUIRED = "missing_required"
    RISKY_TERMS = "risky_terms"
    LEGAL_RISK = "legal_risk"
    REGULATORY_RISK = "regulatory_risk"

@dataclass
class ComplianceViolation:
    """Detailed compliance violation information"""
    violation_type: ViolationType
    clause_text: str
    risk_level: RiskLevel
    description: str
    suggested_rewrite: Optional[str] = None
    auto_fixable: bool = False
    legal_reference: Optional[str] = None

@dataclass
class ComplianceRequest:
    """Structured compliance request data"""
    clause: str
    contract_context: Optional[str] = None
    contract_type: Optional[str] = None
    risk_tolerance: Optional[str] = None
    jurisdiction: Optional[str] = None

@dataclass
class ComplianceResult:
    """Structured compliance analysis result"""
    original_clause: str
    risk_assessment: str
    risk_level: RiskLevel
    violations: List[ComplianceViolation]
    compliant_rewrite: Optional[str]
    flagged_terms: List[str]
    recommendations: List[str]
    confidence_score: float
    requires_legal_review: bool

class ComplianceAgent(BaseAgent):
    """
    Compliance Agent for contract clause analysis and risk assessment
    
    Capabilities:
    - Analyze contract clauses for legal and compliance risks
    - Detect prohibited clauses and risky terms
    - Automatically rewrite non-compliant clauses
    - Provide compliant alternatives and recommendations
    - Flag terms requiring legal review
    """
    
    def __init__(self, context_manager: ContextManager):
        """
        Initialize Compliance Agent
        
        Args:
            context_manager: Context management system
        """
        super().__init__(context_manager, AgentType.COMPLIANCE)
        
        # Get settings and create LLM client
        from src.config.settings import get_settings
        settings = get_settings()
        self.llm_client = LLMClientFactory.create_client(settings)
        
        # Risk assessment patterns
        self.high_risk_patterns = [
            r'\bunlimited\s+liability\b',
            r'\bindemnif(y|ication)\b',
            r'\bwaiv(e|er)\s+of\s+liability\b',
            r'\bhold\s+harmless\b',
            r'\bno\s+warranty\b',
            r'\bas\s+is\b',
            r'\bexclusive\s+remedy\b',
            r'\bconsequential\s+damages\b'
        ]
        
        # Required clause patterns
        self.required_patterns = [
            r'\bwarranty\b',
            r'\bdata\s+protection\b',
            r'\btermination\b',
            r'\bconfidentiality\b',
            r'\bintellectual\s+property\b'
        ]
        
        logger.info("Initialized Compliance Agent with risk assessment patterns")
    
    def _define_capabilities(self) -> AgentCapabilities:
        """Define compliance agent capabilities"""
        return AgentCapabilities(
            agent_type=AgentType.COMPLIANCE,
            supported_operations=[
                "analyze_clause_risk",
                "detect_violations",
                "rewrite_clauses",
                "assess_compliance",
                "flag_risky_terms",
                "provide_alternatives"
            ],
            required_context_layers=["gpc", "dsc"],
            max_response_tokens=2500,
            requires_gpc_validation=True,
            supports_auto_revision=True
        )
    
    def _validate_request_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate compliance request payload
        
        Args:
            payload: Request payload to validate
            
        Returns:
            bool: True if payload is valid
        """
        # Check required field
        if "clause" not in payload:
            logger.error("Missing required field: clause")
            return False
        
        # Validate clause content
        clause = payload.get("clause")
        if not isinstance(clause, str) or not clause.strip():
            logger.error("Clause must be a non-empty string")
            return False
        
        # Validate optional fields
        contract_context = payload.get("contract_context")
        if contract_context is not None and not isinstance(contract_context, str):
            logger.error("Contract context must be a string")
            return False
        
        return True
    
    def _process_agent_request(self, request: AgentRequest, context) -> str:
        """
        Process compliance request and generate response
        
        Args:
            request: Compliance request
            context: Layered context for the request
            
        Returns:
            str: Generated compliance analysis response
        """
        # Parse request into structured format
        compliance_request = self._parse_compliance_request(request.payload)
        
        # Perform compliance analysis
        result = self._analyze_compliance(compliance_request, context)
        
        # Format response
        response = self._format_compliance_response(result, compliance_request)
        
        logger.info(f"Generated compliance analysis for clause with {len(result.violations)} violations "
                   f"and {result.risk_level.value} risk level")
        
        return response
    
    def _parse_compliance_request(self, payload: Dict[str, Any]) -> ComplianceRequest:
        """Parse request payload into structured compliance request"""
        return ComplianceRequest(
            clause=payload["clause"],
            contract_context=payload.get("contract_context"),
            contract_type=payload.get("contract_type"),
            risk_tolerance=payload.get("risk_tolerance"),
            jurisdiction=payload.get("jurisdiction")
        )
    
    def _analyze_compliance(self, request: ComplianceRequest, context) -> ComplianceResult:
        """
        Perform comprehensive compliance analysis
        
        Args:
            request: Structured compliance request
            context: Layered context
            
        Returns:
            ComplianceResult: Generated compliance analysis result
        """
        # Perform initial risk assessment
        violations = self._detect_violations(request.clause, context)
        risk_level = self._assess_risk_level(violations)
        flagged_terms = self._identify_flagged_terms(request.clause)
        
        # Generate LLM-based analysis
        try:
            llm_analysis = self._generate_llm_analysis(request, context, violations)
            
            # Parse LLM response
            risk_assessment, compliant_rewrite, recommendations = self._parse_llm_analysis(llm_analysis)
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            # Use fallback analysis
            risk_assessment, compliant_rewrite, recommendations = self._generate_fallback_analysis(request, violations)
        
        # Determine if legal review is required
        requires_legal_review = self._requires_legal_review(violations, risk_level)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(violations, risk_level)
        
        return ComplianceResult(
            original_clause=request.clause,
            risk_assessment=risk_assessment,
            risk_level=risk_level,
            violations=violations,
            compliant_rewrite=compliant_rewrite,
            flagged_terms=flagged_terms,
            recommendations=recommendations,
            confidence_score=confidence_score,
            requires_legal_review=requires_legal_review
        )
    
    def _detect_violations(self, clause: str, context) -> List[ComplianceViolation]:
        """
        Detect compliance violations in the clause
        
        Args:
            clause: Contract clause text
            context: Layered context with policies
            
        Returns:
            List of detected violations
        """
        violations = []
        clause_lower = clause.lower()
        
        # Get enterprise policies from context
        try:
            gpc = context.gpc
            prohibited_clauses = gpc.prohibited_clauses
            required_clauses = gpc.required_clauses
        except Exception as e:
            logger.warning(f"Could not access GPC context: {str(e)}")
            prohibited_clauses = ["liability_waiver", "indemnification", "unlimited_liability"]
            required_clauses = ["warranty", "data_protection", "termination_rights"]
        
        # Check for prohibited clauses
        for prohibited in prohibited_clauses:
            if self._contains_prohibited_clause(clause_lower, prohibited):
                violation = ComplianceViolation(
                    violation_type=ViolationType.PROHIBITED_CLAUSE,
                    clause_text=clause,
                    risk_level=RiskLevel.HIGH,
                    description=f"Contains prohibited clause: {prohibited}",
                    suggested_rewrite=self._suggest_prohibited_rewrite(clause, prohibited),
                    auto_fixable=True,
                    legal_reference=f"Enterprise policy prohibits {prohibited} clauses"
                )
                violations.append(violation)
        
        # Check for high-risk patterns
        for pattern in self.high_risk_patterns:
            if re.search(pattern, clause_lower, re.IGNORECASE):
                violation = ComplianceViolation(
                    violation_type=ViolationType.RISKY_TERMS,
                    clause_text=clause,
                    risk_level=RiskLevel.HIGH,
                    description=f"Contains high-risk pattern: {pattern}",
                    suggested_rewrite=self._suggest_risk_rewrite(clause, pattern),
                    auto_fixable=True,
                    legal_reference="High-risk legal terms detected"
                )
                violations.append(violation)
        
        # Check for missing required clauses (in context of full contract)
        if len(clause) > 200:  # Only check for longer clauses that might be full sections
            for required in required_clauses:
                if not self._contains_required_clause(clause_lower, required):
                    violation = ComplianceViolation(
                        violation_type=ViolationType.MISSING_REQUIRED,
                        clause_text=clause,
                        risk_level=RiskLevel.MEDIUM,
                        description=f"Missing required clause: {required}",
                        suggested_rewrite=self._suggest_required_addition(clause, required),
                        auto_fixable=True,
                        legal_reference=f"Enterprise policy requires {required} clauses"
                    )
                    violations.append(violation)
        
        return violations
    
    def _contains_prohibited_clause(self, clause_lower: str, prohibited: str) -> bool:
        """Check if clause contains prohibited terms"""
        prohibited_variations = {
            "liability_waiver": ["liability waiver", "waiver of liability", "waive liability", "waives all liability", "waives liability"],
            "indemnification": ["indemnification", "indemnify", "hold harmless"],
            "unlimited_liability": ["unlimited liability", "unlimited damages", "no liability cap"]
        }
        
        variations = prohibited_variations.get(prohibited, [prohibited.replace("_", " ")])
        return any(variation in clause_lower for variation in variations)
    
    def _contains_required_clause(self, clause_lower: str, required: str) -> bool:
        """Check if clause contains required terms"""
        required_variations = {
            "warranty": ["warranty", "warranties", "guarantee"],
            "data_protection": ["data protection", "privacy", "gdpr", "data security"],
            "termination_rights": ["termination", "terminate", "end agreement"]
        }
        
        variations = required_variations.get(required, [required.replace("_", " ")])
        return any(variation in clause_lower for variation in variations)
    
    def _assess_risk_level(self, violations: List[ComplianceViolation]) -> RiskLevel:
        """Assess overall risk level based on violations"""
        if not violations:
            return RiskLevel.LOW
        
        # Check for critical violations
        if any(v.risk_level == RiskLevel.CRITICAL for v in violations):
            return RiskLevel.CRITICAL
        
        # Check for high-risk violations
        high_risk_count = sum(1 for v in violations if v.risk_level == RiskLevel.HIGH)
        if high_risk_count >= 2:
            return RiskLevel.CRITICAL
        elif high_risk_count >= 1:
            return RiskLevel.HIGH
        
        # Check for medium-risk violations
        medium_risk_count = sum(1 for v in violations if v.risk_level == RiskLevel.MEDIUM)
        if medium_risk_count >= 3:
            return RiskLevel.HIGH
        elif medium_risk_count >= 1:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _identify_flagged_terms(self, clause: str) -> List[str]:
        """Identify specific terms that should be flagged for review"""
        flagged = []
        clause_lower = clause.lower()
        
        # Terms that require attention
        flag_patterns = [
            ("exclusive", r'\bexclusive\b'),
            ("perpetual", r'\bperpetual\b'),
            ("irrevocable", r'\birrevocable\b'),
            ("unlimited", r'\bunlimited\b'),
            ("sole remedy", r'\bsole\s+remedy\b'),
            ("liquidated damages", r'\bliquidated\s+damages\b')
        ]
        
        for term, pattern in flag_patterns:
            if re.search(pattern, clause_lower):
                flagged.append(term)
        
        return flagged
    
    def _generate_llm_analysis(self, request: ComplianceRequest, context, violations: List[ComplianceViolation]) -> str:
        """Generate LLM-based compliance analysis"""
        # Build prompt for LLM
        prompt = self._build_compliance_prompt(request, context, violations)
        
        # Create LLM request
        from src.models.llm_types import LLMRequest, LLMMessage
        
        llm_request = LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            max_tokens=self.capabilities.max_response_tokens,
            temperature=0.3  # Lower temperature for more consistent compliance analysis
        )
        
        # Call LLM
        return self._call_llm_sync(llm_request)
    
    def _build_compliance_prompt(self, request: ComplianceRequest, context, violations: List[ComplianceViolation]) -> str:
        """Build LLM prompt for compliance analysis"""
        # Extract relevant context information
        gpc_info = self._extract_gpc_context(context)
        
        # Build violations summary
        violations_summary = []
        for v in violations:
            violations_summary.append(f"- {v.violation_type.value}: {v.description}")
        
        prompt = f"""You are a legal compliance expert analyzing contract clauses. Provide a comprehensive compliance analysis.

CONTRACT CLAUSE TO ANALYZE:
"{request.clause}"

CONTRACT CONTEXT:
{request.contract_context or 'No additional context provided'}

ENTERPRISE POLICIES:
{gpc_info}

DETECTED VIOLATIONS:
{chr(10).join(violations_summary) if violations_summary else 'No violations detected'}

INSTRUCTIONS:
1. Provide a detailed risk assessment of the clause
2. If violations exist, rewrite the clause to be compliant
3. Suggest specific recommendations for improvement
4. Ensure compliance with enterprise policies
5. Consider legal and regulatory implications

RESPONSE FORMAT:
RISK_ASSESSMENT: [Detailed risk analysis]
COMPLIANT_REWRITE: [Rewritten clause if needed, or "No rewrite needed"]
RECOMMENDATIONS: [Specific recommendations]

Generate the compliance analysis:"""

        return prompt
    
    def _extract_gpc_context(self, context) -> str:
        """Extract relevant GPC information for compliance analysis"""
        try:
            gpc = context.gpc
            
            # Build GPC summary for compliance
            gpc_summary = []
            
            if gpc.prohibited_clauses:
                gpc_summary.append(f"Prohibited Clauses: {', '.join(gpc.prohibited_clauses)}")
            
            if gpc.required_clauses:
                gpc_summary.append(f"Required Clauses: {', '.join(gpc.required_clauses)}")
            
            if gpc.compliance_guardrails:
                gpc_summary.append(f"Compliance Guardrails: {'; '.join(gpc.compliance_guardrails[:3])}")
            
            if gpc.legal_requirements:
                gpc_summary.append(f"Legal Requirements: {'; '.join(gpc.legal_requirements[:3])}")
            
            return "\n".join(gpc_summary) if gpc_summary else "No specific policy constraints"
            
        except Exception as e:
            logger.warning(f"Error extracting GPC context: {str(e)}")
            return "Policy information unavailable"
    
    def _parse_llm_analysis(self, llm_response: str) -> Tuple[str, Optional[str], List[str]]:
        """Parse LLM response into structured components"""
        try:
            # Extract sections from LLM response
            sections = self._extract_response_sections(llm_response)
            
            # Extract risk assessment
            risk_assessment = sections.get("RISK_ASSESSMENT", "Standard compliance analysis performed")
            
            # Extract compliant rewrite
            rewrite_text = sections.get("COMPLIANT_REWRITE", "")
            compliant_rewrite = None if "no rewrite needed" in rewrite_text.lower() else rewrite_text
            
            # Extract recommendations
            recommendations_text = sections.get("RECOMMENDATIONS", "")
            recommendations = self._parse_list_section(recommendations_text)
            
            return risk_assessment, compliant_rewrite, recommendations
            
        except Exception as e:
            logger.error(f"Error parsing LLM analysis: {str(e)}")
            return "Analysis parsing failed", None, ["Review clause manually"]
    
    def _extract_response_sections(self, response: str) -> Dict[str, str]:
        """Extract structured sections from LLM response"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            line = line.strip()
            
            # Check if line is a section header
            if ':' in line and line.split(':')[0].isupper():
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.split(':')[0].strip()
                current_content = [line.split(':', 1)[1].strip() if ':' in line else '']
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _parse_list_section(self, text: str) -> List[str]:
        """Parse text section into list of items"""
        if not text:
            return []
        
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Remove bullet points and numbering
                line = line.lstrip('•-*123456789. ')
                if line:
                    items.append(line)
        
        return items
    
    def _generate_fallback_analysis(self, request: ComplianceRequest, violations: List[ComplianceViolation]) -> Tuple[str, Optional[str], List[str]]:
        """Generate fallback analysis when LLM fails"""
        if violations:
            risk_assessment = f"Detected {len(violations)} compliance violations requiring attention"
            
            # Generate basic rewrite by removing problematic terms
            compliant_rewrite = self._generate_basic_rewrite(request.clause, violations)
            
            recommendations = [
                "Review and address detected violations",
                "Consult legal team for complex terms",
                "Ensure compliance with enterprise policies"
            ]
        else:
            risk_assessment = "No significant compliance issues detected"
            compliant_rewrite = None
            recommendations = ["Clause appears compliant with current policies"]
        
        return risk_assessment, compliant_rewrite, recommendations
    
    def _generate_basic_rewrite(self, clause: str, violations: List[ComplianceViolation]) -> str:
        """Generate basic compliant rewrite by addressing violations"""
        rewritten = clause
        
        for violation in violations:
            if violation.suggested_rewrite and violation.auto_fixable:
                # Apply suggested rewrite (simplified approach)
                if violation.violation_type == ViolationType.PROHIBITED_CLAUSE:
                    # Remove or replace prohibited terms
                    rewritten = self._apply_prohibited_fix(rewritten, violation)
        
        return rewritten if rewritten != clause else f"[COMPLIANCE REVIEW REQUIRED] {clause}"
    
    def _apply_prohibited_fix(self, clause: str, violation: ComplianceViolation) -> str:
        """Apply fix for prohibited clause violations"""
        # Simplified rewrite logic
        if "liability waiver" in clause.lower():
            return clause.replace("liability waiver", "limited liability provision")
        elif "indemnification" in clause.lower():
            return clause.replace("indemnification", "mutual indemnification")
        elif "unlimited liability" in clause.lower():
            return clause.replace("unlimited liability", "liability limited to contract value")
        
        return f"[REWRITE REQUIRED] {clause}"
    
    def _suggest_prohibited_rewrite(self, clause: str, prohibited: str) -> str:
        """Suggest rewrite for prohibited clauses"""
        suggestions = {
            "liability_waiver": "Replace with limited liability provision",
            "indemnification": "Replace with mutual indemnification clause",
            "unlimited_liability": "Add liability cap equal to contract value"
        }
        return suggestions.get(prohibited, f"Remove or modify {prohibited} clause")
    
    def _suggest_risk_rewrite(self, clause: str, pattern: str) -> str:
        """Suggest rewrite for risky terms"""
        return f"Modify clause to reduce legal risk associated with pattern: {pattern}"
    
    def _suggest_required_addition(self, clause: str, required: str) -> str:
        """Suggest addition of required clauses"""
        additions = {
            "warranty": "Add warranty provision with appropriate coverage period",
            "data_protection": "Add data protection and privacy compliance clause",
            "termination_rights": "Add termination clause with appropriate notice period"
        }
        return additions.get(required, f"Add {required} clause")
    
    def _requires_legal_review(self, violations: List[ComplianceViolation], risk_level: RiskLevel) -> bool:
        """Determine if legal review is required"""
        # Require legal review for high/critical risk or non-auto-fixable violations
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        # Require review if any violations are not auto-fixable
        if any(not v.auto_fixable for v in violations):
            return True
        
        return False
    
    def _calculate_confidence_score(self, violations: List[ComplianceViolation], risk_level: RiskLevel) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.9
        
        # Reduce confidence based on risk level
        risk_penalties = {
            RiskLevel.LOW: 0.0,
            RiskLevel.MEDIUM: 0.1,
            RiskLevel.HIGH: 0.2,
            RiskLevel.CRITICAL: 0.3
        }
        
        confidence = base_confidence - risk_penalties.get(risk_level, 0.0)
        
        # Reduce confidence based on number of violations
        violation_penalty = min(0.1 * len(violations), 0.3)
        confidence -= violation_penalty
        
        return max(0.5, confidence)  # Minimum confidence of 0.5
    
    def _format_compliance_response(self, result: ComplianceResult, request: ComplianceRequest) -> str:
        """Format compliance result into final response"""
        response_parts = []
        
        # Header
        response_parts.append("COMPLIANCE ANALYSIS REPORT")
        response_parts.append("=" * 50)
        
        # Risk assessment
        response_parts.append(f"\n🔍 RISK ASSESSMENT ({result.risk_level.value.upper()}):")
        response_parts.append(result.risk_assessment)
        
        # Violations
        if result.violations:
            response_parts.append(f"\n⚠️ COMPLIANCE VIOLATIONS ({len(result.violations)} found):")
            for i, violation in enumerate(result.violations, 1):
                response_parts.append(f"{i}. {violation.description} (Risk: {violation.risk_level.value})")
                if violation.suggested_rewrite:
                    response_parts.append(f"   → Suggested fix: {violation.suggested_rewrite}")
        else:
            response_parts.append("\n✅ NO COMPLIANCE VIOLATIONS DETECTED")
        
        # Compliant rewrite
        if result.compliant_rewrite:
            response_parts.append("\n📝 COMPLIANT REWRITE:")
            response_parts.append(f'"{result.compliant_rewrite}"')
        
        # Flagged terms
        if result.flagged_terms:
            response_parts.append(f"\n🚩 FLAGGED TERMS:")
            for term in result.flagged_terms:
                response_parts.append(f"• {term}")
        
        # Recommendations
        if result.recommendations:
            response_parts.append("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations, 1):
                response_parts.append(f"{i}. {rec}")
        
        # Legal review requirement
        if result.requires_legal_review:
            response_parts.append("\n⚖️ LEGAL REVIEW REQUIRED")
            response_parts.append("This clause requires review by legal counsel due to complexity or high risk.")
        
        # Summary
        response_parts.append(f"\n📊 ANALYSIS SUMMARY:")
        response_parts.append(f"Risk Level: {result.risk_level.value.upper()}")
        response_parts.append(f"Violations: {len(result.violations)}")
        response_parts.append(f"Confidence: {result.confidence_score:.1%}")
        response_parts.append(f"Legal Review: {'Required' if result.requires_legal_review else 'Not Required'}")
        
        return "\n".join(response_parts)
    
    def _call_llm_sync(self, llm_request):
        """Synchronous wrapper for LLM calls (simplified for base framework)"""
        try:
            logger.info("Generating compliance analysis using mock LLM (production would use real LLM)")
            
            # Return a structured mock response for compliance analysis
            return """RISK_ASSESSMENT: Medium risk identified due to potential policy violations. Clause requires review for compliance with enterprise standards and regulatory requirements.

COMPLIANT_REWRITE: "This agreement shall include appropriate warranty provisions, data protection measures, and termination rights as required by enterprise policy. Provider shall maintain liability coverage and comply with all applicable regulations."

RECOMMENDATIONS: Add explicit warranty terms with minimum 12-month coverage
Include data protection and privacy compliance clauses
Specify termination rights with appropriate notice periods
Review liability limitations for compliance with enterprise standards
Ensure intellectual property protections are adequate"""
                
        except Exception as e:
            logger.warning(f"LLM call failed, using fallback: {str(e)}")
            # Return a basic structured response for fallback
            return """RISK_ASSESSMENT: Standard compliance analysis performed
COMPLIANT_REWRITE: No rewrite needed - clause appears compliant
RECOMMENDATIONS: Review clause for compliance with enterprise policies"""