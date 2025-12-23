from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

from praf.engine.rules import DecisionResult
from praf.engine.classifier import DomainClassification
from praf.domain.domains import RiskDomain


@dataclass(frozen=True)
class AuditEntry:
    key: str
    value: Any


def build_audit_trail(
    classifications: Dict[RiskDomain, DomainClassification],
    decision: DecisionResult,
    indicator_details: Dict[str, Dict[str, Any]],
    local_scores: Dict[str, float],
) -> List[AuditEntry]:
    entries: List[AuditEntry] = []

    entries.append(AuditEntry(key="overall_decision", value=decision.overall.value))

    per_domain = {d.value: decision.per_domain[d].value for d in decision.per_domain}
    entries.append(AuditEntry(key="per_domain_decision", value=per_domain))

    scores = {d.value: {"score": c.score, "level": c.level.value} for d, c in classifications.items()}
    entries.append(AuditEntry(key="domain_scores", value=scores))

    entries.append(AuditEntry(key="indicator_details", value=indicator_details))
    entries.append(AuditEntry(key="local_scores", value=local_scores))

    return entries
