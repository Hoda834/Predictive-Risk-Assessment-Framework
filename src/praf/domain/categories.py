from __future__ import annotations

from enum import Enum
from typing import Dict, tuple

from .domains import RiskDomain


class RiskCategory(str, Enum):
    UNVALIDATED_ASSUMPTIONS = "unvalidated_assumptions"
    RATIONALE_GAPS = "rationale_gaps"
    TRACEABILITY_GAPS = "traceability_gaps"
    DOCUMENTATION_GAPS = "documentation_gaps"
    ENVIRONMENTAL_SENSITIVITY = "environmental_sensitivity"
    DRIFT_STABILITY = "drift_stability"
    BATCH_VARIABILITY = "batch_variability"
    QC_GAPS = "qc_gaps"
    SINGLE_SOURCE_SUPPLIER = "single_source_supplier"
    SUPPLIER_CHANGE_RISK = "supplier_change_risk"
    DATA_DEFINITION_GAPS = "data_definition_gaps"
    AUDIT_TRAIL_GAPS = "audit_trail_gaps"
    THRESHOLD_GAPS = "threshold_gaps"
    ESCALATION_GAPS = "escalation_gaps"


DOMAIN_TO_CATEGORIES: Dict[RiskDomain, tuple[RiskCategory, ...]] = {
    RiskDomain.DESIGN_MATURITY: (
        RiskCategory.UNVALIDATED_ASSUMPTIONS,
        RiskCategory.RATIONALE_GAPS,
        RiskCategory.TRACEABILITY_GAPS,
    ),
    RiskDomain.REGULATORY_COMPLIANCE: (
        RiskCategory.DOCUMENTATION_GAPS,
        RiskCategory.TRACEABILITY_GAPS,
    ),
    RiskDomain.MEASUREMENT_INTEGRITY: (
        RiskCategory.ENVIRONMENTAL_SENSITIVITY,
        RiskCategory.DRIFT_STABILITY,
    ),
    RiskDomain.MANUFACTURING: (
        RiskCategory.BATCH_VARIABILITY,
        RiskCategory.QC_GAPS,
    ),
    RiskDomain.SUPPLY_CHAIN: (
        RiskCategory.SINGLE_SOURCE_SUPPLIER,
        RiskCategory.SUPPLIER_CHANGE_RISK,
    ),
    RiskDomain.DATA_EVIDENCE: (
        RiskCategory.DATA_DEFINITION_GAPS,
        RiskCategory.AUDIT_TRAIL_GAPS,
    ),
    RiskDomain.DECISION_GOVERNANCE: (
        RiskCategory.THRESHOLD_GAPS,
        RiskCategory.ESCALATION_GAPS,
        RiskCategory.AUDIT_TRAIL_GAPS,
    ),
}
