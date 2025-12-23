from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

from praf.domain.decision_matrix import DecisionScenario, ControlDomain, DecisionMatrix, get_matrix, ControlExpectation
from praf.domain.user_risk import UserRisk


class ControlStatus(str, Enum):
    MISSING = "missing"
    PARTIAL = "partial"
    PRESENT = "present"


@dataclass(frozen=True)
class ControlCheck:
    control_id: str
    status: ControlStatus
    evidence_attached: bool


@dataclass(frozen=True)
class ReadinessGap:
    domain: ControlDomain
    control_id: str
    control_description: str
    minimum_required: bool
    status: str
    evidence_expected: List[str]
    evidence_attached: bool
    priority: str
    linked_risks: List[str]


@dataclass(frozen=True)
class ReadinessSummary:
    decision: DecisionScenario
    readiness: str
    rationale: str
    gaps: List[ReadinessGap]
    prioritised_domains: List[Tuple[str, int]]


def _priority_from_severity(sev: int) -> str:
    if sev >= 13:
        return "critical"
    if sev >= 10:
        return "high"
    if sev >= 7:
        return "medium"
    return "low"


def _domain_risk_severity(risks: List[UserRisk]) -> Dict[ControlDomain, int]:
    out: Dict[ControlDomain, int] = {}
    for r in risks:
        if r.mapped_domain is None:
            continue
        s = r.severity()
        prev = int(out.get(r.mapped_domain, 0))
        out[r.mapped_domain] = max(prev, s)
    return out


def _linked_risk_ids(risks: List[UserRisk], domain: ControlDomain) -> List[str]:
    ids: List[str] = []
    for r in risks:
        if r.mapped_domain == domain:
            ids.append(r.risk_id)
    return ids


def evaluate_decision_readiness(
    decision: DecisionScenario,
    risks: List[UserRisk],
    control_checks: Dict[str, ControlCheck],
) -> ReadinessSummary:
    matrix: DecisionMatrix = get_matrix(decision)

    domain_severity = _domain_risk_severity(risks)
    prioritised_domains = sorted(
        [(d.value, int(domain_severity.get(d, 0))) for d in matrix.domains.keys()],
        key=lambda x: x[1],
        reverse=True,
    )

    gaps: List[ReadinessGap] = []
    blocking_missing = 0

    for domain, expectations in matrix.domains.items():
        sev = int(domain_severity.get(domain, 0))
        domain_priority = _priority_from_severity(sev)
        linked = _linked_risk_ids(risks, domain)

        for exp in expectations:
            ck = control_checks.get(exp.control_id)
            if ck is None:
                status = ControlStatus.MISSING
                evidence_attached = False
            else:
                status = ck.status
                evidence_attached = bool(ck.evidence_attached)

            is_gap = (status != ControlStatus.PRESENT) or (not evidence_attached and exp.minimum_required)
            if not is_gap:
                continue

            if exp.minimum_required and status != ControlStatus.PRESENT:
                blocking_missing += 1
            if exp.minimum_required and (not evidence_attached):
                blocking_missing += 1

            gaps.append(
                ReadinessGap(
                    domain=domain,
                    control_id=exp.control_id,
                    control_description=exp.control_description,
                    minimum_required=bool(exp.minimum_required),
                    status=status.value,
                    evidence_expected=list(exp.expected_evidence),
                    evidence_attached=bool(evidence_attached),
                    priority=domain_priority,
                    linked_risks=list(linked),
                )
            )

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps_sorted = sorted(gaps, key=lambda g: (order.get(g.priority, 9), 0 if g.minimum_required else 1))

    if blocking_missing > 0:
        readiness = "not_ready"
        rationale = "Decision readiness is limited due to missing minimum required controls or missing required evidence."
    else:
        if len(gaps_sorted) > 0:
            readiness = "conditionally_ready"
            rationale = "Decision readiness is acceptable with conditions, as non minimum gaps remain."
        else:
            readiness = "ready"
            rationale = "Decision readiness is acceptable, with minimum required controls and evidence present."

    return ReadinessSummary(
        decision=decision,
        readiness=readiness,
        rationale=rationale,
        gaps=gaps_sorted,
        prioritised_domains=prioritised_domains,
    )


def build_empty_control_checks(matrix: DecisionMatrix) -> Dict[str, ControlCheck]:
    out: Dict[str, ControlCheck] = {}
    for domain, exps in matrix.domains.items():
        for exp in exps:
            out[exp.control_id] = ControlCheck(control_id=exp.control_id, status=ControlStatus.MISSING, evidence_attached=False)
    return out
