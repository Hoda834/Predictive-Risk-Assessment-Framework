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


def _map_answer_to_scale(answer_type: str, answer: Any) -> float:
    if answer_type == "yes_no":
        if isinstance(answer, str):
            v = answer.strip().lower()
            if v in {"yes", "y", "true", "1"}:
                return 1.0
            if v in {"no", "n", "false", "0"}:
                return 5.0
        if isinstance(answer, bool):
            return 1.0 if answer else 5.0
        if isinstance(answer, (int, float)):
            return 1.0 if float(answer) >= 1.0 else 5.0
        return 3.0

    if answer_type == "low_med_high":
        if isinstance(answer, str):
            v = answer.strip().lower()
            if v in {"low", "l"}:
                return 1.0
            if v in {"medium", "med", "m"}:
                return 3.0
            if v in {"high", "h"}:
                return 5.0
        if isinstance(answer, (int, float)):
            x = float(answer)
            if x <= 1.67:
                return 1.0
            if x <= 3.34:
                return 3.0
            return 5.0
        return 3.0

    if answer_type == "scale_1_5":
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
        l = likelihood.get(indicator_id, None)
        i = impact.get(indicator_id, None)
        d = detectability.get(indicator_id, None)

        response_scale = _map_answer_to_scale(indicator.answer_type.value, r)
        l_scale = _map_answer_to_scale("scale_1_5", l)
        i_scale = _map_answer_to_scale("scale_1_5", i)
        d_scale = _map_answer_to_scale("scale_1_5", d)

        dw = float(domain_weights.get(indicator.domain, 1.0))
        nw = float(nature_weight_modifier(indicator.nature))
        iw = float(indicator.base_weight)

        score = response_scale * l_scale * i_scale * d_scale * dw * nw * iw

        local_scores[indicator_id] = float(score)
        details[indicator_id] = {
            "domain": indicator.domain.value,
            "category": indicator.category.value,
            "nature": indicator.nature.value,
            "weights": {"domain": dw, "nature": nw, "indicator": iw},
            "inputs": {"response": r, "likelihood": l, "impact": i, "detectability": d},
            "scaled": {"response": response_scale, "likelihood": l_scale, "impact": i_scale, "detectability": d_scale},
        }

    return ScoreResult(local_scores=local_scores, indicator_details=details)
