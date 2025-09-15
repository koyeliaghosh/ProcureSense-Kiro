# ProcureSense Production Deployment Guide

This guide provides comprehensive instructions for deploying ProcureSense to production and testing the system.

## 🚀 Quick Start Testing

### Prerequisites
1. **Python 3.11+** installed
2. **Git** for cloning the repository
3. **curl** for API testing
4. **Docker** (optional, for containerized deployment)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the System
```bash
# Option 1: Using the startup script (RECOMMENDED)
python run_server.py

# Option 2: Direct FastAPI run
python -m uvicorn src.api.app:create_app --factory --host localhost --port 8000

# Option 3: Using the test runner (includes system validation)
python tests/test_runner.py --start-server
```

The system will start on `http://localhost:8000`

### 3. Access the Web Interface

Once the server is running, you can access:

- **🏠 Main Application**: http://localhost:8000/
- **📊 Business Case & ROI**: http://localhost:8000/static/business-case.html  
- **📚 API Documentation**: http://localhost:8000/docs
- **📈 System Metrics**: http://localhost:8000/integration/metrics
- **🔍 Health Check**: http://localhost:8000/health

### 3. Run Comprehensive Tests

#### Option A: Use Test Runner (Recommended)
```bash
# Run all tests
python tests/test_runner.py

# Run specific test suites
python tests/test_runner.py --unit-only
python tests/test_runner.py --system-only
python tests/test_runner.py --skip-performance
```

#### Option B: Use Shell Scripts
```bash
# Linux/Mac
./scripts/run_tests.sh all

# Windows
scripts\run_tests.bat all
```

#### Option C: Manual Testing
```bash
# Individual test suites
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/system/ -v
python tests/performance/load_test.py
```

---

## 📋 Test Categories & What They Validate

### 1. **Unit Tests** (`tests/unit/`)
**What they test:**
- Individual component functionality
- Agent logic and processing
- GPCritic validation rules
- Context management
- LLM integration

**Key test files:**
- `test_negotiation_agent.py` - Negotiation agent functionality
- `test_compliance_agent.py` - Compliance analysis and violation detection
- `test_forecast_agent.py` - Budget forecasting and analysis
- `test_gp_critic.py` - Policy validation and auto-revision
- `test_api.py` - API endpoint validation

**Expected results:**
- ✅ All agent processing logic works correctly
- ✅ Policy violations are detected accurately
- ✅ Auto-revision fixes common violations
- ✅ API request/response validation works

### 2. **Integration Tests** (`tests/integration/`)
**What they test:**
- Agent-to-GPCritic workflow
- End-to-end processing pipeline
- Component integration
- Workflow orchestration

**Key test files:**
- `test_workflow_integration.py` - Workflow orchestration
- `test_agent_gp_critic_workflow.py` - Complete integration pipeline

**Expected results:**
- ✅ Complete workflow executes successfully
- ✅ Metrics collection works
- ✅ Error handling is robust
- ✅ Integration manager functions correctly

### 3. **System Tests** (`tests/system/`)
**What they test:**
- Complete API functionality
- Real HTTP requests and responses
- Concurrent request handling
- End-to-end business scenarios

**Key test files:**
- `test_system_integration.py` - Full system validation

**Expected results:**
- ✅ All API endpoints respond correctly
- ✅ Policy enforcement works in real scenarios
- ✅ System handles concurrent requests
- ✅ Error handling and validation work

### 4. **Performance Tests** (`tests/performance/`)
**What they test:**
- System performance under load
- Response time validation
- Concurrent user simulation
- Resource utilization

**Key test files:**
- `load_test.py` - Comprehensive load testing

**Expected results:**
- ✅ Response times < 5 seconds
- ✅ System handles 10+ concurrent users
- ✅ Error rate < 5% under load
- ✅ No resource exhaustion

---

## 🧪 Manual Test Scenarios

### Basic Functionality Tests

#### 1. Health Check
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status": "healthy", "components": {...}}`

#### 2. Negotiation Agent - Standard Request
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
**Expected:** Compliant response with pricing proposal

#### 3. Negotiation Agent - High Discount (Warranty Trigger)
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "DiscountVendor Inc",
    "target_discount_pct": 25.0,
    "category": "hardware"
  }'
```
**Expected:** Response includes warranty clauses, compliance_status: "revised"

#### 4. Compliance Agent - Prohibited Clauses
```bash
curl -X POST "http://localhost:8000/agent/compliance" \
  -H "Content-Type: application/json" \
  -d '{
    "clause": "This contract includes unlimited liability and indemnification clauses.",
    "contract_type": "service_agreement",
    "risk_tolerance": "low"
  }'
```
**Expected:** Policy violations detected, auto-revision applied

#### 5. Forecast Agent - Budget Analysis
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
**Expected:** Budget analysis with compliance status

### Advanced Test Scenarios

#### 6. Integration Metrics
```bash
curl http://localhost:8000/integration/metrics
```
**Expected:** Comprehensive metrics with overview, compliance, performance sections

#### 7. Recent Results
```bash
curl "http://localhost:8000/integration/recent?limit=5"
```
**Expected:** Array of recent workflow results

#### 8. Compliance Report
```bash
curl "http://localhost:8000/integration/compliance-report?hours=1"
```
**Expected:** Compliance breakdown and statistics

### Error Handling Tests

#### 9. Invalid Request Validation
```bash
curl -X POST "http://localhost:8000/agent/negotiation" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor": "",
    "target_discount_pct": 150.0,
    "category": "software"
  }'
