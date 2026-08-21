"""End-to-end orchestration of the indicator-based assessment.

Centralises the full flow so the CLI and any embedding share one code path:

    score (initial) -> aggregate -> classify -> severity guard      # initial risk
    apply controls  -> aggregate -> classify -> severity guard      # residual risk
    decide (on residual) -> traceability -> sensitivity -> audit trail

The *initial* figures describe risk before risk-control measures; the
*residual* figures describe risk after the applicable controls. The gate
decision is taken on residual risk (with no controls supplied, residual equals
initial by construction). Traceability links every indicator to the controls
applied to it and the resulting level change, and the sensitivity block reports
which classifications flip under a single ±1 input change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from praf.domain import INDICATOR_LIBRARY, Context
from praf.domain.controls import Control
from praf.domain.domains import RiskDomain, activity_domain_weights
from praf.config.defaults import Defaults
from praf.config.validation import validate_inputs, validate_domain_weights, InputValidationReport
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains
from praf.engine.severity_guard import apply_severity_guard, SeverityGuardResult
from praf.engine.residual import apply_controls, ResidualResult
from praf.engine.sensitivity import sensitivity_analysis
from praf.engine.rules import decide
from praf.engine.explainability import explain
from praf.engine.audit_trail import build_audit_trail


@dataclass(frozen=True)
class AssessmentResult:
    report: Dict[str, Any]
    validation: InputValidationReport
    severity_guard: SeverityGuardResult  # guard result on the residual pass
    residual: ResidualResult


def _stage(details: Dict[str, Any], scores: Dict[str, float], defaults: Defaults):
    """Aggregate, classify, and severity-guard one set of indicator details."""
    aggregated = aggregate_scores(details, scores)
    classifications = classify_domains(
        aggregated.domain_scores, defaults.low_threshold, defaults.high_threshold
    )
    guard = apply_severity_guard(classifications, details)
    return aggregated, guard


def _decision_block(classifications, decision) -> Dict[str, Any]:
    return {
        "overall_decision": decision.overall.value,
        "per_domain_decision": {d.value: decision.per_domain[d].value for d in decision.per_domain},
        "domain_scores": {
            d.value: {"score": classifications[d].score, "level": classifications[d].level.value}
            for d in classifications
        },
    }


def _overrides_block(guard: SeverityGuardResult) -> List[Dict[str, Any]]:
    return [
        {
            "domain": o.domain.value,
            "indicator_id": o.indicator_id,
            "from_level": o.from_level.value,
            "to_level": o.to_level.value,
            "reason": o.reason,
        }
        for o in guard.overrides
    ]


def run_assessment(
    responses: Dict[str, Any],
    likelihood: Dict[str, Any],
    impact: Dict[str, Any],
    detectability: Dict[str, Any],
    context: Context,
    defaults: Optional[Defaults] = None,
    *,
    controls: Optional[List[Control]] = None,
    control_issues: Optional[List[str]] = None,
    include_sensitivity: bool = True,
    top_n: int = 5,
    generated_at: Optional[str] = None,
) -> AssessmentResult:
    defaults = defaults or Defaults()
    controls = controls or []

    validation = validate_inputs(
        list(INDICATOR_LIBRARY.keys()), responses, likelihood, impact, detectability
    )

    domain_weights = activity_domain_weights(context.activity)
    validate_domain_weights(domain_weights)

    # ------ Initial risk (before controls) --------------------------------
    scored = score_indicators(
        responses=responses,
        likelihood=likelihood,
        impact=impact,
        detectability=detectability,
        domain_weights=domain_weights,
    )
    _, initial_guard = _stage(scored.indicator_details, scored.local_scores, defaults)
    initial_classifications = initial_guard.classifications
    initial_decision = decide(initial_classifications)

    # ------ Residual risk (after applicable controls) ---------------------
    residual = apply_controls(scored.indicator_details, controls)
    _, residual_guard = _stage(residual.indicator_details, residual.local_scores, defaults)
    residual_classifications = residual_guard.classifications
    residual_decision = decide(residual_classifications)

    expl = explain(
        residual_classifications, residual.indicator_details, residual.local_scores, top_n=top_n
    )

    # ------ Traceability: hazard -> controls -> residual decision ---------
    traceability: List[Dict[str, Any]] = []
    for iid, meta in scored.indicator_details.items():
        res_meta = residual.indicator_details[iid]
        domain = RiskDomain(meta["domain"])
        traceability.append(
            {
                "indicator_id": iid,
                "question": INDICATOR_LIBRARY[iid].question,
                "domain": meta["domain"],
                "initial_severity": meta["severity"],
                "controls_applied": res_meta.get("controls_applied", []),
                "residual_severity": res_meta["severity"],
                "domain_initial_level": initial_classifications[domain].level.value,
                "domain_residual_level": residual_classifications[domain].level.value,
                "residual_decision": residual_decision.per_domain[domain].value,
            }
        )

    # ------ Sensitivity: does a single ±1 change flip anything? -----------
    sensitivity: Optional[Dict[str, Any]] = None
    if include_sensitivity:

        def _classify_for(l_map, i_map, d_map) -> Tuple[Dict[str, str], str]:
            s = score_indicators(responses, l_map, i_map, d_map, domain_weights)
            r = apply_controls(s.indicator_details, controls)
            _, g = _stage(r.indicator_details, r.local_scores, defaults)
            dec = decide(g.classifications)
            return (
                {d.value: c.level.value for d, c in g.classifications.items()},
                dec.overall.value,
            )

        sensitivity = sensitivity_analysis(
            _classify_for, likelihood, impact, detectability, list(INDICATOR_LIBRARY.keys())
        )

    # ------ Report + audit trail ------------------------------------------
    ctx_dict = {"activity": context.activity.value, "stage": context.stage.value}
    thresholds = {"low": defaults.low_threshold, "high": defaults.high_threshold}

    initial_block = _decision_block(initial_classifications, initial_decision)
    initial_block["severity_overrides"] = _overrides_block(initial_guard)

    residual_block = _decision_block(residual_classifications, residual_decision)
    residual_block["severity_overrides"] = _overrides_block(residual_guard)
    residual_block["controls_applied"] = residual.applied_controls
    residual_block["controls_not_applied"] = residual.not_applied
    residual_block["controls_unverified"] = residual.unverified_applied

    controls_summary = [
        {
            "control_id": c.control_id,
            "name": c.name,
            "status": c.status.value,
            "indicator_ids": list(c.indicator_ids),
            "likelihood_reduction": c.likelihood_reduction,
            "detectability_reduction": c.detectability_reduction,
            "applied": c.applies,
        }
        for c in controls
    ]

    audit = build_audit_trail(
        residual_classifications,
        residual_decision,
        scored.indicator_details,
        scored.local_scores,
        context=ctx_dict,
        thresholds=thresholds,
        input_completeness=validation.as_dict(),
        severity_overrides=residual_guard.overrides,
        generated_at=generated_at,
        initial_summary=initial_block,
        residual_summary=residual_block,
        controls=controls_summary,
        control_issues=list(control_issues or []),
        traceability=traceability,
        sensitivity=sensitivity,
    )

    report: Dict[str, Any] = {
        "context": ctx_dict,
        "input_completeness": validation.as_dict(),
        # Top-level decision figures are the FINAL (residual) ones; with no
        # controls supplied they equal the initial figures by construction.
        "overall_decision": residual_decision.overall.value,
        "per_domain_decision": residual_block["per_domain_decision"],
        "domain_scores": residual_block["domain_scores"],
        "severity_overrides": residual_block["severity_overrides"],
        "initial": initial_block,
        "residual": residual_block,
        "controls": controls_summary,
        "control_issues": list(control_issues or []),
        "traceability": traceability,
        "sensitivity": sensitivity,
        "top_contributors_by_domain": {
            d.value: expl.top_contributors_by_domain.get(d, []) for d in residual_classifications
        },
        "audit_trail": [{"key": a.key, "value": a.value} for a in audit],
    }

    return AssessmentResult(
        report=report,
        validation=validation,
        severity_guard=residual_guard,
        residual=residual,
    )
