# ProcureSense - Kiro Project Structure

This document outlines the complete Kiro project structure for ProcureSense AI, demonstrating the use of specs, hooks, steering, and settings.

## 📁 Complete Project Structure

```
ProcureSense-Kiro/
├── 🤖 .kiro/                          # Kiro IDE configuration and workflows
│   ├── specs/                         # Feature specifications and planning
│   │   └── procure-sense/
│   │       ├── requirements.md        # User stories and acceptance criteria
│   │       ├── design.md             # System architecture and design
│   │       └── tasks.md              # Implementation task breakdown
│   ├── hooks/                        # Agent hooks for automation
│   │   ├── contract-analysis.yml     # Auto-analyze contracts on save
│   │   ├── budget-forecast.yml       # Budget variance monitoring
│   │   ├── vendor-negotiation.yml    # Vendor proposal analysis
│   │   ├── policy-compliance.yml     # Policy update automation
│   │   └── full-procurement-analysis.yml # Complete workflow
│   ├── steering/                     # Context and guidance documents
│   │   ├── procurement-standards.md  # Core procurement guidelines
│   │   ├── compliance-rules.md       # Detailed compliance framework
│   │   ├── market-intelligence.md    # Market data and benchmarks
│   │   └── agent-coordination.md     # Multi-agent workflow guidance
│   ├── settings/                     # Kiro IDE settings
│   │   └── mcp.json                  # Model Context Protocol configuration
│   └── PROJECT_STRUCTURE.md          # This documentation file
├── 🏗️ src/                           # Source code
│   ├── agents/                       # AI agent implementations
│   ├── api/                          # FastAPI application
│   ├── context/                      # Advanced context management
│   ├── critic/                       # Global Policy Critic
│   ├── llm/                          # LLM client implementations
│   ├── models/                       # Data models and types
│   ├── static/                       # Web interface files
│   └── workflow/                     # Integration management
├── 🧪 tests/                         # Comprehensive test suite
├── 🚀 deployment/                    # Docker and production configs
├── 📜 scripts/                       # Utility scripts
└── 📚 docs/                          # Additional documentation
```

## 🎯 Kiro Integration Features

### 1. Specs (Specification-Driven Development)
- **Location**: `.kiro/specs/procure-sense/`
- **Purpose**: Structured feature development with requirements, design, and tasks
- **Files**:
  - `requirements.md`: EARS-format user stories and acceptance criteria
  - `design.md`: System architecture and component design
  - `tasks.md`: Detailed implementation task breakdown

### 2. Agent Hooks (Workflow Automation)
- **Location**: `.kiro/hooks/`
- **Purpose**: Automated AI agent execution on file events or manual triggers
- **Examples**:
  - Contract analysis when contracts are saved
  - Budget forecasting when budget files are updated
  - Policy compliance checks when policies change
  - Multi-agent procurement workflows

### 3. Steering (Context and Guidance)
- **Location**: `.kiro/steering/`
- **Purpose**: Provide context and guidance to AI agents
- **Inclusion Types**:
  - `always`: Always included in agent context
  - `fileMatch`: Included when specific files are accessed
  - `manual`: Included when explicitly referenced
- **Content**:
  - Procurement standards and best practices
  - Compliance rules and validation criteria
  - Market intelligence and pricing benchmarks
  - Agent coordination guidelines

### 4. Settings (IDE Configuration)
- **Location**: `.kiro/settings/`
- **Purpose**: Configure Kiro IDE features and integrations
- **Files**:
  - `mcp.json`: Model Context Protocol server configurations

## 🔗 Agent Hook Examples

### Contract Analysis Hook
```yaml
name: "Auto Contract Analysis"
trigger: "file_save"
pattern: "contracts/*.pdf"
agent: "compliance"
```

### Budget Monitoring Hook
```yaml
name: "Budget Variance Check"
trigger: "file_update"
pattern: "budgets/*.xlsx"
agent: "forecast"
```

### Multi-Agent Workflow Hook
```yaml
name: "Complete Procurement Analysis"
trigger: "manual"
agents: ["negotiation", "compliance", "forecast", "gp_critic"]
```

## 📋 Steering Context Examples

### Always Included (procurement-standards.md)
```markdown
---
inclusion: always
description: "Core procurement standards for all AI agents"
---
# Procurement Standards and Guidelines
- Cost optimization principles
- Quality assurance requirements
- Risk management protocols
```

### File-Specific (compliance-rules.md)
```markdown
---
inclusion: fileMatch
fileMatchPattern: "src/agents/compliance*"
description: "Detailed compliance rules and validation criteria"
---
# Compliance Rules and Validation Criteria
- Legal and regulatory compliance
- Contract compliance framework
- Automated compliance checks
```

### Manual Reference (market-intelligence.md)
```markdown
---
inclusion: manual
contextKey: "market-data"
description: "Market intelligence and pricing benchmarks"
---
# Market Intelligence and Pricing Benchmarks
- Software licensing market data
- Hardware procurement trends
- Services market analysis
```

## 🛠️ MCP Integration

The Model Context Protocol (MCP) configuration enables integration with external data sources:

```json
{
  "mcpServers": {
    "procurement-data": {
      "command": "uvx",
      "args": ["procurement-data-mcp-server@latest"],
      "autoApprove": ["get_vendor_data", "get_contract_history"]
    },
    "market-intelligence": {
      "command": "uvx",
      "args": ["market-intel-mcp-server@latest"],
      "autoApprove": ["get_market_prices", "get_vendor_ratings"]
    }
  }
}
```

## 🎯 Benefits of This Structure

### For Development
- **Structured Planning**: Specs provide clear requirements and design
- **Automated Workflows**: Hooks reduce manual tasks and ensure consistency
- **Context-Aware AI**: Steering provides relevant guidance to agents
- **External Integration**: MCP enables rich data access

### For Judges/Evaluators
- **Clear Documentation**: Complete project structure is self-documenting
- **Kiro Integration**: Demonstrates advanced IDE feature usage
- **Professional Approach**: Shows enterprise-ready development practices
- **Automation Examples**: Real-world workflow automation scenarios

## 🚀 Usage Instructions

### For Developers
1. **Review Specs**: Start with `.kiro/specs/procure-sense/requirements.md`
2. **Configure Hooks**: Enable relevant hooks in `.kiro/hooks/`
3. **Reference Steering**: Use steering documents for context and guidance
4. **Configure MCP**: Set up external data sources in `.kiro/settings/mcp.json`

### For Judges
1. **Explore Structure**: Review this document and the `.kiro/` directory
2. **Test Hooks**: Try the agent hooks with sample files
3. **Review Steering**: See how context is provided to AI agents
4. **Evaluate Integration**: Assess the completeness of Kiro feature usage

This structure demonstrates a comprehensive understanding and implementation of Kiro IDE's advanced features for AI-powered development workflows.