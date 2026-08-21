"""Residual-risk computation: re-score indicators after risk controls.

Takes the *initial* per-indicator details produced by the scorer, applies the
numeric effect of every applicable control (see ``praf.domain.controls``), and
recomputes severity, contributions, and — via the ordinary aggregator/classifier
path — the residual domain indices. The same formulas as the initial pass are
reused deliberately, so initial and residual figures are always comparable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from praf.domain.controls import Control


@dataclass(frozen=True)
class ResidualResult:
    # Same shape as the scorer's outputs, so aggregate_scores() accepts them.
    indicator_details: Dict[str, Dict[str, Any]]
    local_scores: Dict[str, float]
    # indicator_id -> control ids whose effect was applied to it.
    applied_controls: Dict[str, List[str]] = field(default_factory=dict)
    # Controls carried in the input but not applied (planned), for the report.
    not_applied: List[str] = field(default_factory=list)
    # Applied controls whose status is implemented-but-not-verified.
    unverified_applied: List[str] = field(default_factory=list)


def apply_controls(
    indicator_details: Dict[str, Dict[str, Any]],
    controls: List[Control],
) -> ResidualResult:
    """Produce residual indicator details by applying control effects.

    Reductions from multiple controls on the same indicator accumulate, and each
    axis is floored at 1.0 (the best possible value on the 1–5 scale). Impact
    and the response axis are never modified — see praf.domain.controls for the
    rationale. Indicators without applicable controls pass through unchanged, so
    with an empty control list residual == initial by construction.
    """
    # Sum up per-indicator reductions from applicable controls.
    l_red: Dict[str, int] = {}
    d_red: Dict[str, int] = {}
    applied: Dict[str, List[str]] = {}
    not_applied: List[str] = []
    unverified: List[str] = []

    for control in controls:
        if not control.applies:
            not_applied.append(control.control_id)
            continue
        touched = False
        for iid in control.indicator_ids:
            if iid not in indicator_details:
                continue
            l_red[iid] = l_red.get(iid, 0) + control.likelihood_reduction
            d_red[iid] = d_red.get(iid, 0) + control.detectability_reduction
            applied.setdefault(iid, []).append(control.control_id)
            touched = True
        if touched and control.status.value == "implemented":
            unverified.append(control.control_id)

    residual_details: Dict[str, Dict[str, Any]] = {}
    residual_scores: Dict[str, float] = {}

    for iid, meta in indicator_details.items():
        scaled = meta["scaled"]
        r_scale = float(scaled["response"])
        i_scale = float(scaled["impact"])
        l_scale = max(1.0, float(scaled["likelihood"]) - l_red.get(iid, 0))
        d_scale = max(1.0, float(scaled["detectability"]) - d_red.get(iid, 0))

        # Identical formulas to the initial pass (see scorer.py) so the two
        # figures are directly comparable.
        base = (r_scale + l_scale + i_scale + d_scale) / 4.0
        severity = (base - 1.0) / 4.0
        contribution = severity * float(meta["weight_ex_domain"])

        residual_meta = dict(meta)
        residual_meta["scaled"] = {
            "response": r_scale,
            "likelihood": l_scale,
            "impact": i_scale,
            "detectability": d_scale,
        }
        residual_meta["base"] = base
        residual_meta["severity"] = severity
        residual_meta["controls_applied"] = list(applied.get(iid, []))

        residual_details[iid] = residual_meta
        residual_scores[iid] = float(contribution)

    return ResidualResult(
        indicator_details=residual_details,
        local_scores=residual_scores,
        applied_controls=applied,
        not_applied=not_applied,
        unverified_applied=unverified,
    )
