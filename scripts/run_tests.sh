#!/bin/bash

# ProcureSense Test Execution Script
# This script provides easy test execution for different scenarios

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL=${PROCURESENSE_URL:-"http://localhost:8000"}
TIMEOUT=${TIMEOUT:-60}

echo -e "${BLUE}🚀 ProcureSense Test Suite${NC}"
echo "=================================="
echo "Base URL: $BASE_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Function to check if system is running
check_system() {
    echo -e "${YELLOW}🔍 Checking if ProcureSense is running...${NC}"
    
    for i in $(seq 1 $TIMEOUT); do
        if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ System is running!${NC}"
            return 0
        fi
        
        if [ $i -eq 1 ]; then
            echo -e "${YELLOW}⏳ Waiting for system to start...${NC}"
        fi
        
        sleep 1
    done
    
    echo -e "${RED}❌ System not responding after ${TIMEOUT}s${NC}"
    return 1
}

# Function to run unit tests
run_unit_tests() {
    echo -e "${BLUE}🧪 Running Unit Tests${NC}"
    echo "------------------------"
    
    python -m pytest tests/unit/ -v --tb=short --durations=10
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Unit tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Unit tests failed!${NC}"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${BLUE}🔗 Running Integration Tests${NC}"
    echo "------------------------------"
    
    python -m pytest tests/integration/ -v --tb=short
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Integration tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Integration tests failed!${NC}"
        return 1
    fi
}

# Function to run system tests
run_system_tests() {
    echo -e "${BLUE}🌐 Running System Tests${NC}"
    echo "------------------------"
    
    if ! check_system; then
        echo -e "${RED}❌ Cannot run system tests - system not available${NC}"
        return 1
    fi
    
    python -m pytest tests/system/ -v --tb=short -s
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ System tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ System tests failed!${NC}"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    echo -e "${BLUE}⚡ Running Performance Tests${NC}"
    echo "-----------------------------"
    
    if ! check_system; then
        echo -e "${RED}❌ Cannot run performance tests - system not available${NC}"
        return 1
    fi
    
    python tests/performance/load_test.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Performance tests completed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Performance tests failed!${NC}"
        return 1
    fi
}

# Function to run API validation
run_api_validation() {
    echo -e "${BLUE}🔍 Running API Validation${NC}"
    echo "--------------------------"
    
    if ! check_system; then
        echo -e "${RED}❌ Cannot run API validation - system not available${NC}"
        return 1
    fi
    
    # Health check
    echo "Testing health endpoint..."
    if curl -s -f "$BASE_URL/health" | jq -e '.status == "healthy"' > /dev/null; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${RED}❌ Health check failed${NC}"
        return 1
    fi
    
    # Agent status
    echo "Testing agent status..."
    if curl -s -f "$BASE_URL/status/agents" | jq -e 'has("negotiation")' > /dev/null; then
        echo -e "${GREEN}✅ Agent status passed${NC}"
    else
        echo -e "${RED}❌ Agent status failed${NC}"
        return 1
    fi
    
    # Integration metrics
    echo "Testing integration metrics..."
    if curl -s -f "$BASE_URL/integration/metrics" | jq -e 'has("overview")' > /dev/null; then
        echo -e "${GREEN}✅ Integration metrics passed${NC}"
    else
        echo -e "${RED}❌ Integration metrics failed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ API validation completed!${NC}"
    return 0
}

# Function to run manual test examples
run_manual_examples() {
    echo -e "${BLUE}📋 Running Manual Test Examples${NC}"
    echo "--------------------------------"
    
    if ! check_system; then
        echo -e "${RED}❌ Cannot run manual examples - system not available${NC}"
        return 1
    fi
    
    echo "1. Testing Negotiation Agent..."
    curl -X POST "$BASE_URL/agent/negotiation" \
        -H "Content-Type: application/json" \
        -d '{
            "vendor": "TestVendor",
            "target_discount_pct": 15.0,
            "category": "software",
            "context": "Test negotiation"
        }' | jq '.'
    
    echo -e "\n2. Testing Compliance Agent..."
    curl -X POST "$BASE_URL/agent/compliance" \
        -H "Content-Type: application/json" \
        -d '{
            "clause": "Standard terms and conditions with warranty coverage.",
            "contract_type": "software_license",
            "risk_tolerance": "medium"
        }' | jq '.'
    
    echo -e "\n3. Testing Forecast Agent..."
    curl -X POST "$BASE_URL/agent/forecast" \
        -H "Content-Type: application/json" \
        -d '{
            "category": "software",
            "quarter": "Q1 2024",
            "planned_spend": 45000.0,
            "current_budget": 50000.0
        }' | jq '.'
    
    echo -e "${GREEN}✅ Manual examples completed!${NC}"
    return 0
}

# Main execution logic
case "${1:-all}" in
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "system")
        run_system_tests
        ;;
    "performance")
        run_performance_tests
        ;;
    "api")
        run_api_validation
        ;;
    "manual")
        run_manual_examples
        ;;
    "all")
        echo -e "${BLUE}🎯 Running All Test Suites${NC}"
        echo "============================"
        
        success=true
        
        # Run unit tests first (don't need system)
        if ! run_unit_tests; then
            success=false
        fi
        
        echo ""
        
        # Run integration tests
        if ! run_integration_tests; then
            success=false
        fi
        
        echo ""
        
        # Run API validation
        if ! run_api_validation; then
            success=false
        fi
        
        echo ""
        
        # Run system tests
        if ! run_system_tests; then
            success=false
        fi
        
        echo ""
        
        # Run performance tests
        if ! run_performance_tests; then
            success=false
        fi
        
        echo ""
        echo "=================================="
        if [ "$success" = true ]; then
            echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
            echo -e "${GREEN}System is ready for production.${NC}"
            exit 0
        else
            echo -e "${RED}❌ Some tests failed.${NC}"
            echo -e "${YELLOW}Review the results before deployment.${NC}"
            exit 1
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Test types:"
        echo "  unit         - Run unit tests only"
        echo "  integration  - Run integration tests only"
        echo "  system       - Run system tests only"
        echo "  performance  - Run performance tests only"
        echo "  api          - Run API validation only"
        echo "  manual       - Run manual test examples"
        echo "  all          - Run all test suites (default)"
        echo "  help         - Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  PROCURESENSE_URL - Base URL for API (default: http://localhost:8000)"
        echo "  TIMEOUT          - Timeout for system readiness (default: 60s)"
        ;;
    *)
        echo -e "${RED}❌ Unknown test type: $1${NC}"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac