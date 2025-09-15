# Design Document

## Overview

ProcureSense is a multi-agent procurement co-pilot that demonstrates advanced context engineering with enterprise alignment guarantees. The system uses Ollama with gpt-oss-20b to provide intelligent procurement assistance through specialized agents while maintaining strict policy compliance through a hierarchical, budgeted context architecture.

The core innovation is a layered context system with mathematical token budgeting that ensures Global Policy Context (GPC) is never pruned, even under extreme token pressure. A Global Policy Critic (GPCritic) performs post-hoc validation of all agent outputs using only GPC and Domain Strategy Context (DSC) to auto-revise policy violations.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    ProcureSense System                      │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Server (localhost:8000)                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Negotiation    │  │   Compliance    │  │  Forecast    │ │
│  │     Agent       │  │     Agent       │  │    Agent     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │ Global Policy     │                    │
│                    │ Critic (GPCritic) │                    │
│                    └───────────────────┘                    │
├─────────────────────────────────────────────────────────────┤
│              Context Management Layer                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐   │
│  │   GPC   │ │   DSC   │ │   TSC   │ │      ETC        │   │
│  │  (25%)  │ │  (25%)  │ │  (40%)  │ │     (10%)       │   │
│  │ Pinned  │ │Category │ │Session  │ │  Tool Payloads  │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 Ollama Integration Layer                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              gpt-oss-20b Model                      │   │
│  │  • HTTP: /v1/chat/completions (OpenAI compatible)  │   │
│  │  • Native: /api/chat (Ollama native)               │   │
│  │  • Local deployment for enterprise security        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Context Architecture

The system implements a mathematically budgeted context hierarchy:

**Budget Allocation:**
- b = (b_GPC, b_DSC, b_TSC, b_ETC) = (0.25, 0.25, 0.40, 0.10)
- Constraint: Σb_i = 1
- Total budget B enforced at build time

**Pruning Order Under Token Pressure:**
ETC → TSC → DSC → GPC (GPC survives all pruning)

**Alignment Objective:**
```
minimize: α·V(draft, GPC) + β·T(prompt)
subject to: tokens_i ≤ b_i · B
```
Where V counts policy violations, T proxies token cost, B is context budget.## 
Components and Interfaces

### 1. Agent Framework

#### Base Agent Interface
```python
class BaseAgent:
    def __init__(self, context_manager: ContextManager)
    def process_request(self, request: Dict) -> AgentResponse
    def validate_output(self, output: str) -> ValidationResult
```

#### Specialized Agents

**Negotiation Agent**
- Input: `{vendor: str, target_discount_pct: float, category: str}`
- Output: Pricing proposals, contract terms, warranty requirements
- Policy Integration: Auto-adds required warranties for aggressive discounts

**Compliance Agent**
- Input: `{clause: str, contract_context?: str}`
- Output: Risk assessment, compliant rewrites, flagged violations
- Policy Integration: Removes/rewrites prohibited clauses automatically

**Forecast Agent**
- Input: `{category: str, quarter: str, planned_spend: float}`
- Output: Budget alignment analysis, variance reports, trade-off recommendations
- Policy Integration: Enforces budget variance gates, requires trade-off explanations

### 2. Context Management System

#### Context Builder
```python
class ContextManager:
    def __init__(self, config: ContextConfig)
    def build_context(self, agent_type: str, request: Dict) -> LayeredContext
    def prune_context(self, context: LayeredContext, target_tokens: int) -> LayeredContext
    def validate_budgets(self, context: LayeredContext) -> bool
```

#### Context Layers

**Global Policy Context (GPC) - 25% Budget**
- Enterprise OKRs and strategic objectives
- Prohibited/required contract clauses
- Budget thresholds and variance rules
- Compliance guardrails and legal requirements
- **Pinned**: Never pruned under token pressure

**Domain Strategy Context (DSC) - 25% Budget**
- Category-specific procurement playbooks
- Vendor relationship guidelines
- Market intelligence summaries
- Historical negotiation patterns
- **Summarized**: Compressed to fit budget constraints

**Task/Session Context (TSC) - 40% Budget**
- Recent conversation turns with recency bias
- Tool interaction snippets and results
- Session findings and decisions
- User preferences and context
- **Rolling Summaries**: Periodic compression to prevent overfitting

**Ephemeral Tool Context (ETC) - 10% Budget**
- One-shot payloads (quotes, budgets, vendor data)
- Temporary calculation results
- External API responses
- Real-time market data
- **First Pruned**: Discarded under token pressure###
 3. Global Policy Critic (GPCritic)

