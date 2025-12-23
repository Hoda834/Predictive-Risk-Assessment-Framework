from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from praf.domain import INDICATOR_LIBRARY
from praf.domain.natures import nature_weight_modifier
from praf.domain.domains import RiskDomain


@dataclass(frozen=True)
class ScoreResult:
    local_scores: Dict[str, float]
    indicator_details: Dict[str, Dict[str, Any]]


def _map_yes_no(answer: Any) -> float:
    if isinstance(answer, str):
        v = answer.strip().lower()
        if v in {"yes", "y", "true", "1"}:
            return 1.0
        if v in {"no", "n", "false", "0"}:
            return 5.0
        return 3.0
    if isinstance(answer, bool):
        return 1.0 if answer else 5.0
    return 3.0


def _map_low_med_high(answer: Any) -> float:
    if isinstance(answer, str):
        v = answer.strip().lower()
        if v in {"low", "l"}:
            return 1.0
        if v in {"medium", "med", "m"}:
            return 3.0
        if v in {"high", "h"}:
            return 5.0
        return 3.0
    if isinstance(answer, (int, float)):
        x = float(answer)
        if x <= 1.67:
            return 1.0
        if x <= 3.34:
            return 3.0
        return 5.0
    return 3.0


def _map_scale_1_5(answer: Any) -> float:
    if isinstance(answer, (int, float)):
        x = float(answer)
        if x < 1.0:
            return 1.0
        if x > 5.0:
            return 5.0
        return x
    if isinstance(answer, str):
        try:
            x = float(answer.strip())
            if x < 1.0:
                return 1.0
            if x > 5.0:
                return 5.0
            return x
        except ValueError:
            return 3.0
    return 3.0


def _response_scale(answer_type: str, answer: Any) -> float:
    if answer_type == "yes_no":
        return _map_yes_no(answer)
    if answer_type == "low_med_high":
        return _map_low_med_high(answer)
    if answer_type == "scale_1_5":
        return _map_scale_1_5(answer)
    return 3.0


def score_indicators(
    responses: Dict[str, Any],
    likelihood: Dict[str, Any],
    impact: Dict[str, Any],
    detectability: Dict[str, Any],
    domain_weights: Dict[RiskDomain, float],
) -> ScoreResult:
    local_scores: Dict[str, float] = {}
    details: Dict[str, Dict[str, Any]] = {}

    for indicator_id, indicator in INDICATOR_LIBRARY.items():
        r = responses.get(indicator_id, None)
        l = likelihood.get(indicator_id, 3)
        i = impact.get(indicator_id, 3)
        d = detectability.get(indicator_id, 3)

        r_scale = _response_scale(indicator.answer_type.value, r)
        l_scale = _map_scale_1_5(l)
        i_scale = _map_scale_1_5(i)
        d_scale = _map_scale_1_5(d)

        base = (r_scale + l_scale + i_scale + d_scale) / 4.0

        dw = float(domain_weights.get(indicator.domain, 1.0))
        nw = float(nature_weight_modifier(indicator.nature))
        iw = float(indicator.base_weight)

        score = base * dw * nw * iw

        local_scores[indicator_id] = float(score)
        details[indicator_id] = {
            "domain": indicator.domain.value,
            "category": indicator.category.value,
            "nature": indicator.nature.value,
            "weights": {"domain": dw, "nature": nw, "indicator": iw},
            "inputs": {"response": r, "likelihood": l, "impact": i, "detectability": d},
            "scaled": {"response": r_scale, "likelihood": l_scale, "impact": i_scale, "detectability": d_scale},
            "base": base,
        }

    return ScoreResult(local_scores=local_scores, indicator_details=details)
