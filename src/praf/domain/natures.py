from __future__ import annotations

from enum import Enum


class RiskNature(str, Enum):
    STRUCTURAL = "structural"
    TECHNICAL = "technical"
    PROCESS = "process"
    EXTERNAL_DEPENDENCY = "external_dependency"
    DECISION_GOVERNANCE = "decision_governance"


def nature_weight_modifier(nature: RiskNature) -> float:
    mapping = {
        RiskNature.STRUCTURAL: 1.25,
        RiskNature.TECHNICAL: 1.00,
        RiskNature.PROCESS: 1.05,
        RiskNature.EXTERNAL_DEPENDENCY: 1.15,
        RiskNature.DECISION_GOVERNANCE: 1.20,
    }
    return float(mapping.get(nature, 1.0))
