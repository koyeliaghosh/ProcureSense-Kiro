@echo off
REM ProcureSense Test Execution Script for Windows
REM This script provides easy test execution for different scenarios

setlocal enabledelayedexpansion

REM Configuration
if "%PROCURESENSE_URL%"=="" set PROCURESENSE_URL=http://localhost:8000
if "%TIMEOUT%"=="" set TIMEOUT=60

echo 🚀 ProcureSense Test Suite
echo ==================================
echo Base URL: %PROCURESENSE_URL%
echo Timeout: %TIMEOUT%s
echo.

REM Function to check if system is running
:check_system
echo 🔍 Checking if ProcureSense is running...

for /L %%i in (1,1,%TIMEOUT%) do (
    curl -s -f "%PROCURESENSE_URL%/health" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ System is running!
        goto :eof
    )
    
    if %%i equ 1 (
        echo ⏳ Waiting for system to start...
    )
    
    timeout /t 1 /nobreak >nul
)

echo ❌ System not responding after %TIMEOUT%s
exit /b 1

REM Main execution logic
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

if "%TEST_TYPE%"=="unit" goto run_unit_tests
if "%TEST_TYPE%"=="integration" goto run_integration_tests
if "%TEST_TYPE%"=="system" goto run_system_tests
if "%TEST_TYPE%"=="performance" goto run_performance_tests
if "%TEST_TYPE%"=="api" goto run_api_validation
if "%TEST_TYPE%"=="manual" goto run_manual_examples
if "%TEST_TYPE%"=="all" goto run_all_tests
if "%TEST_TYPE%"=="help" goto show_help
if "%TEST_TYPE%"=="-h" goto show_help
if "%TEST_TYPE%"=="--help" goto show_help

echo ❌ Unknown test type: %TEST_TYPE%
echo Use '%0 help' for usage information.
exit /b 1

:run_unit_tests
echo 🧪 Running Unit Tests
echo ------------------------
python -m pytest tests/unit/ -v --tb=short --durations=10
if %errorlevel% equ 0 (
    echo ✅ Unit tests passed!
) else (
    echo ❌ Unit tests failed!
    exit /b 1
)
goto :eof

:run_integration_tests
echo 🔗 Running Integration Tests
echo ------------------------------
python -m pytest tests/integration/ -v --tb=short
if %errorlevel% equ 0 (
    echo ✅ Integration tests passed!
) else (
    echo ❌ Integration tests failed!
    exit /b 1
)
goto :eof

:run_system_tests
echo 🌐 Running System Tests
echo ------------------------
call :check_system
if %errorlevel% neq 0 (
    echo ❌ Cannot run system tests - system not available
    exit /b 1
)

python -m pytest tests/system/ -v --tb=short -s
if %errorlevel% equ 0 (
    echo ✅ System tests passed!
) else (
    echo ❌ System tests failed!
    exit /b 1
)
goto :eof

:run_performance_tests
echo ⚡ Running Performance Tests
echo -----------------------------
call :check_system
if %errorlevel% neq 0 (
    echo ❌ Cannot run performance tests - system not available
    exit /b 1
)

python tests/performance/load_test.py
if %errorlevel% equ 0 (
    echo ✅ Performance tests completed!
) else (
    echo ❌ Performance tests failed!
    exit /b 1
)
goto :eof

:run_api_validation
echo 🔍 Running API Validation
echo --------------------------
call :check_system
if %errorlevel% neq 0 (
    echo ❌ Cannot run API validation - system not available
    exit /b 1
)

echo Testing health endpoint...
curl -s -f "%PROCURESENSE_URL%/health" >nul
if %errorlevel% equ 0 (
    echo ✅ Health check passed
) else (
    echo ❌ Health check failed
    exit /b 1
)

echo Testing agent status...
curl -s -f "%PROCURESENSE_URL%/status/agents" >nul
if %errorlevel% equ 0 (
    echo ✅ Agent status passed
) else (
    echo ❌ Agent status failed
    exit /b 1
)

echo Testing integration metrics...
curl -s -f "%PROCURESENSE_URL%/integration/metrics" >nul
if %errorlevel% equ 0 (
    echo ✅ Integration metrics passed
) else (
    echo ❌ Integration metrics failed
    exit /b 1
)

echo ✅ API validation completed!
goto :eof

:run_manual_examples
echo 📋 Running Manual Test Examples
echo --------------------------------
call :check_system
if %errorlevel% neq 0 (
    echo ❌ Cannot run manual examples - system not available
    exit /b 1
)

echo 1. Testing Negotiation Agent...
curl -X POST "%PROCURESENSE_URL%/agent/negotiation" -H "Content-Type: application/json" -d "{\"vendor\":\"TestVendor\",\"target_discount_pct\":15.0,\"category\":\"software\",\"context\":\"Test negotiation\"}"

echo.
echo 2. Testing Compliance Agent...
curl -X POST "%PROCURESENSE_URL%/agent/compliance" -H "Content-Type: application/json" -d "{\"clause\":\"Standard terms and conditions with warranty coverage.\",\"contract_type\":\"software_license\",\"risk_tolerance\":\"medium\"}"

echo.
echo 3. Testing Forecast Agent...
curl -X POST "%PROCURESENSE_URL%/agent/forecast" -H "Content-Type: application/json" -d "{\"category\":\"software\",\"quarter\":\"Q1 2024\",\"planned_spend\":45000.0,\"current_budget\":50000.0}"

echo.
echo ✅ Manual examples completed!
goto :eof

:run_all_tests
echo 🎯 Running All Test Suites
echo ============================

set success=true

REM Run unit tests first (don't need system)
call :run_unit_tests
if %errorlevel% neq 0 set success=false

echo.

REM Run integration tests
call :run_integration_tests
if %errorlevel% neq 0 set success=false

echo.

REM Run API validation
call :run_api_validation
if %errorlevel% neq 0 set success=false

echo.

REM Run system tests
call :run_system_tests
if %errorlevel% neq 0 set success=false

echo.

REM Run performance tests
call :run_performance_tests
if %errorlevel% neq 0 set success=false

echo.
echo ==================================
if "%success%"=="true" (
    echo 🎉 ALL TESTS PASSED!
    echo System is ready for production.
    exit /b 0
) else (
    echo ❌ Some tests failed.
    echo Review the results before deployment.
    exit /b 1
)

:show_help
echo Usage: %0 [test_type]
echo.
echo Test types:
echo   unit         - Run unit tests only
echo   integration  - Run integration tests only
echo   system       - Run system tests only
echo   performance  - Run performance tests only
echo   api          - Run API validation only
echo   manual       - Run manual test examples
echo   all          - Run all test suites (default)
echo   help         - Show this help message
echo.
echo Environment variables:
echo   PROCURESENSE_URL - Base URL for API (default: http://localhost:8000)
echo   TIMEOUT          - Timeout for system readiness (default: 60s)
goto :eof