"""
Global Policy Critic module for ProcureSense.

This module provides the GPCritic system that validates all agent outputs
against enterprise policies using only GPC and DSC contexts.
"""

from .gp_critic import GlobalPolicyCritic
from .critic_types import (
    PolicyViolation,
    ViolationType,
    CriticResult,
    ComplianceReport,
    RevisionAction
)

__all__ = [
    'GlobalPolicyCritic',
    'PolicyViolation',
    'ViolationType', 
    'CriticResult',
    'ComplianceReport',
    'RevisionAction'
]