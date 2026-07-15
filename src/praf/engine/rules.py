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
    GATHER_DATA = "gather_data"


# Overall precedence, most severe first. A genuine escalation from a
# well-covered domain still wins, but insufficient data outranks "revise":
# an unreliable verdict must not be quietly downgraded to a routine one.
_OVERALL_PRECEDENCE = [Decision.ESCALATE, Decision.GATHER_DATA, Decision.REVISE, Decision.PROCEED]

_LEVEL_TO_DECISION = {
    RiskLevel.ACCEPTABLE: Decision.PROCEED,
    RiskLevel.ACTION_REQUIRED: Decision.REVISE,
    RiskLevel.ESCALATION_REQUIRED: Decision.ESCALATE,
    RiskLevel.INSUFFICIENT_DATA: Decision.GATHER_DATA,
}


@dataclass(frozen=True)
class DecisionResult:
    overall: Decision
    per_domain: Dict[RiskDomain, Decision]


def decide(classifications: Dict[RiskDomain, DomainClassification]) -> DecisionResult:
    per_domain: Dict[RiskDomain, Decision] = {}
    overall = Decision.PROCEED
    overall_rank = _OVERALL_PRECEDENCE.index(Decision.PROCEED)

    for domain, c in classifications.items():
        decision = _LEVEL_TO_DECISION.get(c.level, Decision.PROCEED)
        per_domain[domain] = decision
        rank = _OVERALL_PRECEDENCE.index(decision)
        if rank < overall_rank:
            overall_rank = rank
            overall = decision

    return DecisionResult(overall=overall, per_domain=per_domain)
