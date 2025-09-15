"""
FastAPI application for ProcureSense.

Main application factory and configuration for the ProcureSense API server.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import os

from .models import (
    NegotiationRequest,
    ComplianceRequest,
    ForecastRequest,
    AgentResponse,
    ErrorResponse,
    HealthResponse,
    AgentStatusResponse,
    ContextUsage,
    PolicyViolationInfo,
    ComplianceStatus
)
from .dependencies import get_agent_service, get_gp_critic, get_integration_manager
from ..agents import NegotiationAgent, ComplianceAgent, ForecastAgent
from ..critic import GlobalPolicyCritic
from ..workflow import IntegrationManager
from ..config.settings import get_settings


# Global state for application lifecycle
app_state = {
    "startup_time": None,
    "request_count": 0,
    "agent_stats": {
        "negotiation": {"requests": 0, "total_time": 0.0},
        "compliance": {"requests": 0, "total_time": 0.0},
        "forecast": {"requests": 0, "total_time": 0.0}
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    app_state["startup_time"] = datetime.now()
    print("🚀 ProcureSense API starting up...")
    
    # Initialize components
    try:
        settings = get_settings()
        print(f"📋 Configuration loaded: ProcureSense")
        print(f"🌐 Server will run on {settings.server_host}:{settings.server_port}")
        print("✅ ProcureSense API ready!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 ProcureSense API shutting down...")
    print(f"📊 Total requests processed: {app_state['request_count']}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="ProcureSense API",
        description="Multi-agent procurement co-pilot with enterprise policy compliance",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")
        print(f"📁 Static files mounted from: {static_path}")
    else:
        print(f"⚠️ Static directory not found: {static_path}")
    
    # Add request tracking middleware
    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        start_time = time.time()
        app_state["request_count"] += 1
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(uuid.uuid4())
        
        return response
    
    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="validation_error",
                message="Request validation failed",
                details={"errors": [str(error) for error in exc.errors()]},
                request_id=str(uuid.uuid4())
            ).model_dump()
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="http_error",
                message=exc.detail,
                request_id=str(uuid.uuid4())
            ).model_dump()
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_error",
                message="An internal server error occurred",
                details={"exception": str(exc)},
                request_id=str(uuid.uuid4())
            ).model_dump()
        )
    
    # Root endpoint - serve main app
    @app.get("/")
    async def root():
        """Serve the main application interface."""
        from fastapi.responses import FileResponse
        static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "app.html")
        if os.path.exists(static_path):
            return FileResponse(static_path)
        else:
            return {"message": "ProcureSense API", "docs": "/docs", "static": "/static/app.html"}
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            components={
                "api": "healthy",
                "agents": "healthy",
                "gp_critic": "healthy",
                "llm": "healthy"
            }
        )
    
    # Agent status endpoints
    @app.get("/status/agents", response_model=Dict[str, AgentStatusResponse])
    async def get_agent_status():
        """Get status of all agents."""
        return {
            "negotiation": AgentStatusResponse(
                agent_type="negotiation",
                status="ready",
                total_requests=app_state["agent_stats"]["negotiation"]["requests"],
                average_response_time_ms=_calculate_avg_response_time("negotiation")
            ),
            "compliance": AgentStatusResponse(
                agent_type="compliance", 
                status="ready",
                total_requests=app_state["agent_stats"]["compliance"]["requests"],
                average_response_time_ms=_calculate_avg_response_time("compliance")
            ),
            "forecast": AgentStatusResponse(
                agent_type="forecast",
                status="ready", 
                total_requests=app_state["agent_stats"]["forecast"]["requests"],
                average_response_time_ms=_calculate_avg_response_time("forecast")
            )
        }
    
    # Integration monitoring endpoints
    @app.get("/integration/metrics")
    async def get_integration_metrics(
        integration_manager = Depends(get_integration_manager)
    ):
        """Get comprehensive integration metrics."""
        return integration_manager.get_integration_metrics()
    
    @app.get("/integration/recent")
    async def get_recent_results(
        limit: int = 10,
        integration_manager = Depends(get_integration_manager)
    ):
        """Get recent workflow results."""
        return integration_manager.get_recent_results(limit)
    
    @app.get("/integration/compliance-report")
    async def get_compliance_report(
        hours: int = 24,
        integration_manager = Depends(get_integration_manager)
    ):
        """Get compliance report for specified time period."""
        return integration_manager.get_compliance_report(hours)
    
    @app.post("/integration/reset-metrics")
    async def reset_integration_metrics(
        integration_manager = Depends(get_integration_manager)
    ):
        """Reset integration metrics (admin only)."""
        integration_manager.reset_metrics()
        return {"message": "Integration metrics reset successfully"}

    # Negotiation agent endpoint
    @app.post("/agent/negotiation", response_model=AgentResponse)
    async def negotiate_contract(
        request: NegotiationRequest,
        agent_service = Depends(get_agent_service),
        gp_critic = Depends(get_gp_critic)
    ):
        """
        Process negotiation requests with vendor discount analysis.
        
        Analyzes vendor proposals, generates pricing recommendations,
        and ensures compliance with enterprise policies.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get negotiation agent
            negotiation_agent = agent_service.get_negotiation_agent()
            
            # Process request - create proper AgentRequest object
            from ..agents.agent_types import AgentRequest
            from ..models.base_types import AgentType
            
            agent_request = AgentRequest(
                agent_type=AgentType.NEGOTIATION,
                session_id=request_id,
                payload={
                    "vendor": request.vendor,
                    "target_discount_pct": request.target_discount_pct,  # Already converted by model validator
                    "category": request.category,
                    "context": request.context
                }
            )
            
            agent_result = negotiation_agent.process_request(agent_request)
            
            # Validate with GPCritic
            critic_result = gp_critic.validate_output(
                agent_output=agent_result.agent_response,
                original_request=request.model_dump(),
                agent_type="negotiation"
            )
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            _update_agent_stats("negotiation", processing_time)
            
            # Build response
            return _build_agent_response(
                agent_result=agent_result,
                critic_result=critic_result,
                processing_time_ms=int(processing_time),
                request_id=request_id
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Negotiation processing failed: {str(e)}")
    
    # Compliance agent endpoint
    @app.post("/agent/compliance", response_model=AgentResponse)
    async def analyze_compliance(
        request: ComplianceRequest,
        agent_service = Depends(get_agent_service),
        gp_critic = Depends(get_gp_critic)
    ):
        """
        Analyze contract clauses for compliance violations.
        
        Reviews contract terms, identifies policy violations,
        and provides compliant alternatives.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get compliance agent
            compliance_agent = agent_service.get_compliance_agent()
            
            # Process request - create proper AgentRequest object
            from ..agents.agent_types import AgentRequest
            from ..models.base_types import AgentType
            
            agent_request = AgentRequest(
                agent_type=AgentType.COMPLIANCE,
                session_id=request_id,
                payload={
                    "clause": request.clause,
                    "contract_type": request.contract_type,
                    "risk_tolerance": request.risk_tolerance
                }
            )
            
            agent_result = compliance_agent.process_request(agent_request)
            
            # Validate with GPCritic
            critic_result = gp_critic.validate_output(
                agent_output=agent_result.agent_response,
                original_request=request.model_dump(),
                agent_type="compliance"
            )
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            _update_agent_stats("compliance", processing_time)
            
            # Build response
            return _build_agent_response(
                agent_result=agent_result,
                critic_result=critic_result,
                processing_time_ms=int(processing_time),
                request_id=request_id
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Compliance analysis failed: {str(e)}")
    
    # Forecast agent endpoint
    @app.post("/agent/forecast", response_model=AgentResponse)
    async def forecast_budget(
        request: ForecastRequest,
        agent_service = Depends(get_agent_service),
        gp_critic = Depends(get_gp_critic)
    ):
        """
        Analyze budget forecasts and spending alignment.
        
        Provides spending forecasts, budget variance analysis,
        and alignment recommendations.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get forecast agent
            forecast_agent = agent_service.get_forecast_agent()
            
            # Process request - create proper AgentRequest object
            from ..agents.agent_types import AgentRequest
            from ..models.base_types import AgentType
            
            agent_request = AgentRequest(
                agent_type=AgentType.FORECAST,
                session_id=request_id,
                payload={
                    "category": request.category,
                    "quarter": request.quarter,
                    "planned_spend": request.planned_spend,
                    "current_budget": request.current_budget
                }
            )
            
            agent_result = forecast_agent.process_request(agent_request)
            
            # Validate with GPCritic
            critic_result = gp_critic.validate_output(
                agent_output=agent_result.agent_response,
                original_request=request.model_dump(),
                agent_type="forecast"
            )
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            _update_agent_stats("forecast", processing_time)
            
            # Build response
            return _build_agent_response(
                agent_result=agent_result,
                critic_result=critic_result,
                processing_time_ms=int(processing_time),
                request_id=request_id
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Forecast analysis failed: {str(e)}")
    
    return app


def _calculate_avg_response_time(agent_type: str) -> float:
    """Calculate average response time for an agent."""
    stats = app_state["agent_stats"][agent_type]
    if stats["requests"] == 0:
        return 0.0
    return stats["total_time"] / stats["requests"]


def _update_agent_stats(agent_type: str, processing_time_ms: float):
    """Update agent statistics."""
    stats = app_state["agent_stats"][agent_type]
    stats["requests"] += 1
    stats["total_time"] += processing_time_ms


def _build_agent_response(
    agent_result,
    critic_result,
    processing_time_ms: int,
    request_id: str
) -> AgentResponse:
    """Build standardized agent response."""
    
    # Determine compliance status
    if len(critic_result.violations) == 0:
        compliance_status = ComplianceStatus.COMPLIANT
    elif critic_result.revised_output:
        compliance_status = ComplianceStatus.REVISED
    else:
        compliance_status = ComplianceStatus.FLAGGED
    
    # Convert violations to response format
    policy_violations = [
        PolicyViolationInfo(
            violation_type=v.violation_type.value,
            severity=v.severity,
            description=v.description,
            auto_fixable=v.auto_fixable
        )
        for v in critic_result.violations
    ]
    
    # Use revised output if available, otherwise original
    final_response = critic_result.revised_output or agent_result.agent_response
    
    # Mock context usage (would be real in full implementation)
    context_usage = ContextUsage(
        gpc_tokens=250,  # Mock values
        dsc_tokens=150,
        tsc_tokens=300,
        etc_tokens=50,
        total_tokens=750
    )
    
    return AgentResponse(
        agent_response=final_response,
        compliance_status=compliance_status,
        policy_violations=policy_violations,
        recommendations=getattr(agent_result, 'recommendations', []),
        confidence_score=getattr(agent_result, 'confidence_score', 0.85),
        context_usage=context_usage,
        processing_time_ms=processing_time_ms,
        request_id=request_id
    )