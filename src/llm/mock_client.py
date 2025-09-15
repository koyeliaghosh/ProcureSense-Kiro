"""
Mock LLM Client for cloud deployment where Ollama isn't available.
Provides realistic demo responses for ProcureSense agents.
"""

from typing import Dict, Any
import asyncio
from .base_client import BaseLLMClient
from ..models.llm_types import LLMConfig, LLMResponse


class MockLLMClient(BaseLLMClient):
    """Mock LLM client that provides realistic demo responses."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.demo_responses = {
            "negotiation": """Based on the vendor and discount target, here's my negotiation strategy:

**Pricing Analysis:**
- Current market rate analysis shows competitive positioning
- Target discount of {discount}% is achievable with strategic approach
- Recommend bundling services for additional value

**Negotiation Recommendations:**
1. **Volume Commitment**: Offer 2-year contract for {discount}% discount
2. **Payment Terms**: Net-30 to Net-15 for additional 2% savings  
3. **Warranty Extension**: Request 24-month warranty inclusion
4. **Implementation Support**: Include free onboarding and training

**Risk Mitigation:**
- Include performance SLAs with penalty clauses
- Maintain termination rights with 90-day notice
- Require vendor insurance coverage minimum $2M

**Expected Outcome:** {discount}% discount achieved with enhanced terms and warranty protection.""",

            "compliance": """**Compliance Analysis Complete**

**Policy Violations Identified:**
1. **Termination Clause**: Current "at-will termination" violates enterprise policy
2. **Liability Limitation**: Excessive liability waiver not acceptable
3. **Data Protection**: Missing GDPR compliance requirements

**Risk Assessment:** HIGH RISK - Multiple policy violations detected

**Recommended Revisions:**
1. **Termination Rights**: 
   - Original: "Provider may terminate at will"
   - Revised: "Either party may terminate with 90-day written notice and 30-day cure period"

2. **Liability Protection**:
   - Add mutual liability caps at contract value
   - Exclude gross negligence and willful misconduct

3. **Data Compliance**:
   - Include GDPR compliance certification
   - Add data breach notification requirements (72-hour)

**Compliance Status:** REQUIRES REVISION - Contract cannot proceed without addressing violations.""",

            "forecast": """**Budget Forecast Analysis**

**Current Quarter Performance:**
- Planned Spend: ${planned_spend:,}
- Budget Allocation: ${budget:,}
- Variance: {variance}% {"OVER" if variance > 0 else "UNDER"} budget

**Forecast Projections:**
- Q1 Projected Spend: ${q1_proj:,}
- Q2 Projected Spend: ${q2_proj:,}
- Annual Forecast: ${annual:,}

**Risk Indicators:**
{"🔴 HIGH RISK: Significant budget overrun projected" if variance > 15 else "🟡 MEDIUM RISK: Monitor spending closely" if variance > 5 else "🟢 LOW RISK: Spending within acceptable range"}

**Recommendations:**
1. **Cost Optimization**: Negotiate volume discounts for Q2 purchases
2. **Budget Reallocation**: Consider shifting 10% from hardware to software category
3. **Approval Process**: Implement additional approval for purchases >$25K
4. **Vendor Consolidation**: Reduce vendor count by 20% for better pricing

**Action Items:**
- Review and approve budget variance by {date}
- Implement cost controls for remaining quarters
- Schedule monthly budget review meetings"""
        }
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Generate a mock response based on the agent type."""
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Determine response type from context
        agent_type = "negotiation"  # default
        if context:
            if "clause" in context or "compliance" in prompt.lower():
                agent_type = "compliance"
            elif "budget" in context or "forecast" in prompt.lower():
                agent_type = "forecast"
            elif "vendor" in context or "discount" in prompt.lower():
                agent_type = "negotiation"
        
        # Get base response
        response_template = self.demo_responses.get(agent_type, self.demo_responses["negotiation"])
        
        # Format with context data
        try:
            if agent_type == "negotiation" and context:
                response = response_template.format(
                    discount=context.get("target_discount_pct", 15)
                )
            elif agent_type == "forecast" and context:
                planned = context.get("planned_spend", 50000)
                budget = context.get("current_budget", 75000)
                variance = ((planned - budget) / budget * 100) if budget > 0 else 0
                response = response_template.format(
                    planned_spend=planned,
                    budget=budget,
                    variance=abs(variance),
                    q1_proj=int(planned * 1.1),
                    q2_proj=int(planned * 1.05),
                    annual=int(planned * 4.2),
                    date="2024-03-15"
                )
            else:
                response = response_template
        except (KeyError, ValueError):
            response = response_template
        
        return LLMResponse(
            content=response,
            model="mock-llm-demo",
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response.split()),
                "total_tokens": len(prompt.split()) + len(response.split())
            },
            finish_reason="stop"
        )
    
    async def verify_connection(self) -> bool:
        """Mock connection verification."""
        return True
    
    async def verify_model(self) -> bool:
        """Mock model verification."""
        return True
    
    def reset_connection(self):
        """Mock connection reset."""
        pass