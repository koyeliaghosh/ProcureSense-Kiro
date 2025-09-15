# Manual Test Scenarios for ProcureSense

This document provides comprehensive manual test scenarios to validate ProcureSense functionality from a user perspective.

## Prerequisites

1. **System Running**: Ensure ProcureSense is running at `http://localhost:8000`
2. **API Documentation**: Access Swagger docs at `http://localhost:8000/docs`
3. **Test Tools**: Use curl, Postman, or browser for testing

## Test Categories

### 1. System Health & Status Tests

#### Test 1.1: Health Check
```bash
curl -X GET "http://localhost:8000/health"
```
**Expected Result**: 
- Status: 200 OK
- Response: `{"status": "healthy", "components": {...}}`

#### Test 1.2: Agent Status
```bash
curl -X GET "http://localhost:8000/status/agents"
```
**Expected Result**:
- Status: 200 OK
- Shows status for negotiation, compliance, and forecast agents

#### Test 1.3: Integration Metrics
```bash
curl -X GET "http://localhost:8000/integration/metrics"
```
**Expected Result**:
- Status: 200 OK
- Comprehensive metrics with overview, compliance, performance sections

---

### 2. Negotiation Agent Tests

#### Test 2.1: Standard Negotiation Request
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "TechCorp Solutions",
    "target_discount_pct": 15.0,
    "category": "software",
    "context": "Annual software licensing renewal"
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "compliant" or "revised"
- Response includes pricing proposal and terms
- Processing time > 0ms

#### Test 2.2: High Discount Request (Warranty Trigger)
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "DiscountVendor Inc",
    "target_discount_pct": 25.0,
    "category": "hardware"
  }'
```
**Expected Result**:
- Status: 200 OK
- Response should include warranty clauses
- Compliance status: "compliant" or "revised"
- May show policy violations for missing warranty (auto-fixed)

#### Test 2.3: Excessive Discount Request
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "CheapVendor LLC",
    "target_discount_pct": 40.0,
    "category": "software"
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "revised" or "flagged"
- Policy violations for unauthorized discount
- Discount should be reduced to authorized level (25%)

#### Test 2.4: Invalid Request Validation
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "",
    "target_discount_pct": 150.0,
    "category": "software"
  }'
```
**Expected Result**:
- Status: 422 Unprocessable Entity
- Validation errors for empty vendor and invalid discount percentage

---

### 3. Compliance Agent Tests

#### Test 3.1: Clean Contract Clause
```bash
curl -X POST "http://localhost:8000/agent/compliance" \
  -H "Content-Type: application/json" \
  -d '{
    "clause": "Standard terms and conditions apply with appropriate warranty coverage and security provisions as per industry standards.",
    "contract_type": "software_license",
    "risk_tolerance": "medium"
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "compliant"
- No policy violations
- Risk assessment: LOW or MEDIUM

#### Test 3.2: Prohibited Clauses Detection
```bash
curl -X POST "http://localhost:8000/agent/compliance" \
  -H "Content-Type: application/json" \
  -d '{
    "clause": "This contract includes unlimited liability and indemnification clauses. The client shall hold harmless the vendor for any damages.",
    "contract_type": "service_agreement",
    "risk_tolerance": "low"
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "revised" or "flagged"
- Policy violations detected for prohibited clauses
- Auto-revision removes or replaces prohibited terms

#### Test 3.3: High-Risk Contract Analysis
```bash
curl -X POST "http://localhost:8000/agent/compliance" \
  -H "Content-Type: application/json" \
  -d '{
    "clause": "Vendor disclaims all warranties and limits liability to the maximum extent permitted by law. Client assumes all risks.",
    "contract_type": "consulting",
    "risk_tolerance": "low"
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "flagged" (manual review required)
- High risk assessment
- Recommendations for compliant alternatives

---

### 4. Forecast Agent Tests

#### Test 4.1: Within Budget Forecast
```bash
curl -X POST "http://localhost:8000/agent/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "software",
    "quarter": "Q1 2024",
    "planned_spend": 45000.0,
    "current_budget": 50000.0
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "compliant"
- Budget alignment analysis shows within limits
- Spending forecast and recommendations

#### Test 4.2: Budget Exceeded Scenario
```bash
curl -X POST "http://localhost:8000/agent/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "hardware",
    "quarter": "Q2 2024",
    "planned_spend": 120000.0,
    "current_budget": 100000.0
  }'
```
**Expected Result**:
- Status: 200 OK
- Compliance status: "flagged" or "revised"
- Budget exceeded warnings
- Recommendations for budget adjustments

