---
inclusion: fileMatch
fileMatchPattern: "src/agents/compliance*"
description: "Detailed compliance rules and validation criteria"
---

# Compliance Rules and Validation Criteria

## Legal and Regulatory Compliance

### Data Protection (GDPR/CCPA)
- All vendor contracts must include data processing agreements
- Specify data retention and deletion procedures
- Require breach notification within 72 hours
- Ensure right to data portability and erasure

### Financial Regulations
- Comply with SOX requirements for financial controls
- Maintain audit trails for all procurement decisions
- Ensure proper segregation of duties
- Document approval workflows

### Industry Standards
- ISO 27001 for information security management
- SOC 2 Type II for service organizations
- PCI DSS for payment processing vendors
- HIPAA for healthcare-related services

## Contract Compliance Framework

### Risk Assessment Matrix
- **High Risk**: Contracts >$500K, new vendors, critical systems
- **Medium Risk**: Contracts $100K-$500K, established vendors
- **Low Risk**: Contracts <$100K, pre-approved vendors

### Validation Checkpoints
1. **Legal Review**: All high-risk contracts
2. **Security Review**: All technology vendors
3. **Financial Review**: All contracts >$250K
4. **Business Review**: All strategic partnerships

## Automated Compliance Checks

### Prohibited Clause Detection
```yaml
prohibited_patterns:
  - "unlimited liability"
  - "waiver of rights"
  - "automatic renewal"
  - "exclusive dealing"
  - "no termination rights"
```

### Required Clause Validation
```yaml
required_clauses:
  - "data protection"
  - "warranty"
  - "termination rights"
  - "liability limitation"
  - "governing law"
```

## Escalation Procedures

### Compliance Violations
1. **Immediate**: Block contract execution
2. **Within 24 hours**: Notify legal and procurement teams
3. **Within 48 hours**: Provide remediation plan
4. **Within 1 week**: Implement corrective measures

### Exception Handling
- Document business justification
- Obtain appropriate approvals
- Implement additional controls
- Schedule periodic reviews

## Audit and Monitoring

### Continuous Monitoring
- Real-time contract compliance scanning
- Automated policy violation alerts
- Performance metric tracking
- Vendor risk assessment updates

### Periodic Reviews
- Quarterly compliance assessments
- Annual policy updates
- Vendor performance evaluations
- Contract renewal evaluations

This framework ensures all procurement activities maintain the highest standards of legal and regulatory compliance.