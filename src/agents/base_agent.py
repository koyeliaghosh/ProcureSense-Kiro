"""
Base agent class providing common functionality for all ProcureSense agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time
import logging
from datetime import datetime

from src.agents.agent_types import (
    AgentRequest, AgentResponse, AgentCapabilities, 
    ValidationResult, AgentMetrics
)
from src.models.base_types import AgentType, ComplianceStatus, PolicyViolation
from src.context.context_manager import ContextManager
from src.context.gpc_manager import GPCManager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all ProcureSense agents
    
    Provides common functionality including:
    - Context management and injection
    - Response validation and compliance checking
    - Metrics tracking and performance monitoring
    - Error handling and logging
    """
    
    def __init__(self, context_manager: ContextManager, agent_type: AgentType):
        """
        Initialize base agent with context management
        
        Args:
            context_manager: Context management system
            agent_type: Type of agent (negotiation, compliance, forecast)
        """
        self.context_manager = context_manager
        self.agent_type = agent_type
        self.gpc_manager = context_manager.gpc_manager
        self.capabilities = self._define_capabilities()
        self.metrics = AgentMetrics()
        
        logger.info(f"Initialized {agent_type.value} agent with capabilities: {self.capabilities.supported_operations}")
    
    @abstractmethod
    def _define_capabilities(self) -> AgentCapabilities:
        """
        Define agent-specific capabilities and constraints
        
        Returns:
            AgentCapabilities: Agent capability definition
        """
        pass
    
    @abstractmethod
    def _process_agent_request(self, request: AgentRequest, context) -> str:
        """
        Process agent-specific request logic
        
        Args:
            request: Standardized agent request
            context: Layered context for the request
            
        Returns:
            str: Raw agent response before validation
        """
        pass
    
    @abstractmethod
    def _validate_request_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate agent-specific request payload
        
        Args:
            payload: Request payload to validate
            
        Returns:
            bool: True if payload is valid
        """
        pass
    
    def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Main request processing pipeline with full validation and metrics
        
        Args:
            request: Standardized agent request
            
        Returns:
            AgentResponse: Validated and compliant response
        """
        start_time = time.time()
        self.metrics.total_requests += 1
        
        try:
            # Validate request
            if not self._validate_request(request):
                raise ValueError(f"Invalid request for {self.agent_type.value} agent")
            
            # Build context
            context = self._build_context(request)
            
            # Process agent-specific logic
            raw_response = self._process_agent_request(request, context)
            
            # Validate output for policy compliance
            validation_result = self._validate_output(raw_response, request)
            
            # Build final response
            response = self._build_response(
                raw_response, 
                validation_result, 
                context,
                time.time() - start_time
            )
            
            # Update metrics
            self._update_metrics(response, time.time() - start_time)
            
            logger.info(f"Successfully processed {self.agent_type.value} request in {time.time() - start_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing {self.agent_type.value} request: {str(e)}")
            return self._build_error_response(str(e), time.time() - start_time)
    
    def _validate_request(self, request: AgentRequest) -> bool:
        """
        Validate incoming request format and content
        
        Args:
            request: Request to validate
            
        Returns:
            bool: True if request is valid
        """
        # Check agent type matches
        if request.agent_type != self.agent_type:
            logger.error(f"Agent type mismatch: expected {self.agent_type.value}, got {request.agent_type.value}")
            return False
        
        # Validate payload structure
        if not self._validate_request_payload(request.payload):
            logger.error(f"Invalid payload for {self.agent_type.value} agent")
            return False
        
        # Check session ID is present
        if not request.session_id or not request.session_id.strip():
            logger.error("Missing or empty session_id")
            return False
        
        return True
    
    def _build_context(self, request: AgentRequest):
        """
        Build layered context for the request
        
        Args:
            request: Agent request
            
        Returns:
            LayeredContext: Built context with all layers
        """
        # Extract session data from request if available
        session_data = {}
        if request.user_context:
            session_data['user_context'] = request.user_context
        
        # Build context using context manager
        context = self.context_manager.build_context(
            agent_type=self.agent_type.value,
            request=request.payload,
            session_data=session_data
        )
        
        logger.debug(f"Built context with {context.total_tokens} total tokens")
        return context
    
    def _validate_output(self, output: str, request: AgentRequest) -> ValidationResult:
        """
        Validate agent output for policy compliance
        
        Args:
            output: Raw agent output
            request: Original request for context
            
        Returns:
            ValidationResult: Validation results with violations and fixes
        """
        # Extract category and amount from request if available
        category = request.payload.get('category')
        amount = request.payload.get('planned_spend') or request.payload.get('amount')
        
        # Use GPC manager for comprehensive validation
        gpc_result = self.gpc_manager.validate_comprehensive(output, category, amount)
        
        # Convert to ValidationResult format
        violations = gpc_result.violations  # Already PolicyViolation objects
        
        # Generate auto-fixes based on violations
        auto_fixes = []
        for violation in violations:
            if violation.auto_fixable:
                auto_fixes.append(f"Auto-fix available for: {violation.description}")
        
        return ValidationResult(
            is_compliant=gpc_result.is_valid,
            violations=violations,
            auto_fixes=auto_fixes,
            manual_review_required=any(not v.auto_fixable for v in violations),
            confidence_score=gpc_result.compliance_score
        )
    
    def _build_response(self, raw_response: str, validation_result: ValidationResult, 
                       context, processing_time: float) -> AgentResponse:
        """
        Build standardized agent response
        
        Args:
            raw_response: Raw agent output
            validation_result: Validation results
            context: Context used for processing
            processing_time: Time taken to process request
            
        Returns:
            AgentResponse: Standardized response
        """
        # Determine compliance status
        if validation_result.is_compliant:
            compliance_status = ComplianceStatus.COMPLIANT
        elif validation_result.auto_fixes:
            compliance_status = ComplianceStatus.REVISED
        else:
            compliance_status = ComplianceStatus.FLAGGED
        
        # Extract policy violations as strings
        policy_violations = [v.description for v in validation_result.violations]
        
        # Build recommendations based on violations and fixes
        recommendations = []
        if validation_result.auto_fixes:
            recommendations.extend(validation_result.auto_fixes)
        if validation_result.manual_review_required:
            recommendations.append("Manual review required for complex policy violations")
        
        # Get context usage
        context_usage = context.get_layer_tokens()
        
        return AgentResponse(
            agent_response=raw_response,
            compliance_status=compliance_status,
            policy_violations=policy_violations,
            recommendations=recommendations,
            confidence_score=validation_result.confidence_score,
            context_usage=context_usage
        )
    
    def _build_error_response(self, error_message: str, processing_time: float) -> AgentResponse:
        """
        Build error response for failed requests
        
        Args:
            error_message: Error description
            processing_time: Time taken before error
            
        Returns:
            AgentResponse: Error response
        """
        return AgentResponse(
            agent_response=f"Error processing {self.agent_type.value} request: {error_message}",
            compliance_status=ComplianceStatus.FLAGGED,
            policy_violations=[f"Processing error: {error_message}"],
            recommendations=["Please check request format and try again"],
            confidence_score=0.0,
            context_usage={}
        )
    
    def _update_metrics(self, response: AgentResponse, processing_time: float):
        """
        Update agent performance metrics
        
        Args:
            response: Agent response
            processing_time: Time taken to process
        """
        # Update success metrics
        if response.compliance_status != ComplianceStatus.FLAGGED:
            self.metrics.successful_responses += 1
        
        # Update violation metrics
        if response.policy_violations:
            self.metrics.policy_violations += 1
        
        # Update revision metrics
        if response.compliance_status == ComplianceStatus.REVISED:
            self.metrics.auto_revisions += 1
        
        # Update timing metrics
        total_time = (self.metrics.average_response_time * (self.metrics.total_requests - 1) + processing_time)
        self.metrics.average_response_time = total_time / self.metrics.total_requests
        
        # Update confidence metrics
        total_confidence = (self.metrics.average_confidence_score * (self.metrics.total_requests - 1) + response.confidence_score)
        self.metrics.average_confidence_score = total_confidence / self.metrics.total_requests
        
        # Update context usage metrics
        for layer, tokens in response.context_usage.items():
            if layer not in self.metrics.context_token_usage:
                self.metrics.context_token_usage[layer] = 0
            self.metrics.context_token_usage[layer] += tokens
    
    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities"""
        return self.capabilities
    
    def get_metrics(self) -> AgentMetrics:
        """Get agent performance metrics"""
        return self.metrics
    
    def reset_metrics(self):
        """Reset agent metrics (useful for testing)"""
        self.metrics = AgentMetrics()
        logger.info(f"Reset metrics for {self.agent_type.value} agent")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive agent status
        
        Returns:
            Dict containing agent status information
        """
        return {
            "agent_type": self.agent_type.value,
            "capabilities": {
                "supported_operations": self.capabilities.supported_operations,
                "required_context_layers": self.capabilities.required_context_layers,
                "max_response_tokens": self.capabilities.max_response_tokens,
                "requires_gpc_validation": self.capabilities.requires_gpc_validation,
                "supports_auto_revision": self.capabilities.supports_auto_revision
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "violation_rate": self.metrics.violation_rate,
                "average_response_time": self.metrics.average_response_time,
                "average_confidence_score": self.metrics.average_confidence_score
            },
            "context_manager_status": self.context_manager.get_policy_summary()
        }