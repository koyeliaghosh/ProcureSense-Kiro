# Implementation Plan

- [ ] 1. Set up project structure and core configuration








  - Create FastAPI project structure with proper directory organization (src/, tests/, config/)
  - Create requirements.txt with FastAPI, Pydantic, python-dotenv, httpx dependencies
  - Implement environment configuration loading for Ollama settings and context budgets
  - **⚙️ CONFIGURE**: Create .env template with OLLAMA_HOST, OLLAMA_MODEL, context budgets
  - Create base data models and type definitions for the system
  - _Requirements: 6.1, 7.1, 7.2_

- [ ] 2. Implement flexible LLM integration layer




  - Create LLM client with support for multiple deployment options (local Ollama, remote Ollama, OpenAI-compatible APIs)
  - **⚙️ CONFIGURE**: Choose deployment option and set appropriate environment variables
  - Implement connection management with retry logic and endpoint fallback
  - **⚙️ CONFIGURE**: For local Ollama: verify model is available (see deployment options below)
  - Add model loading verification and error handling for chosen deployment
  - Write unit tests for LLM communication and error scenarios across deployment types
  - _Requirements: 6.1, 6.2, 6.3, 7.3_
- [x] 3. Build context management system foundation



- [ ] 3. Build context management system foundation

  - Implement token counting utilities for accurate budget tracking
  - Create LayeredContext data structure with GPC, DSC, TSC, ETC layers
  - Build context budget validation and enforcement logic
  - Write unit tests for context layer management and token counting
  - _Requirements: 5.1, 5.2, 5.3_
- [ ] 4. Implement context pruning algorithm



- [ ] 4. Implement context pruning algorithm

  - Create context pruning logic following ETC→TSC→DSC→GPC hierarchy
  - Implement GPC pinning to ensure it's never pruned under token pressure
  - Add context summarization for TSC rolling summaries and DSC compression
  - Write unit tests for pruning scenarios and budget compliance
  - _Requirements: 5.1, 5.4_
-

- [-] 5. Create Global Policy Context (GPC) management







  - Implement PolicyContext data model with OKRs, prohibited/required clauses, and compliance rules
  - **⚙️ CONFIGURE**: Define enterprise policies in .env (PROHIBITED_CLAUSES, REQUIRED_CLAUSES, BUDGET_THRESHOLDS)
  - Create GPC loader that reads enterprise policies from configuration
  - Build policy validation utilities for detecting violations
  - Write unit tests for policy loading and validation logic
  - _Requirements: 4.2, 4.3, 7.2_

- [x] 6. Build base agent framework




  - Create BaseAgent abstract class with common functionality
  - Implement AgentRequest and AgentResponse data models
  - Add context injection and response validation interfaces
  - Write unit tests for base agent functionality
  - _Requirements: 1.1, 2.1, 3.1_

- [x] 7. Implement Negotiation Agent




  - Create NegotiationAgent class with vendor/discount/category request handling
  - Implement pricing proposal generation using gpt-oss-20b via Ollama
  - Add automatic warranty addition logic for aggressive discounts
  - Write unit tests for negotiation logic and warranty requirements
  - _Requirements: 1.1, 1.2, 1.3_




- [ ] 8. Implement Compliance Agent

  - Create ComplianceAgent class with clause analysis capabilities
  - Implement risk assessment and prohibited clause detection




  - Add automatic clause rewriting for compliance violations
  - Write unit tests for compliance checking and clause rewriting
  - _Requirements: 2.1, 2.2, 2.3_




- [ ] 9. Implement Forecast Agent

  - Create ForecastAgent class with budget alignment analysis
  - Implement variance detection and trade-off recommendation logic
  - Add budget threshold enforcement and OKR alignment checking



  - Write unit tests for forecasting and budget variance handling
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 10. Build Global Policy Critic (GPCritic)




  - Create GlobalPolicyCritic class with GPC+DSC only context validation
  - Implement policy violation detection using enterprise rules
  - Add automatic revision logic for common policy violations
  - Write unit tests for policy criticism and auto-revision functionality
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 11. Create FastAPI endpoints and routing

  - Implement POST /agent/negotiation endpoint with request validation
  - Implement POST /agent/compliance endpoint with clause processing
  - Implement POST /agent/forecast endpoint with budget analysis
  - Add request/response models and error handling for all endpoints
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 12. Integrate agent-to-GPCritic workflow

  - Connect all agents to route outputs through GPCritic validation
  - Implement compliance status reporting and violation tracking
  - Add context usage reporting for token budget monitoring
  - Write integration tests for end-to-end agent-to-critic flow
  - _Requirements: 4.1, 4.4_

- [ ] 13. Implement acceptance test scenarios

  - Create AT-1 test: Verify warranty addition for aggressive discount negotiations
  - Create AT-2 test: Verify trade-off explanations for budget variance scenarios
  - Create AT-3 test: Verify prohibited clause removal by Compliance + GPCritic
  - Create AT-4 test: Verify hierarchical prompt efficiency vs flat alternatives
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 14. Add comprehensive error handling and logging

  - Implement error handling for Ollama connection failures and model issues
  - Add context budget violation handling with graceful degradation
  - Create audit trail logging for policy violations and corrections
  - Add PII detection and protection in session data handling
  - _Requirements: 5.4, 7.4_

