from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from praf.domain.activities import Context, ProjectStage
from praf.domain.risk_patterns import RiskPattern, UserRisk


class GateGuidance(str, Enum):
    PROCEED = "proceed"
    PROCEED_WITH_CONDITIONS = "proceed_with_conditions"
    HOLD_PENDING_CONTROLS = "hold_pending_controls"
    REVIEW_BEFORE_NEXT_STAGE = "review_before_next_stage"


@dataclass(frozen=True)
class RiskGuidance:
    risk_id: str
    pattern: RiskPattern
    priority: str
    gate_guidance: GateGuidance
    why: str
    recommended_actions: List[str]
    expected_evidence: List[str]


@dataclass(frozen=True)
class GuidanceSummary:
    overall_gate_guidance: GateGuidance
    rationale: str
    items: List[RiskGuidance]


def _priority(l: int, i: int, d: int) -> str:
    severity = l + i + d
    if i >= 5 and l >= 4:
        return "critical"
    if severity >= 12:
        return "high"
    if severity >= 9:
        return "medium"
    return "low"


def _gate_from_priority(stage: ProjectStage, priority: str) -> GateGuidance:
    if priority == "critical":
        return GateGuidance.HOLD_PENDING_CONTROLS
    if priority == "high":
        if stage in {ProjectStage.CONCEPT, ProjectStage.DESIGN}:
            return GateGuidance.PROCEED_WITH_CONDITIONS
        return GateGuidance.REVIEW_BEFORE_NEXT_STAGE
    if priority == "medium":
        return GateGuidance.REVIEW_BEFORE_NEXT_STAGE
    return GateGuidance.PROCEED


def _actions_for_pattern(pattern: RiskPattern) -> List[str]:
    mapping = {
        RiskPattern.SUPPLIER_RELIABILITY: [
            "Define supplier change notification rule",
            "Define incoming inspection criteria",
            "Define second source or contingency plan",
        ],
        RiskPattern.PROCESS_VARIABILITY: [
            "Define critical process parameters",
            "Define batch variability monitoring",
            "Define acceptance criteria for release decisions",
        ],
        RiskPattern.DESIGN_MATURITY: [
            "Create assumptions and rationale log",
            "Define design review checkpoint and outputs",
            "Define change control for design decisions",
        ],
        RiskPattern.MEASUREMENT_INTEGRITY: [
            "Define calibration and drift monitoring approach",
            "Define environmental sensitivity checks",
            "Define criteria for re verification triggers",
        ],
        RiskPattern.DATA_INTEGRITY: [
            "Define data capture plan and ownership",
            "Define audit trail for changes and decisions",
            "Define data quality checks",
        ],
        RiskPattern.EVIDENCE_SUFFICIENCY: [
            "Define what evidence is required for this stage",
            "Define test plan or evaluation plan",
            "Define acceptance criteria for evidence completeness",
        ],
        RiskPattern.GOVERNANCE_ACCOUNTABILITY: [
            "Define decision thresholds and escalation rules",
            "Define accountable owner for each decision gate",
            "Define decision log format and review cadence",
        ],
        RiskPattern.REGULATORY_READINESS: [
            "Define required documentation set for this stage",
            "Define traceability between requirements and evidence",
            "Define review checklist for readiness gaps",
        ],
        RiskPattern.OPERATIONAL_CONTINUITY: [
            "Define failure scenarios and recovery steps",
            "Define monitoring and incident logging",
            "Define continuity expectations and responsibilities",
        ],
        RiskPattern.OTHER: [
            "Clarify risk statement and expected impact",
            "Define a control objective",
            "Define evidence to confirm controls are working",
        ],
    }
    return list(mapping.get(pattern, mapping[RiskPattern.OTHER]))


def _evidence_for_pattern(pattern: RiskPattern) -> List[str]:
    mapping = {
        RiskPattern.SUPPLIER_RELIABILITY: [
            "Supplier change rule document",
            "Incoming inspection checklist",
            "Supplier contingency note",
        ],
        RiskPattern.PROCESS_VARIABILITY: [
            "Critical process parameters list",
            "Variability monitoring plan",
            "Release acceptance criteria",
        ],
        RiskPattern.DESIGN_MATURITY: [
            "Assumptions and rationale log",
            "Design review record",
            "Change control record",
        ],
        RiskPattern.MEASUREMENT_INTEGRITY: [
            "Calibration plan",
            "Sensitivity check record",
            "Re verification trigger criteria",
        ],
        RiskPattern.DATA_INTEGRITY: [
            "Data capture plan",
            "Audit trail entry template",
            "Data quality check list",
        ],
        RiskPattern.EVIDENCE_SUFFICIENCY: [
            "Evidence checklist for this stage",
            "Test or evaluation plan",
            "Evidence acceptance criteria",
        ],
        RiskPattern.GOVERNANCE_ACCOUNTABILITY: [
            "Escalation thresholds document",
            "Decision ownership matrix",
            "Decision log sample entry",
        ],
        RiskPattern.REGULATORY_READINESS: [
            "Documentation checklist",
            "Traceability mapping note",
            "Readiness gap review record",
        ],
        RiskPattern.OPERATIONAL_CONTINUITY: [
            "Failure scenarios list",
            "Incident log template",
            "Recovery steps note",
        ],
        RiskPattern.OTHER: [
            "Risk clarification note",
            "Control objective statement",
            "Evidence definition note",
        ],
    }
    return list(mapping.get(pattern, mapping[RiskPattern.OTHER]))


def generate_guidance(ctx: Context, risks: List[UserRisk]) -> GuidanceSummary:
    items: List[RiskGuidance] = []

    for r in risks:
        if r.pattern is None:
            continue

        pr = _priority(r.likelihood, r.impact, r.detectability)
        gate = _gate_from_priority(ctx.stage, pr)

        why = f"Pattern is {r.pattern.value} with L I D {r.likelihood} {r.impact} {r.detectability} at stage {ctx.stage.value}"

        items.append(
            RiskGuidance(
                risk_id=r.risk_id,
                pattern=r.pattern,
                priority=pr,
                gate_guidance=gate,
                why=why,
                recommended_actions=_actions_for_pattern(r.pattern),
                expected_evidence=_evidence_for_pattern(r.pattern),
            )
        )

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items_sorted = sorted(items, key=lambda x: order.get(x.priority, 9))

    overall = GateGuidance.PROCEED
    for it in items_sorted:
        if it.gate_guidance == GateGuidance.HOLD_PENDING_CONTROLS:
            overall = GateGuidance.HOLD_PENDING_CONTROLS
            break
        if it.gate_guidance == GateGuidance.PROCEED_WITH_CONDITIONS and overall != GateGuidance.HOLD_PENDING_CONTROLS:
            overall = GateGuidance.PROCEED_WITH_CONDITIONS
        if it.gate_guidance == GateGuidance.REVIEW_BEFORE_NEXT_STAGE and overall == GateGuidance.PROCEED:
            overall = GateGuidance.REVIEW_BEFORE_NEXT_STAGE

    rationale = "Overall guidance is derived from the highest priority mapped risks in the selected context"

    return GuidanceSummary(
        overall_gate_guidance=overall,
        rationale=rationale,
        items=items_sorted,
    )