#### Architecture
```python
class GlobalPolicyCritic:
    def __init__(self, gpc_context: str, dsc_context: str)
    def validate_output(self, agent_output: str, original_request: Dict) -> CriticResult
    def auto_revise(self, violations: List[PolicyViolation]) -> str
    def generate_compliance_report(self) -> ComplianceReport
```

#### Validation Process
1. **Input**: Agent draft + original request
2. **Context**: Only GPC + DSC (no TSC/ETC contamination)
3. **Analysis**: Policy violation detection using enterprise rules
4. **Auto-Revision**: Automatic fixes for common violations
5. **Output**: Compliant response + compliance report

### 4. API Layer

#### FastAPI Endpoints

**POST /agent/negotiation**
```json
{
  "vendor": "string",
  "target_discount_pct": "float",
  "category": "string",
  "context": "optional string"
}
```

**POST /agent/compliance**
```json
{
  "clause": "string",
  "contract_type": "optional string",
  "risk_tolerance": "optional string"
}
```

**POST /agent/forecast**
```json
{
  "category": "string",
  "quarter": "string",
  "planned_spend": "float",
  "current_budget": "optional float"
}
```

#### Response Format
```json
{
  "agent_response": "string",
  "compliance_status": "compliant|revised|flagged",
  "policy_violations": ["array of violations"],
  "recommendations": ["array of recommendations"],
  "confidence_score": "float",
  "context_usage": {
    "gpc_tokens": "int",
    "dsc_tokens": "int", 
    "tsc_tokens": "int",
    "etc_tokens": "int"
  }
}
```## Data
 Models

### Core Models

#### PolicyContext
```python
@dataclass
class PolicyContext:
    okrs: List[str]
    prohibited_clauses: List[str]
    required_clauses: List[str]
    budget_thresholds: Dict[str, float]
    compliance_rules: List[ComplianceRule]
    token_budget: int
```

#### AgentRequest
```python
@dataclass
class AgentRequest:
    agent_type: AgentType
    payload: Dict[str, Any]
    session_id: str
    user_context: Optional[str]
    priority: RequestPriority
```

#### LayeredContext
```python
@dataclass
class LayeredContext:
    gpc: GlobalPolicyContext
    dsc: DomainStrategyContext  
    tsc: TaskSessionContext
    etc: EphemeralToolContext
    total_tokens: int
    budget_compliance: bool
```

#### ValidationResult
```python
@dataclass
class ValidationResult:
    is_compliant: bool
    violations: List[PolicyViolation]
    auto_fixes: List[str]
    manual_review_required: bool
    confidence_score: float
```

## Error Handling

### Context Budget Violations
- **Detection**: Real-time token counting during context building
- **Response**: Automatic pruning following ETC→TSC→DSC→GPC order
- **Logging**: Budget violation events with context layer details
- **Fallback**: Minimal GPC-only context if extreme pressure

### Ollama/gpt-oss-20b Integration Failures
- **Ollama Connection**: Retry with exponential backoff, fallback between /v1/chat/completions and /api/chat endpoints
- **gpt-oss-20b Model Loading**: Automatic model pull and loading if not available locally
- **Model Overload**: Queue management with priority handling for concurrent requests
- **Response Timeout**: Graceful degradation with cached responses, configurable timeout per agent type
- **Invalid Responses**: GPCritic validation with auto-correction, model-specific prompt adjustments

### Policy Violation Handling
- **Detection**: GPCritic validation against GPC rules
- **Auto-Revision**: Automatic fixes for common violations
- **Manual Review**: Flagging for complex policy conflicts
- **Audit Trail**: Complete logging of violations and corrections

### Data Privacy Protection
- **PII Detection**: Automatic identification in session data
- **Summarization**: Store findings, not raw PII in TSC
- **Encryption**: Sensitive data encrypted at rest
- **Retention**: Automatic cleanup of ephemeral contexts#
# Testing Strategy

### Unit Testing
- **Context Management**: Budget allocation and pruning logic
- **Agent Logic**: Individual agent response generation
- **Policy Validation**: GPCritic violation detection
- **API Endpoints**: Request/response handling

### Integration Testing
- **Agent-to-GPCritic Flow**: End-to-end policy enforcement with gpt-oss-20b
- **Context Layer Interaction**: Cross-layer data flow within token budgets
- **Ollama Integration**: Model communication reliability, endpoint fallback testing
- **gpt-oss-20b Performance**: Response quality validation, token usage optimization
- **Configuration Loading**: Environment variable handling for Ollama host/model settings

