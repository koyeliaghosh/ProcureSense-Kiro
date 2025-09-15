# Requirements Document

## Introduction

ProcureSense is an enterprise procurement automation system that demonstrates advanced context engineering with hierarchical prompt management. The system uses Ollama with gpt-oss-20b to provide intelligent procurement assistance through specialized agents while maintaining enterprise alignment over local optimization. The system features a layered, budgeted context architecture that ensures critical business policies and guardrails are preserved even under token pressure.

## Requirements

### Requirement 1

**User Story:** As a procurement manager, I want an intelligent negotiation agent that can propose optimal pricing and terms for vendor contracts, so that I can achieve better deals while maintaining compliance with company policies.

#### Acceptance Criteria

1. WHEN a negotiation request is submitted with vendor details, target discount percentage, and category THEN the system SHALL generate pricing proposals and contract terms
2. WHEN the negotiation agent proposes terms THEN the system SHALL route all outputs through GPCritic for policy compliance
3. WHEN aggressive discounts are requested THEN the system SHALL automatically add required warranties and protective clauses
4. IF the proposed terms violate company policies THEN the system SHALL auto-revise the output to ensure compliance

### Requirement 2

**User Story:** As a legal compliance officer, I want an automated compliance agent that can identify and rewrite risky contract clauses, so that all procurement contracts meet our legal and regulatory requirements.

#### Acceptance Criteria

1. WHEN a contract clause is submitted for review THEN the system SHALL identify potential legal and compliance risks
2. WHEN prohibited clauses are detected THEN the system SHALL automatically remove or rewrite them
3. WHEN risky terms are identified THEN the system SHALL flag them and provide compliant alternatives
4. WHEN compliance review is complete THEN the system SHALL route results through GPCritic for final validation

### Requirement 3

**User Story:** As a financial planning manager, I want a forecasting agent that aligns procurement plans with budgets and OKRs, so that spending stays within approved limits and supports business objectives.

#### Acceptance Criteria

1. WHEN forecast requests include category, quarter, and planned spend THEN the system SHALL analyze alignment with budgets and OKRs
2. WHEN spending variance exceeds defined thresholds THEN the system SHALL include trade-off explanations or budget adjustments
3. WHEN overspend scenarios are detected THEN the system SHALL enforce budget variance gates
4. WHEN forecasts are generated THEN the system SHALL ensure alignment with Global Policy Context requirements

### Requirement 4

**User Story:** As a system administrator, I want a Global Policy Critic that performs post-hoc validation of all agent outputs, so that enterprise policies are consistently enforced across all procurement decisions.

#### Acceptance Criteria

1. WHEN any agent generates output THEN the system SHALL route it through GPCritic for validation
2. WHEN GPCritic detects policy violations THEN the system SHALL auto-revise outputs to ensure compliance
3. WHEN GPCritic processes outputs THEN the system SHALL use only GPC and DSC contexts for validation
4. WHEN revisions are made THEN the system SHALL maintain the original intent while ensuring policy compliance

### Requirement 5

**User Story:** As a system architect, I want a layered, budgeted context architecture that prioritizes enterprise alignment, so that critical business policies are preserved even under token pressure.

#### Acceptance Criteria

1. WHEN the system operates under token pressure THEN the system SHALL prune contexts in order: ETC → TSC → DSC → GPC
2. WHEN Global Policy Context is loaded THEN the system SHALL ensure it remains pinned and non-prunable
3. WHEN context budgets are allocated THEN the system SHALL distribute as: GPC (25%), DSC (25%), TSC (40%), ETC (10%)
4. WHEN session data accumulates THEN the system SHALL summarize findings periodically while protecting PII

### Requirement 6

**User Story:** As a procurement system user, I want RESTful API endpoints for each agent type, so that I can integrate procurement intelligence into existing workflows and applications.

#### Acceptance Criteria

1. WHEN negotiation requests are made THEN the system SHALL provide POST /agent/negotiation endpoint accepting vendor, target_discount_pct, and category
2. WHEN compliance reviews are needed THEN the system SHALL provide POST /agent/compliance endpoint accepting clause data
3. WHEN forecasting is required THEN the system SHALL provide POST /agent/forecast endpoint accepting category, quarter, and planned_spend
4. WHEN API requests are processed THEN the system SHALL return structured responses with agent recommendations and policy compliance status

### Requirement 7

**User Story:** As a system operator, I want configurable policies and guardrails through environment variables, so that the system can be adapted to different organizational requirements without code changes.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL load budgets, guardrails, model configuration, and host settings from .env file
2. WHEN policies are defined in configuration THEN the system SHALL enforce prohibited and required clauses automatically
3. WHEN model parameters are configured THEN the system SHALL use specified Ollama model and host settings
4. WHEN configuration changes are made THEN the system SHALL apply new settings without requiring code modifications

### Requirement 8

**User Story:** As a quality assurance engineer, I want automated acceptance tests that validate enterprise alignment guarantees, so that the system consistently prioritizes business policies over local optimization.

#### Acceptance Criteria

1. WHEN negotiation adds discounts THEN the system SHALL automatically include required warranties (AT-1)
2. WHEN forecast variance exceeds thresholds THEN the system SHALL include trade-offs or adjustments (AT-2)
3. WHEN prohibited clauses are detected THEN the system SHALL remove or rewrite them via Compliance and GPCritic (AT-3)
4. WHEN hierarchical prompts are used THEN the system SHALL maintain shorter, cleaner prompts compared to flat prompt alternatives (AT-4)