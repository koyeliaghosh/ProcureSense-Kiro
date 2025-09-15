"""
Forecast Agent for ProcureSense procurement automation system

Handles budget alignment analysis, variance detection, and trade-off recommendations
with OKR alignment checking and budget threshold enforcement.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.agents.agent_types import AgentRequest, AgentCapabilities
from src.models.base_types import AgentType
from src.context.context_manager import ContextManager
from src.llm.client_factory import LLMClientFactory

logger = logging.getLogger(__name__)

class VarianceLevel(str, Enum):
    """Budget variance levels"""
    UNDER_BUDGET = "under_budget"
    ON_TARGET = "on_target"
    MINOR_OVERAGE = "minor_overage"
    SIGNIFICANT_OVERAGE = "significant_overage"
    CRITICAL_OVERAGE = "critical_overage"

class AlignmentStatus(str, Enum):
    """OKR alignment status"""
    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"
    UNKNOWN = "unknown"

@dataclass
class BudgetVariance:
    """Budget variance analysis"""
    category: str
    planned_spend: float
    budget_allocation: float
    variance_amount: float
    variance_percentage: float
    variance_level: VarianceLevel
    exceeds_threshold: bool

@dataclass
class OKRAlignment:
    """OKR alignment analysis"""
    okr_text: str
    alignment_status: AlignmentStatus
    alignment_score: float
    supporting_rationale: str

@dataclass
class ForecastRequest:
    """Structured forecast request data"""
    category: str
    quarter: str
    planned_spend: float
    current_budget: Optional[float] = None
    business_justification: Optional[str] = None
    strategic_priority: Optional[str] = None

@dataclass
class ForecastResult:
    """Structured forecast analysis result"""
    category: str
    quarter: str
    planned_spend: float
    budget_variance: BudgetVariance
    okr_alignments: List[OKRAlignment]
    trade_off_recommendations: List[str]
    budget_adjustments: List[str]
    risk_factors: List[str]
    approval_requirements: List[str]
    confidence_score: float
    requires_executive_approval: bool

class ForecastAgent(BaseAgent):
    """
    Forecast Agent for budget alignment and variance analysis
    
    Capabilities:
    - Analyze budget alignment with planned spending
    - Detect variance and recommend trade-offs
    - Check OKR alignment and strategic fit
    - Enforce budget variance gates
    - Provide budget adjustment recommendations
    """
    
    def __init__(self, context_manager: ContextManager):
        """Initialize Forecast Agent"""
        super().__init__(context_manager, AgentType.FORECAST)
        
        # Get settings and create LLM client
        from src.config.settings import get_settings
        settings = get_settings()
        self.llm_client = LLMClientFactory.create_client(settings)
        
        # Variance thresholds
        self.minor_variance_threshold = 0.05    # 5%
        self.significant_variance_threshold = 0.15  # 15%
        self.critical_variance_threshold = 0.25     # 25%
        
        # Executive approval thresholds
        self.executive_approval_threshold = 100000.0  # $100k
        self.board_approval_threshold = 500000.0      # $500k
        
        logger.info("Initialized Forecast Agent with budget variance thresholds")
    
    def _define_capabilities(self) -> AgentCapabilities:
        """Define forecast agent capabilities"""
        return AgentCapabilities(
            agent_type=AgentType.FORECAST,
            supported_operations=[
                "analyze_budget_alignment",
                "detect_variance",
                "recommend_trade_offs",
                "check_okr_alignment",
                "enforce_budget_gates",
                "calculate_adjustments"
            ],
            required_context_layers=["gpc", "dsc"],
            max_response_tokens=2000,
            requires_gpc_validation=True,
            supports_auto_revision=True
        )
    
    def _validate_request_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate forecast request payload"""
        required_fields = ["category", "quarter", "planned_spend"]
        
        # Check required fields
        for field in required_fields:
            if field not in payload:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate planned spend
        planned_spend = payload.get("planned_spend")
        if not isinstance(planned_spend, (int, float)) or planned_spend < 0:
            logger.error(f"Invalid planned spend: {planned_spend}")
            return False
        
        # Validate category
        category = payload.get("category")
        if not isinstance(category, str) or not category.strip():
            logger.error("Category must be a non-empty string")
            return False
        
        # Validate quarter
        quarter = payload.get("quarter")
        if not isinstance(quarter, str) or not self._is_valid_quarter(quarter):
            logger.error(f"Invalid quarter format: {quarter}")
            return False
        
        return True
    
    def _is_valid_quarter(self, quarter: str) -> bool:
        """Validate quarter format (e.g., Q1 2024, Q2 2024)"""
        try:
            parts = quarter.strip().split()
            if len(parts) != 2:
                return False
            
            quarter_part = parts[0].upper()
            year_part = parts[1]
            
            # Check quarter format
            if not quarter_part.startswith('Q') or quarter_part[1:] not in ['1', '2', '3', '4']:
                return False
            
            # Check year format
            year = int(year_part)
            current_year = datetime.now().year
            if year < current_year or year > current_year + 5:
                return False
            
            return True
        except (ValueError, IndexError):
            return False
    
    def _process_agent_request(self, request: AgentRequest, context) -> str:
        """Process forecast request and generate response"""
        # Parse request into structured format
        forecast_request = self._parse_forecast_request(request.payload)
        
        # Perform forecast analysis
        result = self._analyze_forecast(forecast_request, context)
        
        # Format response
        response = self._format_forecast_response(result, forecast_request)
        
        logger.info(f"Generated forecast analysis for {forecast_request.category} {forecast_request.quarter}")
        
        return response
    
    def _parse_forecast_request(self, payload: Dict[str, Any]) -> ForecastRequest:
        """Parse request payload into structured forecast request"""
        return ForecastRequest(
            category=payload["category"],
            quarter=payload["quarter"],
            planned_spend=payload["planned_spend"],
            current_budget=payload.get("current_budget"),
            business_justification=payload.get("business_justification"),
            strategic_priority=payload.get("strategic_priority")
        )
    
    def _analyze_forecast(self, request: ForecastRequest, context) -> ForecastResult:
        """Perform comprehensive forecast analysis"""
        # Analyze budget variance
        budget_variance = self._analyze_budget_variance(request, context)
        
        # Check OKR alignment
        okr_alignments = self._analyze_okr_alignment(request, context)
        
        # Generate trade-off recommendations and adjustments
        try:
            llm_analysis = self._generate_llm_analysis(request, context, budget_variance, okr_alignments)
            trade_offs, adjustments, risks = self._parse_llm_analysis(llm_analysis)
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            trade_offs, adjustments, risks = self._generate_fallback_analysis(request, budget_variance)
        
        # Determine approval requirements
        approval_requirements = self._determine_approval_requirements(request, budget_variance)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(budget_variance, okr_alignments)
        
        # Determine if executive approval is required
        requires_executive_approval = self._requires_executive_approval(request, budget_variance)
        
        return ForecastResult(
            category=request.category,
            quarter=request.quarter,
            planned_spend=request.planned_spend,
            budget_variance=budget_variance,
            okr_alignments=okr_alignments,
            trade_off_recommendations=trade_offs,
            budget_adjustments=adjustments,
            risk_factors=risks,
            approval_requirements=approval_requirements,
            confidence_score=confidence_score,
            requires_executive_approval=requires_executive_approval
        )
    
    def _get_budget_allocation(self, request: ForecastRequest, context) -> float:
        """Get budget allocation for the request"""
        # Use current_budget if provided
        if request.current_budget is not None:
            return request.current_budget
        
        try:
            # Get budget allocation from GPC context
            gpc = context.gpc
            budget_thresholds = gpc.budget_thresholds
            
            # Get budget allocation for category
            budget_allocation = budget_thresholds.get(request.category.lower(), 50000.0)
            return budget_allocation
            
        except Exception as e:
            logger.warning(f"Could not access budget context: {str(e)}")
            # Use default budget allocation
            return 50000.0
    
    def _analyze_budget_variance(self, request: ForecastRequest, context) -> BudgetVariance:
        """Analyze budget variance for the forecast request"""
        # Get budget allocation
        budget_allocation = self._get_budget_allocation(request, context)
        
        # Calculate variance
        variance_amount = request.planned_spend - budget_allocation
        variance_percentage = (variance_amount / budget_allocation) if budget_allocation > 0 else 0.0
        
        # Determine variance level
        variance_level = self._determine_variance_level(variance_percentage)
        
        # Check if exceeds threshold
        exceeds_threshold = abs(variance_percentage) > self.significant_variance_threshold
        
        return BudgetVariance(
            category=request.category,
            planned_spend=request.planned_spend,
            budget_allocation=budget_allocation,
            variance_amount=variance_amount,
            variance_percentage=variance_percentage,
            variance_level=variance_level,
            exceeds_threshold=exceeds_threshold
        )
    
    def _determine_variance_level(self, variance_percentage: float) -> VarianceLevel:
        """Determine variance level based on percentage"""
        abs_variance = abs(variance_percentage)
        
        if abs_variance >= self.critical_variance_threshold:
            return VarianceLevel.CRITICAL_OVERAGE if variance_percentage > 0 else VarianceLevel.UNDER_BUDGET
        elif abs_variance >= self.significant_variance_threshold:
            return VarianceLevel.SIGNIFICANT_OVERAGE if variance_percentage > 0 else VarianceLevel.UNDER_BUDGET
        elif abs_variance >= self.minor_variance_threshold:
            return VarianceLevel.MINOR_OVERAGE if variance_percentage > 0 else VarianceLevel.ON_TARGET
        else:
            return VarianceLevel.ON_TARGET
    
    def _analyze_okr_alignment(self, request: ForecastRequest, context) -> List[OKRAlignment]:
        """Analyze OKR alignment for the forecast request"""
        alignments = []
        
        try:
            # Get enterprise OKRs from context
            gpc = context.gpc
            enterprise_okrs = gpc.enterprise_okrs
            
            for okr in enterprise_okrs:
                alignment = self._assess_okr_alignment(request, okr)
                alignments.append(alignment)
                
        except Exception as e:
            logger.warning(f"Could not access OKR context: {str(e)}")
            # Create default OKR alignment
            default_okr = OKRAlignment(
                okr_text="Cost optimization and efficiency improvement",
                alignment_status=AlignmentStatus.UNKNOWN,
                alignment_score=0.5,
                supporting_rationale="Unable to assess alignment due to missing context"
            )
            alignments.append(default_okr)
        
        return alignments
    
    def _assess_okr_alignment(self, request: ForecastRequest, okr_text: str) -> OKRAlignment:
        """Assess alignment between forecast request and specific OKR"""
        # Simple keyword-based alignment assessment
        okr_lower = okr_text.lower()
        category_lower = request.category.lower()
        
        alignment_score = 0.5  # Default neutral alignment
        alignment_status = AlignmentStatus.UNKNOWN
        rationale = "Standard alignment assessment"
        
        # Check for cost-related OKRs
        if any(keyword in okr_lower for keyword in ["cost", "save", "reduce", "efficiency"]):
            if request.planned_spend < 50000:  # Smaller spend aligns with cost reduction
                alignment_score = 0.8
                alignment_status = AlignmentStatus.ALIGNED
                rationale = "Lower spending aligns with cost reduction objectives"
            else:
                alignment_score = 0.3
                alignment_status = AlignmentStatus.MISALIGNED
                rationale = "Higher spending may conflict with cost reduction goals"
        
        # Check for growth/investment OKRs
        elif any(keyword in okr_lower for keyword in ["growth", "invest", "expand", "improve"]):
            if request.planned_spend > 25000:  # Investment spending
                alignment_score = 0.8
                alignment_status = AlignmentStatus.ALIGNED
                rationale = "Investment spending supports growth objectives"
            else:
                alignment_score = 0.6
                alignment_status = AlignmentStatus.PARTIALLY_ALIGNED
                rationale = "Moderate spending partially supports growth goals"
        
        # Check for category-specific alignment
        if category_lower in okr_lower:
            alignment_score = min(alignment_score + 0.2, 1.0)
            rationale += f" and directly relates to {request.category} category"
        
        return OKRAlignment(
            okr_text=okr_text,
            alignment_status=alignment_status,
            alignment_score=alignment_score,
            supporting_rationale=rationale
        )
    
    def _generate_llm_analysis(self, request: ForecastRequest, context, budget_variance: BudgetVariance, okr_alignments: List[OKRAlignment]) -> str:
        """Generate LLM-based forecast analysis"""
        # Build prompt for LLM
        prompt = self._build_forecast_prompt(request, context, budget_variance, okr_alignments)
        
        # Create LLM request
        from src.models.llm_types import LLMRequest, LLMMessage
        
        llm_request = LLMRequest(
            messages=[LLMMessage(role="user", content=prompt)],
            max_tokens=self.capabilities.max_response_tokens,
            temperature=0.4  # Moderate temperature for balanced analysis
        )
        
        # Call LLM
        return self._call_llm_sync(llm_request)
    
    def _build_forecast_prompt(self, request: ForecastRequest, context, budget_variance: BudgetVariance, okr_alignments: List[OKRAlignment]) -> str:
        """Build LLM prompt for forecast analysis"""
        # Extract relevant context information
        gpc_info = self._extract_gpc_context(context)
        
        # Build OKR alignment summary
        okr_summary = []
        for alignment in okr_alignments:
            okr_summary.append(f"- {alignment.okr_text}: {alignment.alignment_status.value} ({alignment.alignment_score:.1%})")
        
        prompt = f"""You are a financial planning expert analyzing procurement forecasts. Provide comprehensive budget analysis and recommendations.

FORECAST REQUEST:
- Category: {request.category}
- Quarter: {request.quarter}
- Planned Spend: ${request.planned_spend:,.2f}
- Budget Allocation: ${budget_variance.budget_allocation:,.2f}
- Variance: ${budget_variance.variance_amount:,.2f} ({budget_variance.variance_percentage:.1%})
- Variance Level: {budget_variance.variance_level.value}

BUSINESS CONTEXT:
- Justification: {request.business_justification or 'Not provided'}
- Strategic Priority: {request.strategic_priority or 'Not specified'}

ENTERPRISE POLICIES:
{gpc_info}

OKR ALIGNMENT ANALYSIS:
{chr(10).join(okr_summary) if okr_summary else 'No OKR alignment data available'}

INSTRUCTIONS:
1. Analyze the budget variance and its implications
2. Provide specific trade-off recommendations if overage exists
3. Suggest budget adjustments or alternatives
4. Identify potential risk factors
5. Ensure alignment with enterprise policies and OKRs

RESPONSE FORMAT:
TRADE_OFF_RECOMMENDATIONS: [Specific trade-off options]
BUDGET_ADJUSTMENTS: [Recommended budget adjustments]
RISK_FACTORS: [Potential risks and mitigation strategies]

Generate the forecast analysis:"""

        return prompt
    
    def _extract_gpc_context(self, context) -> str:
        """Extract relevant GPC information for forecast analysis"""
        try:
            gpc = context.gpc
            
            # Build GPC summary for forecasting
            gpc_summary = []
            
            if gpc.enterprise_okrs:
                gpc_summary.append(f"Enterprise OKRs: {'; '.join(gpc.enterprise_okrs[:3])}")
            
            if gpc.budget_thresholds:
                thresholds = [f"{cat}: ${amt:,.0f}" for cat, amt in gpc.budget_thresholds.items()]
                gpc_summary.append(f"Budget Thresholds: {', '.join(thresholds)}")
            
            if gpc.compliance_guardrails:
                gpc_summary.append(f"Compliance Guardrails: {'; '.join(gpc.compliance_guardrails[:2])}")
            
            return "\n".join(gpc_summary) if gpc_summary else "No specific policy constraints"
            
        except Exception as e:
            logger.warning(f"Error extracting GPC context: {str(e)}")
            return "Policy information unavailable"
    
    def _parse_llm_analysis(self, llm_response: str) -> Tuple[List[str], List[str], List[str]]:
        """Parse LLM response into structured components"""
        try:
            # Extract sections from LLM response
            sections = self._extract_response_sections(llm_response)
            
            # Extract trade-off recommendations
            trade_offs_text = sections.get("TRADE_OFF_RECOMMENDATIONS", "")
            trade_offs = self._parse_list_section(trade_offs_text)
            
            # Extract budget adjustments
            adjustments_text = sections.get("BUDGET_ADJUSTMENTS", "")
            adjustments = self._parse_list_section(adjustments_text)
            
            # Extract risk factors
            risks_text = sections.get("RISK_FACTORS", "")
            risks = self._parse_list_section(risks_text)
            
            return trade_offs, adjustments, risks
            
        except Exception as e:
            logger.error(f"Error parsing LLM analysis: {str(e)}")
            return ["Review spending priorities"], ["Consider budget reallocation"], ["Monitor variance trends"]
    
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
    
    def _generate_fallback_analysis(self, request: ForecastRequest, budget_variance: BudgetVariance) -> Tuple[List[str], List[str], List[str]]:
        """Generate fallback analysis when LLM fails"""
        trade_offs = []
        adjustments = []
        risks = []
        
        # Generate recommendations based on variance level
        if budget_variance.variance_level in [VarianceLevel.SIGNIFICANT_OVERAGE, VarianceLevel.CRITICAL_OVERAGE]:
            trade_offs.extend([
                "Consider phasing the spend across multiple quarters",
                "Evaluate alternative vendors or solutions",
                "Reduce scope to fit within budget constraints"
            ])
            
            adjustments.extend([
                f"Request additional budget of ${abs(budget_variance.variance_amount):,.2f}",
                "Reallocate funds from other categories",
                "Defer non-critical components to next quarter"
            ])
            
            risks.extend([
                "Budget overage may impact other initiatives",
                "Requires executive approval for variance",
                "Potential delay if budget not approved"
            ])
        
        elif budget_variance.variance_level == VarianceLevel.MINOR_OVERAGE:
            trade_offs.extend([
                "Minor adjustments to scope or timeline",
                "Negotiate better terms with vendors"
            ])
            
            adjustments.extend([
                "Small budget increase may be acceptable",
                "Optimize procurement approach"
            ])
        
        else:  # On target or under budget
            trade_offs.extend([
                "Consider additional value-add features",
                "Invest savings in quality improvements"
            ])
            
            adjustments.extend([
                "Budget allocation appears appropriate",
                "Consider reallocating surplus to other needs"
            ])
        
        return trade_offs, adjustments, risks
    
    def _determine_approval_requirements(self, request: ForecastRequest, budget_variance: BudgetVariance) -> List[str]:
        """Determine approval requirements based on spend and variance"""
        approvals = []
        
        # Check spend thresholds
        if request.planned_spend >= self.board_approval_threshold:
            approvals.append("Board of Directors approval required")
        elif request.planned_spend >= self.executive_approval_threshold:
            approvals.append("Executive leadership approval required")
        
        # Check variance thresholds
        if budget_variance.variance_level == VarianceLevel.CRITICAL_OVERAGE:
            approvals.append("CFO approval required for critical budget variance")
        elif budget_variance.variance_level == VarianceLevel.SIGNIFICANT_OVERAGE:
            approvals.append("Finance director approval required for significant variance")
        
        # Default approval for normal spend
        if not approvals:
            approvals.append("Standard procurement approval process")
        
        return approvals
    
    def _calculate_confidence_score(self, budget_variance: BudgetVariance, okr_alignments: List[OKRAlignment]) -> float:
        """Calculate confidence score for the forecast analysis"""
        base_confidence = 0.8
        
        # Reduce confidence based on variance level
        variance_penalties = {
            VarianceLevel.ON_TARGET: 0.0,
            VarianceLevel.UNDER_BUDGET: 0.0,
            VarianceLevel.MINOR_OVERAGE: 0.1,
            VarianceLevel.SIGNIFICANT_OVERAGE: 0.2,
            VarianceLevel.CRITICAL_OVERAGE: 0.3
        }
        
        confidence = base_confidence - variance_penalties.get(budget_variance.variance_level, 0.0)
        
        # Adjust based on OKR alignment
        if okr_alignments:
            avg_alignment = sum(alignment.alignment_score for alignment in okr_alignments) / len(okr_alignments)
            alignment_bonus = (avg_alignment - 0.5) * 0.2  # +/- 0.1 based on alignment
            confidence += alignment_bonus
        
        return max(0.5, min(1.0, confidence))  # Keep between 0.5 and 1.0
    
    def _requires_executive_approval(self, request: ForecastRequest, budget_variance: BudgetVariance) -> bool:
        """Determine if executive approval is required"""
        # High spend amounts require approval
        if request.planned_spend >= self.executive_approval_threshold:
            return True
        
        # Significant variances require approval
        if budget_variance.variance_level in [VarianceLevel.SIGNIFICANT_OVERAGE, VarianceLevel.CRITICAL_OVERAGE]:
            return True
        
        return False
    
    def _format_forecast_response(self, result: ForecastResult, request: ForecastRequest) -> str:
        """Format forecast result into final response"""
        response_parts = []
        
        # Header
        response_parts.append(f"BUDGET FORECAST ANALYSIS - {request.category.upper()} {request.quarter}")
        response_parts.append("=" * 60)
        
        # Budget variance analysis
        variance = result.budget_variance
        response_parts.append(f"\n💰 BUDGET VARIANCE ANALYSIS:")
        response_parts.append(f"Planned Spend: ${variance.planned_spend:,.2f}")
        response_parts.append(f"Budget Allocation: ${variance.budget_allocation:,.2f}")
        response_parts.append(f"Variance: ${variance.variance_amount:,.2f} ({variance.variance_percentage:.1%})")
        response_parts.append(f"Variance Level: {variance.variance_level.value.replace('_', ' ').title()}")
        
        # OKR alignment
        if result.okr_alignments:
            response_parts.append(f"\n🎯 OKR ALIGNMENT ANALYSIS:")
            for alignment in result.okr_alignments:
                status_emoji = "✅" if alignment.alignment_status == AlignmentStatus.ALIGNED else "⚠️" if alignment.alignment_status == AlignmentStatus.PARTIALLY_ALIGNED else "❌"
                response_parts.append(f"{status_emoji} {alignment.okr_text}")
                response_parts.append(f"   Status: {alignment.alignment_status.value.replace('_', ' ').title()} ({alignment.alignment_score:.1%})")
                response_parts.append(f"   Rationale: {alignment.supporting_rationale}")
        
        # Trade-off recommendations
        if result.trade_off_recommendations:
            response_parts.append(f"\n⚖️ TRADE-OFF RECOMMENDATIONS:")
            for i, trade_off in enumerate(result.trade_off_recommendations, 1):
                response_parts.append(f"{i}. {trade_off}")
        
        # Budget adjustments
        if result.budget_adjustments:
            response_parts.append(f"\n📊 BUDGET ADJUSTMENTS:")
            for i, adjustment in enumerate(result.budget_adjustments, 1):
                response_parts.append(f"{i}. {adjustment}")
        
        # Risk factors
        if result.risk_factors:
            response_parts.append(f"\n⚠️ RISK FACTORS:")
            for i, risk in enumerate(result.risk_factors, 1):
                response_parts.append(f"{i}. {risk}")
        
        # Approval requirements
        response_parts.append(f"\n✅ APPROVAL REQUIREMENTS:")
        for i, approval in enumerate(result.approval_requirements, 1):
            response_parts.append(f"{i}. {approval}")
        
        # Executive approval flag
        if result.requires_executive_approval:
            response_parts.append(f"\n🔴 EXECUTIVE APPROVAL REQUIRED")
            response_parts.append("This forecast requires executive leadership review due to high spend or significant variance.")
        
        # Summary
        response_parts.append(f"\n📈 FORECAST SUMMARY:")
        response_parts.append(f"Category: {result.category}")
        response_parts.append(f"Quarter: {result.quarter}")
        response_parts.append(f"Planned Spend: ${result.planned_spend:,.2f}")
        response_parts.append(f"Variance Level: {variance.variance_level.value.replace('_', ' ').title()}")
        response_parts.append(f"Confidence Score: {result.confidence_score:.1%}")
        response_parts.append(f"Executive Approval: {'Required' if result.requires_executive_approval else 'Not Required'}")
        
        return "\n".join(response_parts)
    
    def _call_llm_sync(self, llm_request):
        """Synchronous wrapper for LLM calls (simplified for base framework)"""
        try:
            logger.info("Generating forecast analysis using mock LLM (production would use real LLM)")
            
            # Return a structured mock response for budget forecasting
            return """TRADE_OFF_RECOMMENDATIONS: Consider phased implementation to spread costs across quarters. Evaluate alternative vendors for competitive pricing. Prioritize high-impact initiatives and defer non-critical purchases to future quarters.

BUDGET_ADJUSTMENTS: Request additional budget allocation of 15-20% to accommodate planned spending. Consider reallocating funds from underutilized categories. Implement quarterly budget reviews to track variance trends.

RISK_FACTORS: Budget variance exceeds acceptable threshold of 15%
Market price volatility may impact final costs
Vendor delivery delays could affect quarterly spending patterns
Currency fluctuations for international vendors
Regulatory changes may require additional compliance spending

OKR_ALIGNMENT: Spending aligns with strategic objectives for operational efficiency
Investment supports digital transformation initiatives
Budget allocation matches enterprise growth targets"""
                
        except Exception as e:
            logger.warning(f"LLM call failed, using fallback: {str(e)}")
            # Return a basic structured response for fallback
            return """TRADE_OFF_RECOMMENDATIONS: Consider alternative approaches and phased implementation
BUDGET_ADJUSTMENTS: Review budget allocation and seek additional funding if needed
RISK_FACTORS: Monitor variance trends and ensure stakeholder alignment"""