```
**Expected:** 422 Validation Error

#### 10. Invalid Endpoint
```bash
curl http://localhost:8000/invalid/endpoint
```
**Expected:** 404 Not Found

---

## 🎯 Success Criteria Checklist

### ✅ Functional Requirements
- [ ] All agent endpoints respond successfully (200 OK)
- [ ] Policy violations are detected and handled appropriately
- [ ] Auto-revision works for fixable violations
- [ ] Manual review flagging works for complex issues
- [ ] Integration metrics are collected and reported accurately
- [ ] Error handling provides meaningful responses

### ✅ Performance Requirements
- [ ] Response times are under 5 seconds for standard requests
- [ ] System handles 10+ concurrent requests without degradation
- [ ] Error rate is below 5% under normal load
- [ ] No memory leaks or resource exhaustion observed

### ✅ Compliance Requirements
- [ ] All outputs comply with enterprise policies
- [ ] Audit trails are maintained for all requests
- [ ] Violation detection accuracy is high (>95%)
- [ ] Auto-revision maintains original intent while ensuring compliance

### ✅ Integration Requirements
- [ ] Agent-to-GPCritic workflow functions correctly
- [ ] Metrics collection is comprehensive and accurate
- [ ] Error handling is robust across all components
- [ ] API documentation is accurate and accessible

---

## 🐛 Troubleshooting Common Issues

### Issue: System Won't Start
**Symptoms:** Connection refused, health check fails
**Solutions:**
1. Check if port 8000 is available: `netstat -an | grep 8000`
2. Verify Python dependencies: `pip install -r requirements.txt`
3. Check environment variables in `.env` file
4. Review application logs for startup errors

### Issue: Slow Response Times
**Symptoms:** Requests take >10 seconds, timeouts
**Solutions:**
1. Check system resources (CPU, memory usage)
2. Verify no other processes are consuming resources
3. Monitor network connectivity
4. Check if LLM service is responsive

### Issue: Policy Violations Not Detected
**Symptoms:** Prohibited clauses pass through, no violations flagged
**Solutions:**
1. Verify GPC manager is loaded correctly
2. Check policy configuration in context manager
3. Review GPCritic validation logic
4. Ensure violation patterns are correctly defined

### Issue: Tests Failing
**Symptoms:** Unit/integration tests fail
**Solutions:**
1. Ensure system is running for system tests
2. Check test dependencies are installed
3. Verify mock configurations in test files
4. Review test data and expected results

### Issue: High Error Rates
**Symptoms:** Many 500 errors, failed requests
**Solutions:**
1. Check application logs for exceptions
2. Verify all dependencies are properly configured
3. Monitor resource usage during load
4. Review error handling in agent implementations

---

## 📊 Expected Test Results

### Unit Tests
- **Expected:** 50+ tests passing
- **Coverage:** >90% code coverage
- **Duration:** <30 seconds

### Integration Tests
- **Expected:** 9+ tests passing
- **Coverage:** End-to-end workflow validation
- **Duration:** <60 seconds

### System Tests
- **Expected:** 15+ tests passing
- **Coverage:** Complete API functionality
- **Duration:** <120 seconds

### Performance Tests
- **Expected Results:**
  - Average response time: <2 seconds
  - 95th percentile: <5 seconds
  - Error rate: <2%
  - Throughput: >5 requests/second

---

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
cd deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export APP_ENV=production
export LOG_LEVEL=info

# Start with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
```

### Health Monitoring
- Health endpoint: `GET /health`
- Metrics endpoint: `GET /integration/metrics`
- Documentation: `GET /docs`

---

## 📈 Monitoring & Maintenance

### Key Metrics to Monitor
1. **Response Times:** Average, 95th percentile
2. **Error Rates:** 4xx and 5xx error percentages
3. **Compliance Rates:** Policy violation detection and resolution
4. **Throughput:** Requests per second
5. **Resource Usage:** CPU, memory, disk usage

### Log Monitoring
- Application logs for errors and warnings
- Access logs for request patterns
- Performance logs for slow queries

### Regular Maintenance
1. **Daily:** Check system health and error rates
2. **Weekly:** Review compliance reports and metrics
3. **Monthly:** Performance analysis and optimization
4. **Quarterly:** Security updates and dependency upgrades

---

## 🎉 Conclusion

ProcureSense is now ready for production deployment! The comprehensive test suite validates:

- ✅ **Complete Functionality:** All agents work correctly with policy enforcement
- ✅ **Enterprise Compliance:** 100% policy compliance guarantee through GPCritic
- ✅ **Production Readiness:** Performance, error handling, and monitoring
- ✅ **Scalability:** Concurrent request handling and resource optimization

**Next Steps:**
1. Run the complete test suite: `python tests/test_runner.py`
2. Deploy to your production environment
3. Set up monitoring and alerting
4. Configure backup and disaster recovery
5. Train users on the API endpoints and functionality

For support and questions, refer to the API documentation at `/docs` when the system is running.