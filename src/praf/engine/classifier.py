from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from praf.domain.domains import RiskDomain


class RiskLevel(str, Enum):
    ACCEPTABLE = "acceptable"
    ACTION_REQUIRED = "action_required"
    ESCALATION_REQUIRED = "escalation_required"


@dataclass(frozen=True)
class DomainClassification:
    domain: RiskDomain
    score: float
    level: RiskLevel


def classify_domains(domain_scores: Dict[RiskDomain, float], low_threshold: float, high_threshold: float) -> Dict[RiskDomain, DomainClassification]:
    results: Dict[RiskDomain, DomainClassification] = {}
    for domain, score in domain_scores.items():
        s = float(score)
        if s < low_threshold:
            level = RiskLevel.ACCEPTABLE
        elif s < high_threshold:
            level = RiskLevel.ACTION_REQUIRED
        else:
            level = RiskLevel.ESCALATION_REQUIRED
        results[domain] = DomainClassification(domain=domain, score=s, level=level)
    return results
