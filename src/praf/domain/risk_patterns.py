from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RiskPattern(str, Enum):
    SUPPLIER_RELIABILITY = "supplier_reliability"
    PROCESS_VARIABILITY = "process_variability"
    DESIGN_MATURITY = "design_maturity"
    MEASUREMENT_INTEGRITY = "measurement_integrity"
    DATA_INTEGRITY = "data_integrity"
    EVIDENCE_SUFFICIENCY = "evidence_sufficiency"
    GOVERNANCE_ACCOUNTABILITY = "governance_accountability"
    REGULATORY_READINESS = "regulatory_readiness"
    OPERATIONAL_CONTINUITY = "operational_continuity"
    OTHER = "other"


@dataclass(frozen=True)
class UserRisk:
    risk_id: str
    description: str
    owner: str
    likelihood: int
    impact: int
    detectability: int
    pattern: Optional[RiskPattern] = None


def suggest_pattern_from_text(text: str) -> RiskPattern:
    t = (text or "").strip().lower()

    if any(k in t for k in ["supplier", "vendor", "procurement", "lead time", "single source", "subcontract"]):
        return RiskPattern.SUPPLIER_RELIABILITY

    if any(k in t for k in ["batch", "variability", "process", "yield", "defect", "scrap", "manufactur"]):
        return RiskPattern.PROCESS_VARIABILITY

    if any(k in t for k in ["assumption", "architecture", "requirement", "specification", "design change"]):
        return RiskPattern.DESIGN_MATURITY

    if any(k in t for k in ["calibration", "drift", "stability", "noise", "environment", "temperature", "humidity"]):
        return RiskPattern.MEASUREMENT_INTEGRITY

    if any(k in t for k in ["data", "integrity", "logging", "audit trail", "trace", "traceability"]):
        return RiskPattern.DATA_INTEGRITY

    if any(k in t for k in ["evidence", "validation", "verification", "test plan", "dataset", "sample size"]):
        return RiskPattern.EVIDENCE_SUFFICIENCY

    if any(k in t for k in ["governance", "decision", "threshold", "escalation", "approval", "owner"]):
        return RiskPattern.GOVERNANCE_ACCOUNTABILITY

    if any(k in t for k in ["regulatory", "compliance", "submission", "standard", "iso", "documentation"]):
        return RiskPattern.REGULATORY_READINESS

    if any(k in t for k in ["continuity", "availability", "downtime", "failure", "disruption", "support"]):
        return RiskPattern.OPERATIONAL_CONTINUITY

    return RiskPattern.OTHER
