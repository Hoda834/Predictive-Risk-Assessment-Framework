from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from praf.engine.classifier import DomainClassification
from praf.domain.domains import RiskDomain


@dataclass(frozen=True)
class Explanation:
    top_contributors_by_domain: Dict[RiskDomain, List[Tuple[str, float]]]


def explain(
    classifications: Dict[RiskDomain, DomainClassification],
    indicator_details: Dict[str, Dict[str, Any]],
    local_scores: Dict[str, float],
    top_n: int = 5,
) -> Explanation:
    domain_to_items: Dict[RiskDomain, List[Tuple[str, float]]] = {}

    for indicator_id, meta in indicator_details.items():
        domain = RiskDomain(meta["domain"])
        score = float(local_scores.get(indicator_id, 0.0))
        domain_to_items.setdefault(domain, []).append((indicator_id, score))

    top_by_domain: Dict[RiskDomain, List[Tuple[str, float]]] = {}
    for domain in classifications.keys():
        items = domain_to_items.get(domain, [])
        items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
        top_by_domain[domain] = items_sorted[: max(0, int(top_n))]

    return Explanation(top_contributors_by_domain=top_by_domain)
