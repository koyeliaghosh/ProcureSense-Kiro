---
inclusion: always
description: "Guidelines for multi-agent coordination and workflow management"
---

# Agent Coordination and Workflow Management

## Multi-Agent Workflow Principles

### Sequential Processing
When agents need to work in sequence:
1. **Negotiation Agent** → Initial analysis and strategy
2. **Compliance Agent** → Policy validation and risk assessment  
3. **Forecast Agent** → Budget impact and timing analysis
4. **GP Critic** → Final review and recommendation synthesis

### Parallel Processing
When agents can work simultaneously:
- Negotiation and Forecast agents can analyze different aspects
- Compliance validation can run parallel to cost analysis
- Market research can occur alongside contract review

### Information Sharing
- All agents share common context through the Context Manager
- Critical findings are propagated to subsequent agents
- Conflicts between agent recommendations are escalated to GP Critic

## Agent Interaction Protocols

### Negotiation Agent Coordination
- **Input Dependencies**: Market data, budget constraints, compliance requirements
- **Output Sharing**: Pricing strategies, terms recommendations, risk assessments
- **Escalation**: Complex negotiations requiring legal review

### Compliance Agent Coordination  
- **Input Dependencies**: Contract terms, policy updates, regulatory changes
- **Output Sharing**: Compliance status, violation alerts, remediation suggestions
- **Escalation**: Policy violations requiring executive approval

### Forecast Agent Coordination
- **Input Dependencies**: Historical data, market trends, budget allocations
- **Output Sharing**: Budget forecasts, variance alerts, timing recommendations
- **Escalation**: Significant budget variances or market disruptions

### GP Critic Coordination
- **Input Dependencies**: All agent outputs, enterprise policies, strategic objectives
- **Output Sharing**: Final recommendations, conflict resolutions, strategic guidance
- **Escalation**: Strategic decisions requiring board or executive input

## Workflow Orchestration

### Standard Procurement Workflow
```yaml
workflow_steps:
  1. intake:
      agent: "system"
      action: "validate_request"
      
  2. initial_analysis:
      agent: "negotiation"
      action: "analyze_requirements"
      
  3. compliance_check:
      agent: "compliance"  
      action: "validate_policies"
      depends_on: [2]
      
  4. budget_analysis:
      agent: "forecast"
      action: "analyze_budget_impact"
      depends_on: [2]
      
  5. final_review:
      agent: "gp_critic"
      action: "synthesize_recommendations"
      depends_on: [3, 4]
```

### Emergency Procurement Workflow
```yaml
emergency_workflow:
  1. rapid_assessment:
      agents: ["negotiation", "compliance"]
      parallel: true
      timeout: 15_minutes
      
  2. expedited_review:
      agent: "gp_critic"
      action: "emergency_approval"
      depends_on: [1]
      timeout: 5_minutes
```

## Context Management

### Shared Context Elements
- **Enterprise Policies**: Always available to all agents
- **Budget Information**: Shared between Negotiation and Forecast agents
- **Vendor History**: Available to Negotiation and Compliance agents
- **Market Data**: Shared between Negotiation and Forecast agents

### Agent-Specific Context
- **Negotiation**: Vendor relationships, pricing history, contract terms
- **Compliance**: Policy violations, audit findings, regulatory updates
- **Forecast**: Budget variances, spending patterns, market trends
- **GP Critic**: Strategic objectives, risk tolerance, decision history

## Error Handling and Recovery

### Agent Failure Scenarios
- **Timeout**: Escalate to human review after configured timeout
- **Conflict**: GP Critic arbitrates between conflicting recommendations
- **Data Unavailable**: Proceed with available information, flag limitations
- **Policy Violation**: Block transaction, require manual override

### Recovery Procedures
1. **Automatic Retry**: For transient failures (network, temporary unavailability)
2. **Fallback Mode**: Use cached data or simplified analysis
3. **Human Escalation**: For complex scenarios requiring judgment
4. **Audit Trail**: Maintain complete record of all decisions and failures

## Performance Monitoring

### Key Metrics
- **Response Time**: Target <30 seconds for standard workflows
- **Accuracy**: >95% compliance with enterprise policies
- **Consistency**: <5% variance in similar scenario recommendations
- **Availability**: >99.5% uptime for all agents

### Quality Assurance
- **Cross-Validation**: Agents validate each other's outputs
- **Feedback Loops**: Learn from human overrides and corrections
- **Continuous Improvement**: Regular model updates and retraining
- **Audit Reviews**: Periodic assessment of decision quality

This framework ensures efficient, accurate, and reliable multi-agent coordination for all procurement scenarios.