- [ ] 15. Create configuration and deployment setup

  - **⚙️ CONFIGURE**: Create comprehensive .env template with all required configuration options
  - **⚙️ CONFIGURE**: Document Ollama installation and gpt-oss-20b model setup instructions
  - Add startup validation for Ollama connectivity and model availability
  - **⚙️ CONFIGURE**: Set up FastAPI server host/port configuration (default: localhost:8000)
  - Implement health check endpoints for system monitoring
  - Create deployment documentation and configuration examples
  - _Requirements: 7.1, 7.3, 7.4_
#
# Configuration Checklist

Before starting implementation, ensure you have configured:

### Deployment Options (Choose One)

**Option 1: Local Ollama with Smaller Model (RECOMMENDED for space constraints)**
- [ ] **Install Ollama**: Download and install Ollama on your system

- [ ] **Pull smaller model**: Run `ollama pull llama3.1:8b` (~4.7GB) or `ollama pull mistral:7b` (~4.1GB)
- [ ] **Verify Ollama**: Confirm Ollama is running on localhost:11434
- [ ] **Test Model**: Test model responds via `ollama run llama3.1:8b`

**Option 2: Local Ollama with gpt-oss-20b (if you have 40GB+ storage)**
- [ ] **Install Ollama**: Download and install Ollama on your system
- [ ] **Pull gpt-oss-20b**: Run `ollama pull gpt-oss-20b` (~40GB)
- [ ] **Verify Ollama**: Confirm Ollama is running on localhost:11434
- [ ] **Test Model**: Test gpt-oss-20b responds via `ollama run gpt-oss-20b`

**Option 3: Remote Ollama Server**
- [ ] **Access Remote Server**: Ensure you have access to a remote Ollama instance
- [ ] **Network Connectivity**: Verify network access to the remote server

**Option 4: OpenAI-Compatible API**
- [ ] **API Credentials**: Obtain API key for OpenAI, Anthropic, or other service
- [ ] **Network Access**: Ensure internet connectivity for API calls

### Environment Variables (.env file)

**For Local Ollama with Smaller Model (Space-Constrained):**
```bash
# LLM Configuration - UPDATE THESE
LLM_PROVIDER=ollama                 # ollama, openai, anthropic
OLLAMA_HOST=localhost:11434         # Your Ollama host
OLLAMA_MODEL=llama3.1:8b           # Smaller model (~4.7GB)
OLLAMA_TIMEOUT=30                  # Adjust based on your hardware
OLLAMA_MAX_TOKENS=4096            # Adjust based on your needs

# Context Budgets (tokens) - ADJUSTED FOR SMALLER MODEL
CONTEXT_BUDGET_TOTAL=2000         # Reduced for 8B model
CONTEXT_BUDGET_GPC=500            # 25% for Global Policy Context
CONTEXT_BUDGET_DSC=500            # 25% for Domain Strategy Context  
CONTEXT_BUDGET_TSC=800            # 40% for Task/Session Context
CONTEXT_BUDGET_ETC=200            # 10% for Ephemeral Tool Context
```

**For Remote Ollama Server:**
```bash
# Remote Ollama Configuration
LLM_PROVIDER=ollama
OLLAMA_HOST=your-server:11434      # Remote Ollama server
OLLAMA_MODEL=gpt-oss-20b          # Model on remote server
OLLAMA_TIMEOUT=60                 # Higher timeout for network
OLLAMA_MAX_TOKENS=4096
```

**For OpenAI-Compatible API:**
```bash
# OpenAI-Compatible Configuration
LLM_PROVIDER=openai               # or anthropic, etc.
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4                # Or gpt-3.5-turbo
OLLAMA_TIMEOUT=30
OLLAMA_MAX_TOKENS=4096
```

**Common Configuration (All Options):**
```bash
# FastAPI Server - UPDATE THESE  
SERVER_HOST=localhost             # Your server host
SERVER_PORT=8000                 # Your preferred port

# Enterprise Policies - CUSTOMIZE THESE
PROHIBITED_CLAUSES=liability_waiver,indemnification,unlimited_liability
REQUIRED_CLAUSES=warranty,data_protection,termination_rights
BUDGET_THRESHOLDS=software:50000,hardware:100000,services:25000

# Compliance Rules - CUSTOMIZE THESE
VARIANCE_THRESHOLD=0.15          # 15% budget variance threshold
AUTO_REVISION_ENABLED=true       # Enable GPCritic auto-revision
AUDIT_LOGGING_ENABLED=true       # Enable compliance audit logging
```

### Hardware Requirements by Option

**Option 1: Local Ollama with Smaller Model**
- [ ] **Memory**: 8GB+ system RAM (vs 16GB+ for gpt-oss-20b)
- [ ] **Storage**: 5GB+ disk space (vs 40GB+ for gpt-oss-20b)
- [ ] **CPU/GPU**: Standard CPU sufficient, GPU optional

**Option 2: Local Ollama with gpt-oss-20b**
- [ ] **Memory**: 16GB+ system RAM
- [ ] **Storage**: 40GB+ disk space
- [ ] **CPU/GPU**: GPU recommended for faster inference

**Option 3: Remote Ollama Server**
- [ ] **Memory**: Minimal local requirements
- [ ] **Storage**: Minimal local requirements
- [ ] **Network**: Stable internet connection

**Option 4: OpenAI-Compatible API**
- [ ] **Memory**: Minimal local requirements
- [ ] **Storage**: Minimal local requirements
- [ ] **Network**: Stable internet connection
- [ ] **Cost**: API usage costs apply