### Acceptance Testing (Automated)

**AT-1: Warranty Addition**
- Input: Aggressive discount negotiation request
- Expected: Required warranties automatically added
- Validation: GPCritic confirms warranty presence

**AT-2: Budget Variance Handling**
- Input: Forecast with >threshold variance
- Expected: Trade-offs or adjustments included
- Validation: Response contains variance explanation

**AT-3: Prohibited Clause Removal**
- Input: Contract with prohibited terms
- Expected: Clauses removed/rewritten by Compliance + GPCritic
- Validation: Final output contains no prohibited terms

**AT-4: Hierarchical Prompt Efficiency**
- Input: Complex procurement scenario
- Expected: Hierarchical prompt shorter than flat alternative
- Validation: Token count comparison with equivalent flat prompt

### Performance Testing
- **Token Budget Compliance**: Verify budget constraints under load
- **Response Time**: Agent response times under various loads
- **Context Pruning**: Pruning algorithm performance
- **Memory Usage**: Context storage and cleanup efficiency

### Security Testing
- **Policy Bypass Attempts**: Malicious input designed to circumvent policies
- **Data Leakage**: PII protection in context summaries
- **Configuration Security**: Environment variable protection
- **API Security**: Input validation and sanitization
## Ollama I
ntegration Details

### Model Configuration Options

**Option 1: Local Ollama (Recommended for Enterprise)**
- **Model**: gpt-oss-20b (20B parameters, ~40GB disk space)
- **Deployment**: Local Ollama instance for full data control
- **Requirements**: 16GB+ RAM, 40GB+ storage

**Option 2: Local Ollama with Smaller Model (Space-Constrained)**
- **Model**: llama3.1:8b (~4.7GB) or mistral:7b (~4.1GB)
- **Deployment**: Local Ollama instance with reduced storage needs
- **Requirements**: 8GB+ RAM, 5GB+ storage

**Option 3: Remote Ollama API**
- **Model**: Any model on remote Ollama server
- **Deployment**: Connect to external Ollama instance
- **Requirements**: Network access to Ollama server

**Option 4: OpenAI-Compatible API**
- **Model**: Any OpenAI-compatible endpoint (OpenAI, Anthropic, etc.)
- **Deployment**: External API with enterprise API keys
- **Requirements**: API credentials and network access

**Endpoints**: 
- Primary: `/v1/chat/completions` (OpenAI-compatible)
- Fallback: `/api/chat` (Ollama native format)
- **Configuration**: Model parameters, host, and timeout settings via `.env`

### Context Engineering for gpt-oss-20b
- **Token Optimization**: Hierarchical context designed for 20B parameter efficiency
- **Prompt Engineering**: Model-specific prompt templates optimized for gpt-oss-20b
- **Response Parsing**: Custom parsing logic for gpt-oss-20b output format
- **Temperature Control**: Agent-specific temperature settings for optimal performance

### Performance Considerations
- **Local Processing**: No external API calls, full enterprise data control
- **Memory Management**: Efficient context loading for 20B parameter model
- **Concurrent Requests**: Queue management for multiple agent requests
- **Model Warm-up**: Keep model loaded for consistent response times

### Environment Configuration

**For Local Ollama (Space-Constrained):**
```bash
# Ollama Configuration - Smaller Model
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=llama3.1:8b              # Only ~4.7GB vs 40GB
OLLAMA_TIMEOUT=30
OLLAMA_MAX_TOKENS=4096

# Context Budgets (tokens) - Adjusted for smaller model
CONTEXT_BUDGET_TOTAL=2000              # Reduced for 8B model
CONTEXT_BUDGET_GPC=500                 # 25%
CONTEXT_BUDGET_DSC=500                 # 25%
CONTEXT_BUDGET_TSC=800                 # 40%
CONTEXT_BUDGET_ETC=200                 # 10%
```

**For Remote Ollama API:**
```bash
# Remote Ollama Configuration
OLLAMA_HOST=your-ollama-server:11434   # Remote server
OLLAMA_MODEL=gpt-oss-20b               # Model on remote server
OLLAMA_TIMEOUT=60                      # Higher timeout for network
OLLAMA_MAX_TOKENS=4096
```

**For OpenAI-Compatible API:**
```bash
# OpenAI-Compatible Configuration
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4                     # Or gpt-3.5-turbo
OLLAMA_TIMEOUT=30
OLLAMA_MAX_TOKENS=4096
```