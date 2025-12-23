from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from praf.domain.domains import RiskDomain


@dataclass(frozen=True)
class AggregatedResult:
    domain_scores: Dict[RiskDomain, float]
    category_scores: Dict[str, float]
    domain_counts: Dict[RiskDomain, int]


def aggregate_scores(indicator_details: Dict[str, Dict[str, Any]], local_scores: Dict[str, float]) -> AggregatedResult:
    domain_sum: Dict[RiskDomain, float] = {}
    domain_counts: Dict[RiskDomain, int] = {}
    category_sum: Dict[str, float] = {}
    category_counts: Dict[str, int] = {}

    for indicator_id, meta in indicator_details.items():
        score = float(local_scores.get(indicator_id, 0.0))
        domain = RiskDomain(meta["domain"])
        category = str(meta["category"])

        domain_sum[domain] = float(domain_sum.get(domain, 0.0) + score)
        domain_counts[domain] = int(domain_counts.get(domain, 0) + 1)

        category_sum[category] = float(category_sum.get(category, 0.0) + score)
        category_counts[category] = int(category_counts.get(category, 0) + 1)

    domain_avg: Dict[RiskDomain, float] = {}
    for d in domain_sum:
        c = max(1, int(domain_counts.get(d, 1)))
        domain_avg[d] = float(domain_sum[d] / c)

    category_avg: Dict[str, float] = {}
    for k in category_sum:
        c = max(1, int(category_counts.get(k, 1)))
        category_avg[k] = float(category_sum[k] / c)

    return AggregatedResult(domain_scores=domain_avg, category_scores=category_avg, domain_counts=domain_counts)
