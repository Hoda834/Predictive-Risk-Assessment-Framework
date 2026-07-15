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

    Each ``local_scores`` value is a weighted contribution
    ``severity * (nature_weight * indicator_weight)`` (severity in 0..1). The
    domain/category index is computed in two steps:

    1. A weight-normalised mean of the severities scaled to 0..100::

           base_index = 100 * sum(severity_i * w_i) / sum(w_i)

       where ``w_i = nature_weight * indicator_weight``. This is bounded to
       [0, 100] regardless of how many indicators a domain has, so any domain
       can reach the escalation threshold.

    2. The activity-dependent **domain weight** is applied as a sensitivity
       multiplier and capped at 100::

           index = min(100, base_index * domain_weight)

    The domain weight is constant across a domain's indicators, so it would
    cancel out of step 1's normalised mean; applying it afterwards is what makes
    context-aware weighting actually shift the classification of the domains an
    activity emphasises.
    """
    domain_sum: Dict[RiskDomain, float] = {}
    domain_weight_ex: Dict[RiskDomain, float] = {}
    domain_dw: Dict[RiskDomain, float] = {}
    domain_counts: Dict[RiskDomain, int] = {}
    category_sum: Dict[str, float] = {}
    category_weight_ex: Dict[str, float] = {}
    category_dw: Dict[str, float] = {}

    for indicator_id, meta in indicator_details.items():
        contribution = float(local_scores.get(indicator_id, 0.0))
        weight = float(meta.get("weight_ex_domain", 1.0))
        dw = float(meta.get("domain_weight", 1.0))
        domain = RiskDomain(meta["domain"])
        category = str(meta["category"])

        domain_sum[domain] = float(domain_sum.get(domain, 0.0) + contribution)
        domain_weight_ex[domain] = float(domain_weight_ex.get(domain, 0.0) + weight)
        domain_dw[domain] = dw  # constant across a domain's indicators
        domain_counts[domain] = int(domain_counts.get(domain, 0) + 1)

        category_sum[category] = float(category_sum.get(category, 0.0) + contribution)
        category_weight_ex[category] = float(category_weight_ex.get(category, 0.0) + weight)
        category_dw[category] = dw

    domain_index: Dict[RiskDomain, float] = {}
    for d in domain_sum:
        w = domain_weight_ex.get(d, 0.0)
        base_index = 100.0 * domain_sum[d] / w if w > 0.0 else 0.0
        domain_index[d] = float(min(100.0, base_index * domain_dw.get(d, 1.0)))

    category_index: Dict[str, float] = {}
    for k in category_sum:
        w = category_weight_ex.get(k, 0.0)
        base_index = 100.0 * category_sum[k] / w if w > 0.0 else 0.0
        category_index[k] = float(min(100.0, base_index * category_dw.get(k, 1.0)))

    return AggregatedResult(domain_scores=domain_index, category_scores=category_index, domain_counts=domain_counts)
