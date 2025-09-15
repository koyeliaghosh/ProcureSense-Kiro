#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Quick test
try:
    from src.api.dependencies import get_agent_service
    from src.agents.agent_types import AgentRequest
    from src.models.base_types import AgentType
    
    agent_service = get_agent_service()
    agent = agent_service.get_negotiation_agent()
    
    # Test with percentage format (like web form sends)
    request = AgentRequest(
        agent_type=AgentType.NEGOTIATION,
        session_id="test",
        payload={"vendor": "Test", "target_discount_pct": 15.0, "category": "software", "context": None}
    )
    
    result = agent.process_request(request)
    print(f"✅ SUCCESS! Response length: {len(result.agent_response)}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")