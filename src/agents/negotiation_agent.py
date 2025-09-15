"""
Negotiation Agent for ProcureSense procurement automation system

Handles vendor negotiations, pricing proposals, and contract term generation
with automatic warranty addition for aggressive discounts.
"""
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent
from src.agents.agent_types import AgentRequest, AgentCapabilities
from src.models.base_types import AgentType
from src.context.context_manager import ContextManager
from src.llm.client_factory import LLMClientFactory

logger = logging.getLogger(__name__)

@dataclass
class NegotiationRequest:
    """Structured negotiation request data"""
    vendor: str
    target_discount_pct: float
    category: str
    current_price: Optional[float] = None
    contract_duration: Optional[str] = None
    volume_commitment: Optional[int] = None
    additional_context: Optional[str] = None

@dataclass
class NegotiationResult:
    """Structured negotiation result"""
    pricing_proposal: str
    contract_terms: List[str]
    warranty_requirements: List[str]
    risk_mitigation: List[str]
    negotiation_strategy: str
    confidence_score: float

class NegotiationAgent(BaseAgent):
    """
    Negotiation Agent for vendor negotiations and pricing proposals
    
    Capabilities:
    - Generate pricing proposals based on target discounts
    - Propose contract terms and conditions
    - Automatically add warranties for aggressive discounts
    - Provide negotiation strategies and risk mitigation
    """
    
    def __init__(self, context_manager: ContextManager):
        """
        Initialize Negotiation Agent
        
        Args:
            context_manager: Context management system
        """
        super().__init__(context_manager, AgentType.NEGOTIATION)
        
        # Get settings and create LLM client
        from src.config.settings import get_settings
        settings = get_settings()
        self.llm_client = LLMClientFactory.create_client(settings)
        
        # Thresholds for aggressive discount detection
        self.aggressive_discount_threshold = 0.15  # 15% or higher
        self.high_risk_discount_threshold = 0.25   # 25% or higher
        
        logger.info("Initialized Negotiation Agent with LLM client")
    
    def _define_capabilities(self) -> AgentCapabilities:
        """Define negotiation agent capabilities"""
        return AgentCapabilities(
            agent_type=AgentType.NEGOTIATION,
            supported_operations=[
                "generate_pricing_proposal",
                "negotiate_terms",
                "add_warranties",
                "assess_negotiation_risk",
                "create_contract_terms"
            ],
            required_context_layers=["gpc", "dsc", "tsc"],
            max_response_tokens=2000,
            requires_gpc_validation=True,
            supports_auto_revision=True
        )
    
    def _validate_request_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate negotiation request payload
        
        Args:
            payload: Request payload to validate
            
        Returns:
            bool: True if payload is valid
        """
        required_fields = ["vendor", "target_discount_pct", "category"]
        
        # Check required fields
        for field in required_fields:
            if field not in payload:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate discount percentage (accept both decimal 0.15 and percentage 15.0)
        discount = payload.get("target_discount_pct")
        if not isinstance(discount, (int, float)) or discount < 0:
            logger.error(f"Invalid discount percentage: {discount}. Must be a positive number.")
            return False
        
        # Convert percentage to decimal if needed (15.0 -> 0.15)
        if discount > 1:
            payload["target_discount_pct"] = discount / 100.0
            logger.info(f"Converted discount from {discount}% to {payload['target_discount_pct']}")
        
        # Final validation: should be between 0 and 1 after conversion
        final_discount = payload["target_discount_pct"]
        if final_discount > 1:
            logger.error(f"Discount percentage too high: {final_discount}. Maximum is 100% (1.0).")
            return False
        
        # Validate vendor name
        vendor = payload.get("vendor")
        if not isinstance(vendor, str) or not vendor.strip():
            logger.error("Vendor name must be a non-empty string")
            return False
        
        # Validate category
        category = payload.get("category")
        if not isinstance(category, str) or not category.strip():
            logger.error("Category must be a non-empty string")
            return False
        
        return True
    
    def _process_agent_request(self, request: AgentRequest, context) -> str:
        """
        Process negotiation request and generate response
        
        Args:
            request: Negotiation request
            context: Layered context for the request
            
        Returns:
            str: Generated negotiation response
        """
        # Parse request into structured format
        negotiation_request = self._parse_negotiation_request(request.payload)
        
        # Generate negotiation result
        result = self._generate_negotiation_result(negotiation_request, context)
        
        # Format response
        response = self._format_negotiation_response(result, negotiation_request)
        
        logger.info(f"Generated negotiation response for vendor {negotiation_request.vendor} "
                   f"with {negotiation_request.target_discount_pct:.1%} discount target")
        
        return response
    
    def _parse_negotiation_request(self, payload: Dict[str, Any]) -> NegotiationRequest:
        """Parse request payload into structured negotiation request"""
        return NegotiationRequest(
            vendor=payload["vendor"],
            target_discount_pct=payload["target_discount_pct"],
            category=payload["category"],
            current_price=payload.get("current_price"),
            contract_duration=payload.get("contract_duration"),
            volume_commitment=payload.get("volume_commitment"),
            additional_context=payload.get("additional_context")
        )
    
    def _generate_negotiation_result(self, request: NegotiationRequest, context) -> NegotiationResult:
        """
        Generate comprehensive negotiation result using LLM
        
        Args:
            request: Structured negotiation request
            context: Layered context
            
        Returns:
            NegotiationResult: Generated negotiation result
        """
        # Build prompt for LLM
        prompt = self._build_negotiation_prompt(request, context)
        
        # Generate response using LLM
        try:
            # Create LLM request
            from src.models.llm_types import LLMRequest, LLMMessage
            
            llm_request = LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                max_tokens=self.capabilities.max_response_tokens,
                temperature=0.7
            )
            
            # For now, use a synchronous approach (in production, this would be async)
            # This is a simplified implementation for the base framework
            llm_response = self._call_llm_sync(llm_request)
            
            # Parse LLM response into structured result
            result = self._parse_llm_response(llm_response, request)
            
            # Add automatic warranties for aggressive discounts
            result = self._add_automatic_warranties(result, request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating negotiation result: {str(e)}")
            # Return fallback result
            return self._generate_fallback_result(request)
    
    def _build_negotiation_prompt(self, request: NegotiationRequest, context) -> str:
        """
        Build LLM prompt for negotiation
        
        Args:
            request: Negotiation request
            context: Layered context
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Extract relevant context information
        gpc_info = self._extract_gpc_context(context)
        dsc_info = self._extract_dsc_context(context, request.category)
        
        prompt = f"""You are a procurement negotiation expert. Generate a comprehensive negotiation proposal.

NEGOTIATION REQUEST:
- Vendor: {request.vendor}
- Target Discount: {request.target_discount_pct:.1%}
- Category: {request.category}
- Current Price: {request.current_price or 'Not specified'}
- Contract Duration: {request.contract_duration or 'Not specified'}
- Volume Commitment: {request.volume_commitment or 'Not specified'}
- Additional Context: {request.additional_context or 'None'}

ENTERPRISE POLICIES:
{gpc_info}

CATEGORY STRATEGY:
{dsc_info}

INSTRUCTIONS:
1. Generate a pricing proposal that achieves the target discount
2. Propose specific contract terms and conditions
3. Include negotiation strategy and tactics
4. Identify risk mitigation measures
5. Ensure compliance with enterprise policies
6. Format response as structured sections

RESPONSE FORMAT:
PRICING_PROPOSAL: [Detailed pricing proposal]
CONTRACT_TERMS: [List of proposed contract terms]
NEGOTIATION_STRATEGY: [Strategic approach and tactics]
RISK_MITIGATION: [Risk mitigation measures]
CONFIDENCE: [Confidence score 0.0-1.0]

Generate the negotiation proposal:"""

        return prompt
    
    def _extract_gpc_context(self, context) -> str:
        """Extract relevant GPC information for negotiation"""
        try:
            gpc = context.gpc
            
            # Build GPC summary for negotiation
            gpc_summary = []
            
            if gpc.enterprise_okrs:
                gpc_summary.append(f"Enterprise OKRs: {'; '.join(gpc.enterprise_okrs[:3])}")
            
            if gpc.prohibited_clauses:
                gpc_summary.append(f"Prohibited Clauses: {', '.join(gpc.prohibited_clauses)}")
            
            if gpc.required_clauses:
                gpc_summary.append(f"Required Clauses: {', '.join(gpc.required_clauses)}")
            
            if gpc.budget_thresholds:
                thresholds = [f"{cat}: ${amt:,.0f}" for cat, amt in gpc.budget_thresholds.items()]
                gpc_summary.append(f"Budget Thresholds: {', '.join(thresholds)}")
            
            return "\n".join(gpc_summary) if gpc_summary else "No specific policy constraints"
            
        except Exception as e:
            logger.warning(f"Error extracting GPC context: {str(e)}")
            return "Policy information unavailable"
    
    def _extract_dsc_context(self, context, category: str) -> str:
        """Extract relevant DSC information for the category"""
        try:
            dsc = context.dsc
            
            # Build DSC summary for negotiation
            dsc_summary = []
            
            # Category-specific playbook
            if category in dsc.category_playbooks:
                dsc_summary.append(f"Category Playbook: {dsc.category_playbooks[category]}")
            
            # Vendor guidelines
            if dsc.vendor_guidelines:
                dsc_summary.append(f"Vendor Guidelines: {'; '.join(dsc.vendor_guidelines[:2])}")
            
            # Market intelligence
            if dsc.market_intelligence:
                dsc_summary.append(f"Market Intelligence: {'; '.join(dsc.market_intelligence[:2])}")
            
            return "\n".join(dsc_summary) if dsc_summary else f"No specific strategy for {category} category"
            
        except Exception as e:
            logger.warning(f"Error extracting DSC context: {str(e)}")
            return "Strategy information unavailable"
    
    def _parse_llm_response(self, llm_response: str, request: NegotiationRequest) -> NegotiationResult:
        """
        Parse LLM response into structured negotiation result
        
        Args:
            llm_response: Raw LLM response
            request: Original negotiation request
            
        Returns:
            NegotiationResult: Parsed result
        """
        try:
            # Initialize result with defaults
            result = NegotiationResult(
                pricing_proposal="",
                contract_terms=[],
                warranty_requirements=[],
                risk_mitigation=[],
                negotiation_strategy="",
                confidence_score=0.7
            )
            
            # Parse sections from LLM response
            sections = self._extract_response_sections(llm_response)
            
            # Extract pricing proposal
            result.pricing_proposal = sections.get("PRICING_PROPOSAL", 
                f"Negotiate {request.target_discount_pct:.1%} discount with {request.vendor}")
            
            # Extract contract terms
            terms_text = sections.get("CONTRACT_TERMS", "")
            result.contract_terms = self._parse_list_section(terms_text)
            
            # Extract negotiation strategy
            result.negotiation_strategy = sections.get("NEGOTIATION_STRATEGY", 
                "Standard negotiation approach with competitive benchmarking")
            
            # Extract risk mitigation
            risk_text = sections.get("RISK_MITIGATION", "")
            result.risk_mitigation = self._parse_list_section(risk_text)
            
            # Extract confidence score
            confidence_text = sections.get("CONFIDENCE", "0.7")
            try:
                result.confidence_score = float(confidence_text.strip())
                result.confidence_score = max(0.0, min(1.0, result.confidence_score))
            except ValueError:
                result.confidence_score = 0.7
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return self._generate_fallback_result(request)
    
    def _extract_response_sections(self, response: str) -> Dict[str, str]:
        """Extract structured sections from LLM response"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            line = line.strip()
            
            # Check if line is a section header
            if ':' in line and line.isupper():
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
    
    def _add_automatic_warranties(self, result: NegotiationResult, request: NegotiationRequest) -> NegotiationResult:
        """
        Add automatic warranties for aggressive discounts
        
        Args:
            result: Current negotiation result
            request: Original negotiation request
            
        Returns:
            NegotiationResult: Updated result with warranties
        """
        discount = request.target_discount_pct
        
        # Check if discount is aggressive
        if discount >= self.aggressive_discount_threshold:
            logger.info(f"Adding automatic warranties for aggressive discount: {discount:.1%}")
            
            # Standard warranties for aggressive discounts
            automatic_warranties = []
            
            if discount >= self.aggressive_discount_threshold:
                automatic_warranties.extend([
                    "Extended warranty period (minimum 24 months)",
                    "Performance guarantee with SLA commitments",
                    "Quality assurance and defect remediation"
                ])
            
            if discount >= self.high_risk_discount_threshold:
                automatic_warranties.extend([
                    "Financial stability guarantee or insurance",
                    "Delivery guarantee with penalty clauses",
                    "Intellectual property indemnification"
                ])
            
            # Category-specific warranties
            category_warranties = self._get_category_warranties(request.category, discount)
            automatic_warranties.extend(category_warranties)
            
            # Add to result
            result.warranty_requirements.extend(automatic_warranties)
            
            # Update contract terms to include warranty references
            warranty_term = f"Enhanced warranty requirements due to {discount:.1%} discount target"
            if warranty_term not in result.contract_terms:
                result.contract_terms.append(warranty_term)
            
            # Update risk mitigation
            risk_item = f"Mitigate {discount:.1%} discount risk through comprehensive warranties"
            if risk_item not in result.risk_mitigation:
                result.risk_mitigation.append(risk_item)
        
        return result
    
    def _get_category_warranties(self, category: str, discount: float) -> List[str]:
        """Get category-specific warranties based on discount level"""
        category_lower = category.lower()
        warranties = []
        
        if "software" in category_lower:
            warranties.extend([
                "Software maintenance and updates guarantee",
                "Data migration and integration support",
                "User training and documentation"
            ])
            
        elif "hardware" in category_lower:
            warranties.extend([
                "Hardware replacement guarantee",
                "On-site technical support",
                "Preventive maintenance program"
            ])
            
        elif "service" in category_lower:
            warranties.extend([
                "Service level agreement (SLA) guarantees",
                "Resource availability commitments",
                "Escalation and resolution procedures"
            ])
        
        return warranties
    
    def _generate_fallback_result(self, request: NegotiationRequest) -> NegotiationResult:
        """Generate fallback result when LLM fails"""
        return NegotiationResult(
            pricing_proposal=f"Negotiate {request.target_discount_pct:.1%} discount with {request.vendor} "
                           f"for {request.category} category procurement",
            contract_terms=[
                "Standard payment terms (Net 30)",
                "Delivery within agreed timeframe",
                "Quality standards compliance",
                "Termination clause with 30-day notice"
            ],
            warranty_requirements=[],
            risk_mitigation=[
                "Vendor financial stability verification",
                "Reference checks with existing customers",
                "Pilot program before full commitment"
            ],
            negotiation_strategy="Competitive benchmarking with market rate analysis",
            confidence_score=0.6
        )
    
    def _format_negotiation_response(self, result: NegotiationResult, request: NegotiationRequest) -> str:
        """
        Format negotiation result into final response
        
        Args:
            result: Negotiation result
            request: Original request
            
        Returns:
            str: Formatted response
        """
        response_parts = []
        
        # Header
        response_parts.append(f"NEGOTIATION PROPOSAL FOR {request.vendor.upper()}")
        response_parts.append("=" * 50)
        
        # Pricing proposal
        response_parts.append("\n📊 PRICING PROPOSAL:")
        response_parts.append(result.pricing_proposal)
        
        # Contract terms
        if result.contract_terms:
            response_parts.append("\n📋 PROPOSED CONTRACT TERMS:")
            for i, term in enumerate(result.contract_terms, 1):
                response_parts.append(f"{i}. {term}")
        
        # Warranty requirements
        if result.warranty_requirements:
            response_parts.append("\n🛡️ WARRANTY REQUIREMENTS:")
            for i, warranty in enumerate(result.warranty_requirements, 1):
                response_parts.append(f"{i}. {warranty}")
        
        # Negotiation strategy
        response_parts.append("\n🎯 NEGOTIATION STRATEGY:")
        response_parts.append(result.negotiation_strategy)
        
        # Risk mitigation
        if result.risk_mitigation:
            response_parts.append("\n⚠️ RISK MITIGATION:")
            for i, risk in enumerate(result.risk_mitigation, 1):
                response_parts.append(f"{i}. {risk}")
        
        # Confidence and summary
        response_parts.append(f"\n✅ CONFIDENCE SCORE: {result.confidence_score:.1%}")
        response_parts.append(f"\nTarget Discount: {request.target_discount_pct:.1%} | Category: {request.category}")
        
        return "\n".join(response_parts)
    
    def _call_llm_sync(self, llm_request):
        """
        Synchronous wrapper for LLM calls (simplified for base framework)
        
        For now, returns a structured mock response to ensure system functionality.
        In production, this would integrate with actual LLM services.
        """
        try:
            logger.info("Generating negotiation response using mock LLM (production would use real LLM)")
            
            # Return a structured mock response that matches expected format
            return """PRICING_PROPOSAL: Negotiate competitive pricing with volume discounts and multi-year commitment incentives. Propose tiered pricing structure with additional savings for extended contract terms.

CONTRACT_TERMS: Net 30 payment terms
Performance-based service level agreements
Quarterly business reviews and optimization sessions
Flexible scaling options for changing requirements
Standard termination clause with 60-day notice

NEGOTIATION_STRATEGY: Lead with competitive market analysis and benchmark pricing. Emphasize long-term partnership value and volume commitments. Use phased implementation approach to demonstrate value before full commitment.

RISK_MITIGATION: Vendor financial stability verification through credit checks
Reference validation with similar-sized customers
Pilot program implementation before full rollout
Escrow arrangement for large upfront payments
Regular performance monitoring and review cycles

CONFIDENCE: 0.85"""
                
        except Exception as e:
            logger.warning(f"LLM call failed, using fallback: {str(e)}")
            # Return a basic structured response for fallback
            return """PRICING_PROPOSAL: Standard negotiation approach with competitive benchmarking
CONTRACT_TERMS: Standard terms and conditions with performance guarantees
NEGOTIATION_STRATEGY: Market-based pricing with volume incentives
RISK_MITIGATION: Standard vendor qualification and performance monitoring
CONFIDENCE: 0.6"""