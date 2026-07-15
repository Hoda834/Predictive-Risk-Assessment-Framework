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
    """Aggregate per-indicator contributions into 0..100 risk indices.

    Each ``local_scores`` value is a weighted contribution ``severity * weight``
    (severity in 0..1). The domain/category index is the weight-normalised mean
    of the severities scaled to 0..100::

        index = 100 * sum(severity_i * weight_i) / sum(weight_i)

    Because it is normalised by the total weight, the index is bounded to
    [0, 100] regardless of how many indicators a domain has or how large their
    weights are, so any domain can reach the escalation threshold.
    """
    domain_sum: Dict[RiskDomain, float] = {}
    domain_weight: Dict[RiskDomain, float] = {}
    domain_counts: Dict[RiskDomain, int] = {}
    category_sum: Dict[str, float] = {}
    category_weight: Dict[str, float] = {}

    for indicator_id, meta in indicator_details.items():
        contribution = float(local_scores.get(indicator_id, 0.0))
        weight = float(meta.get("weight_product", 1.0))
        domain = RiskDomain(meta["domain"])
        category = str(meta["category"])

        domain_sum[domain] = float(domain_sum.get(domain, 0.0) + contribution)
        domain_weight[domain] = float(domain_weight.get(domain, 0.0) + weight)
        domain_counts[domain] = int(domain_counts.get(domain, 0) + 1)

        category_sum[category] = float(category_sum.get(category, 0.0) + contribution)
        category_weight[category] = float(category_weight.get(category, 0.0) + weight)

    domain_index: Dict[RiskDomain, float] = {}
    for d in domain_sum:
        w = domain_weight.get(d, 0.0)
        domain_index[d] = float(100.0 * domain_sum[d] / w) if w > 0.0 else 0.0

    category_index: Dict[str, float] = {}
    for k in category_sum:
        w = category_weight.get(k, 0.0)
        category_index[k] = float(100.0 * category_sum[k] / w) if w > 0.0 else 0.0

    return AggregatedResult(domain_scores=domain_index, category_scores=category_index, domain_counts=domain_counts)
