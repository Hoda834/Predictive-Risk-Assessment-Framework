from __future__ import annotations

from enum import Enum
from typing import Dict

from .activities import Activity


class RiskDomain(str, Enum):
    DESIGN_MATURITY = "design_maturity"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    MANUFACTURING = "manufacturing"
    MEASUREMENT_INTEGRITY = "measurement_integrity"
    SUPPLY_CHAIN = "supply_chain"
    DATA_EVIDENCE = "data_evidence"
    DECISION_GOVERNANCE = "decision_governance"


def activity_domain_weights(activity: Activity) -> Dict[RiskDomain, float]:
    base = {
        RiskDomain.DESIGN_MATURITY: 1.0,
        RiskDomain.REGULATORY_COMPLIANCE: 1.0,
        RiskDomain.MANUFACTURING: 1.0,
        RiskDomain.MEASUREMENT_INTEGRITY: 1.0,
        RiskDomain.SUPPLY_CHAIN: 1.0,
        RiskDomain.DATA_EVIDENCE: 1.0,
        RiskDomain.DECISION_GOVERNANCE: 1.0,
    }

    mapping = {
        Activity.PRODUCT_DESIGN: {
            RiskDomain.DESIGN_MATURITY: 1.25,
            RiskDomain.REGULATORY_COMPLIANCE: 1.15,
            RiskDomain.DATA_EVIDENCE: 1.10,
            RiskDomain.DECISION_GOVERNANCE: 1.10,
        },
        Activity.PROTOTYPE_DEVELOPMENT: {
            RiskDomain.MEASUREMENT_INTEGRITY: 1.20,
            RiskDomain.DESIGN_MATURITY: 1.10,
            RiskDomain.DATA_EVIDENCE: 1.10,
        },
        Activity.MANUFACTURING_SCALE_UP: {
            RiskDomain.MANUFACTURING: 1.30,
            RiskDomain.SUPPLY_CHAIN: 1.20,
            RiskDomain.REGULATORY_COMPLIANCE: 1.10,
        },
        Activity.SUPPLIER_SELECTION: {
            RiskDomain.SUPPLY_CHAIN: 1.35,
            RiskDomain.MANUFACTURING: 1.10,
        },
        Activity.REGULATORY_PREPARATION: {
            RiskDomain.REGULATORY_COMPLIANCE: 1.40,
            RiskDomain.DATA_EVIDENCE: 1.20,
            RiskDomain.DECISION_GOVERNANCE: 1.10,
        },
        Activity.DATA_COLLECTION: {
            RiskDomain.DATA_EVIDENCE: 1.40,
            RiskDomain.DECISION_GOVERNANCE: 1.10,
        },
        Activity.SYSTEM_DESIGN: {
            RiskDomain.DESIGN_MATURITY: 1.15,
            RiskDomain.DECISION_GOVERNANCE: 1.20,
            RiskDomain.DATA_EVIDENCE: 1.10,
        },
        Activity.PROCESS_OPTIMISATION: {
            RiskDomain.MANUFACTURING: 1.15,
            RiskDomain.DECISION_GOVERNANCE: 1.15,
        },
    }

    boosts = mapping.get(activity, {})
    for d, w in boosts.items():
        base[d] = w

    return base
