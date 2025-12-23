from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from praf.engine.classifier import DomainClassification, RiskLevel
from praf.domain.domains import RiskDomain


class Decision(str, Enum):
    PROCEED = "proceed"
    REVISE = "revise"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class DecisionResult:
    overall: Decision
    per_domain: Dict[RiskDomain, Decision]


def decide(classifications: Dict[RiskDomain, DomainClassification]) -> DecisionResult:
    per_domain: Dict[RiskDomain, Decision] = {}
    overall = Decision.PROCEED

    for domain, c in classifications.items():
        if c.level == RiskLevel.ACCEPTABLE:
            per_domain[domain] = Decision.PROCEED
        elif c.level == RiskLevel.ACTION_REQUIRED:
            per_domain[domain] = Decision.REVISE
            if overall != Decision.ESCALATE:
                overall = Decision.REVISE
        else:
            per_domain[domain] = Decision.ESCALATE
            overall = Decision.ESCALATE

    return DecisionResult(overall=overall, per_domain=per_domain)
