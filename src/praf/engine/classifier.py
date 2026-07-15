from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from praf.domain.domains import RiskDomain


class RiskLevel(str, Enum):
    ACCEPTABLE = "acceptable"
    ACTION_REQUIRED = "action_required"
    ESCALATION_REQUIRED = "escalation_required"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class DomainClassification:
    domain: RiskDomain
    score: float
    level: RiskLevel
    coverage: float = 1.0


def classify_domains(
    domain_scores: Dict[RiskDomain, float],
    low_threshold: float,
    high_threshold: float,
    coverage: Optional[Dict[RiskDomain, float]] = None,
    coverage_threshold: float = 0.0,
) -> Dict[RiskDomain, DomainClassification]:
    """Classify each domain index against the thresholds.

    If ``coverage`` is supplied and a domain's coverage (fraction of its
    indicators that were actually answered) is below ``coverage_threshold``,
    the domain is reported as ``INSUFFICIENT_DATA`` instead of a risk level:
    "we don't have enough input to judge this" must be distinguishable from
    "the risk is medium". Passing no coverage (the default) preserves the
    original behaviour.
    """
    results: Dict[RiskDomain, DomainClassification] = {}
    for domain, score in domain_scores.items():
        s = float(score)
        cov = float(coverage.get(domain, 1.0)) if coverage is not None else 1.0

        if coverage is not None and cov < coverage_threshold:
            level = RiskLevel.INSUFFICIENT_DATA
        elif s < low_threshold:
            level = RiskLevel.ACCEPTABLE
        elif s < high_threshold:
            level = RiskLevel.ACTION_REQUIRED
        else:
            level = RiskLevel.ESCALATION_REQUIRED

        results[domain] = DomainClassification(domain=domain, score=s, level=level, coverage=cov)
    return results
