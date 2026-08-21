from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from praf.engine.rules import DecisionResult
from praf.engine.classifier import DomainClassification
from praf.engine.severity_guard import SeverityOverride
from praf.domain.domains import RiskDomain
from praf import __version__, MODEL_VERSION, SCHEMA_VERSION


@dataclass(frozen=True)
class AuditEntry:
    key: str
    value: Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_audit_trail(
    classifications: Dict[RiskDomain, DomainClassification],
    decision: DecisionResult,
    indicator_details: Dict[str, Dict[str, Any]],
    local_scores: Dict[str, float],
    *,
    context: Optional[Dict[str, Any]] = None,
    thresholds: Optional[Dict[str, float]] = None,
    input_completeness: Optional[Dict[str, Any]] = None,
    severity_overrides: Optional[List[SeverityOverride]] = None,
    generated_at: Optional[str] = None,
    initial_summary: Optional[Dict[str, Any]] = None,
    residual_summary: Optional[Dict[str, Any]] = None,
    controls: Optional[List[Dict[str, Any]]] = None,
    control_issues: Optional[List[str]] = None,
    traceability: Optional[List[Dict[str, Any]]] = None,
    sensitivity: Optional[Dict[str, Any]] = None,
) -> List[AuditEntry]:
    """Assemble a traceable record of an assessment.

    Beyond the results themselves, the trail now records *what produced them* so
    the record is reproducible and defensible (ISO 14971 traceability /
    ISO 13485 records): a UTC timestamp, the software and risk-model versions,
    the acceptability thresholds in force, the project context, the completeness
    of the input, and any severity-guard overrides that were applied.

    ``generated_at`` may be injected (e.g. by tests) for a deterministic record;
    otherwise the current UTC time is stamped.
    """
    entries: List[AuditEntry] = []

    # --- Provenance / metadata (who/when/which-version) -------------------
    entries.append(AuditEntry(key="schema_version", value=SCHEMA_VERSION))
    entries.append(AuditEntry(key="tool_version", value=__version__))
    entries.append(AuditEntry(key="model_version", value=MODEL_VERSION))
    entries.append(AuditEntry(key="generated_at", value=generated_at or _utc_now_iso()))
    if context is not None:
        entries.append(AuditEntry(key="context", value=context))
    if thresholds is not None:
        entries.append(AuditEntry(key="thresholds", value=thresholds))
    if input_completeness is not None:
        entries.append(AuditEntry(key="input_completeness", value=input_completeness))

    # --- Decisions and scores --------------------------------------------
    entries.append(AuditEntry(key="overall_decision", value=decision.overall.value))

    per_domain = {d.value: decision.per_domain[d].value for d in decision.per_domain}
    entries.append(AuditEntry(key="per_domain_decision", value=per_domain))

    scores = {d.value: {"score": c.score, "level": c.level.value} for d, c in classifications.items()}
    entries.append(AuditEntry(key="domain_scores", value=scores))

    if severity_overrides:
        entries.append(
            AuditEntry(
                key="severity_overrides",
                value=[
                    {
                        "domain": o.domain.value,
                        "indicator_id": o.indicator_id,
                        "impact": o.impact,
                        "likelihood": o.likelihood,
                        "from_level": o.from_level.value,
                        "to_level": o.to_level.value,
                        "reason": o.reason,
                    }
                    for o in severity_overrides
                ],
            )
        )

    # --- Initial vs residual, controls, traceability, sensitivity ---------
    if initial_summary is not None:
        entries.append(AuditEntry(key="initial", value=initial_summary))
    if residual_summary is not None:
        entries.append(AuditEntry(key="residual", value=residual_summary))
    if controls is not None:
        entries.append(AuditEntry(key="controls", value=controls))
    if control_issues:
        entries.append(AuditEntry(key="control_issues", value=control_issues))
    if traceability is not None:
        entries.append(AuditEntry(key="traceability", value=traceability))
    if sensitivity is not None:
        entries.append(AuditEntry(key="sensitivity", value=sensitivity))

    entries.append(AuditEntry(key="indicator_details", value=indicator_details))
    entries.append(AuditEntry(key="local_scores", value=local_scores))

    return entries
