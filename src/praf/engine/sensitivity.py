"""One-at-a-time sensitivity (uncertainty) analysis of the classification.

Indicator inputs are expert judgements on coarse 1–5 scales, so every value
carries at least ±1 of honest uncertainty. A classification that changes when a
single input moves by one step is not a robust basis for a gate decision — the
reviewer should know that before acting on it.

This module perturbs each effective likelihood / impact / detectability value by
±1 (clamped to the 1–5 scale), re-runs the full classification for each
perturbation, and reports every domain-band or overall-decision flip. The output
distinguishes *fragile* domains (flip under some single ±1 change) from stable
ones. The analysis is one-at-a-time by design: it is cheap (≤ 6 runs per
indicator), and each reported flip names the exact input that causes it, which
is what makes it actionable.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

# classify_fn(likelihood, impact, detectability) ->
#     (domain_levels: Dict[str, str], overall_decision: str)
ClassifyFn = Callable[
    [Dict[str, Any], Dict[str, Any], Dict[str, Any]],
    Tuple[Dict[str, str], str],
]

_AXES = ("likelihood", "impact", "detectability")


def _effective(value: Any) -> float:
    """The value the scorer will actually use (missing -> neutral 3)."""
    if value is None:
        return 3.0
    try:
        x = float(value)
    except (TypeError, ValueError):
        return 3.0
    return max(1.0, min(5.0, x))


def sensitivity_analysis(
    classify_fn: ClassifyFn,
    likelihood: Dict[str, Any],
    impact: Dict[str, Any],
    detectability: Dict[str, Any],
    indicator_ids: List[str],
) -> Dict[str, Any]:
    baseline_domains, baseline_overall = classify_fn(likelihood, impact, detectability)

    axis_maps = {
        "likelihood": dict(likelihood),
        "impact": dict(impact),
        "detectability": dict(detectability),
    }

    flips: List[Dict[str, Any]] = []
    overall_flips: List[Dict[str, Any]] = []

    for iid in indicator_ids:
        for axis in _AXES:
            current = _effective(axis_maps[axis].get(iid))
            for delta in (-1.0, 1.0):
                perturbed_value = max(1.0, min(5.0, current + delta))
                if perturbed_value == current:
                    continue  # already at the scale boundary

                perturbed = {a: dict(m) for a, m in axis_maps.items()}
                perturbed[axis][iid] = perturbed_value

                domains, overall = classify_fn(
                    perturbed["likelihood"],
                    perturbed["impact"],
                    perturbed["detectability"],
                )

                for domain, level in domains.items():
                    if baseline_domains.get(domain) != level:
                        flips.append(
                            {
                                "indicator_id": iid,
                                "axis": axis,
                                "delta": delta,
                                "domain": domain,
                                "from_level": baseline_domains.get(domain),
                                "to_level": level,
                            }
                        )
                if overall != baseline_overall:
                    overall_flips.append(
                        {
                            "indicator_id": iid,
                            "axis": axis,
                            "delta": delta,
                            "from_decision": baseline_overall,
                            "to_decision": overall,
                        }
                    )

    fragile = sorted({f["domain"] for f in flips})

    return {
        "method": "one-at-a-time ±1 perturbation of each effective likelihood/impact/detectability value (clamped to 1–5)",
        "baseline_domain_levels": baseline_domains,
        "baseline_overall_decision": baseline_overall,
        "domain_flips": flips,
        "overall_decision_flips": overall_flips,
        "fragile_domains": fragile,
        "stable": not flips and not overall_flips,
    }