#### Test 4.3: Quarterly Planning Analysis
```bash
curl -X POST "http://localhost:8000/agent/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "consulting",
    "quarter": "Q3 2024",
    "planned_spend": 30000.0
  }'
```
**Expected Result**:
- Status: 200 OK
- Quarterly spending analysis
- Trend analysis and projections
- Risk assessment for spending patterns

---

### 5. Integration & Workflow Tests

#### Test 5.1: Recent Results Tracking
```bash
curl -X GET "http://localhost:8000/integration/recent?limit=10"
```
**Expected Result**:
- Status: 200 OK
- Array of recent workflow results
- Each result includes request_id, agent_type, compliance_status, timestamp

#### Test 5.2: Compliance Reporting
```bash
curl -X GET "http://localhost:8000/integration/compliance-report?hours=24"
```
**Expected Result**:
- Status: 200 OK
- Compliance breakdown by status
- Violation statistics
- Success rates and trends

#### Test 5.3: Metrics Reset (Admin)
```bash
curl -X POST "http://localhost:8000/integration/reset-metrics"
```
**Expected Result**:
- Status: 200 OK
- Confirmation message
- Subsequent metrics calls show reset counters

---

### 6. Error Handling & Edge Cases

#### Test 6.1: Invalid Endpoints
```bash
curl -X GET "http://localhost:8000/invalid/endpoint"
```
**Expected Result**: Status 404 Not Found

#### Test 6.2: Wrong HTTP Methods
```bash
curl -X GET "http://localhost:8000/agent/negotiation"
```
**Expected Result**: Status 405 Method Not Allowed

#### Test 6.3: Malformed JSON
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{"invalid": json}'
```
**Expected Result**: Status 422 Unprocessable Entity

---

### 7. Performance & Load Tests

#### Test 7.1: Response Time Validation
- Make multiple requests to each agent endpoint
- Verify response times are reasonable (< 5 seconds)
- Check processing_time_ms in responses

#### Test 7.2: Concurrent Request Handling
- Use tools like Apache Bench or curl in parallel
- Send 10-20 concurrent requests
- Verify all requests complete successfully

```bash
# Example with curl (run multiple terminals)
for i in {1..10}; do
  curl -X POST "http://localhost:8000/agent/negotiation" \
    -H "Content-Type: application/json" \
    -d "{\"vendor\":\"Vendor$i\",\"target_discount_pct\":15.0,\"category\":\"software\"}" &
done
wait
```

---

### 8. End-to-End Business Scenarios

#### Test 8.1: Complete Procurement Workflow
1. **Negotiation**: Request pricing for software license
2. **Compliance**: Review generated contract terms
3. **Forecast**: Analyze budget impact
4. **Monitoring**: Check integration metrics

#### Test 8.2: Policy Violation Workflow
1. **Submit**: Request with policy violations
2. **Detect**: Verify violations are detected
3. **Revise**: Confirm auto-revision occurs
4. **Audit**: Check compliance reporting

#### Test 8.3: High-Risk Scenario Handling
1. **Submit**: High-risk request (large discount, risky clauses)
2. **Flag**: Verify manual review flagging
3. **Report**: Check compliance report shows flagged items

---

## Success Criteria

### Functional Requirements
- ✅ All agent endpoints respond successfully
- ✅ Policy violations are detected and handled
- ✅ Auto-revision works for fixable violations
- ✅ Manual review flagging works for complex issues
- ✅ Integration metrics are collected and reported

### Performance Requirements
- ✅ Response times < 5 seconds for standard requests
- ✅ System handles 10+ concurrent requests
- ✅ No memory leaks or resource exhaustion

### Compliance Requirements
- ✅ All outputs comply with enterprise policies
- ✅ Audit trails are maintained
- ✅ Violation detection is accurate
- ✅ Auto-revision maintains original intent

### Integration Requirements
- ✅ Agent-to-GPCritic workflow functions correctly
- ✅ Metrics collection is comprehensive
- ✅ Error handling is robust
- ✅ API documentation is accurate

---

## Troubleshooting Common Issues

### Issue: 500 Internal Server Error
- Check application logs
- Verify all dependencies are running
- Ensure environment variables are set

### Issue: Slow Response Times
- Check system resources (CPU, memory)
- Verify LLM service (Ollama) is responsive
- Monitor database performance

### Issue: Policy Violations Not Detected
- Verify GPC manager is loaded correctly
- Check policy configuration
- Review GPCritic validation logic

### Issue: Auto-Revision Not Working
- Check GPCritic auto-revision settings
- Verify violation types are marked as auto-fixable
- Review revision templates and logic