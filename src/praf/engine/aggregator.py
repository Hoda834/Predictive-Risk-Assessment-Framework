from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from praf.domain.domains import RiskDomain


@dataclass(frozen=True)
class AggregatedResult:
    domain_scores: Dict[RiskDomain, float]
    category_scores: Dict[str, float]


def aggregate_scores(indicator_details: Dict[str, Dict[str, Any]], local_scores: Dict[str, float]) -> AggregatedResult:
    domain_scores: Dict[RiskDomain, float] = {}
    category_scores: Dict[str, float] = {}

    for indicator_id, meta in indicator_details.items():
        score = float(local_scores.get(indicator_id, 0.0))
        domain = RiskDomain(meta["domain"])
        category = str(meta["category"])

        domain_scores[domain] = float(domain_scores.get(domain, 0.0) + score)
        category_scores[category] = float(category_scores.get(category, 0.0) + score)

    return AggregatedResult(domain_scores=domain_scores, category_scores=category_scores)
