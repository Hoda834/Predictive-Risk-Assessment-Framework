from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from praf.domain import INDICATOR_LIBRARY
from praf.domain.natures import nature_weight_modifier
from praf.domain.domains import RiskDomain
from praf.domain.indicators import Polarity


@dataclass(frozen=True)
class ScoreResult:
    local_scores: Dict[str, float]
    indicator_details: Dict[str, Dict[str, Any]]


def _map_yes_no(answer: Any) -> float:
    """Map a yes/no answer to the affirmative axis (yes = 5, no = 1).

    This is the *raw* answer scale, where a higher value simply means a more
    affirmative answer. Whether "yes" raises or lowers risk is decided later by
    the indicator's polarity (see ``score_indicators``), not here.
    """
    if isinstance(answer, str):
        v = answer.strip().lower()
        if v in {"yes", "y", "true", "1"}:
            return 5.0
        if v in {"no", "n", "false", "0"}:
            return 1.0
        return 3.0
    if isinstance(answer, bool):
        return 5.0 if answer else 1.0
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

        # An indicator counts as answered only if the user supplied a response;
        # a missing response falls back to a neutral score, which must not be
        # mistaken for a real "medium" signal (see coverage in the aggregator).
        answered = isinstance(r, str) and r.strip() != "" if isinstance(r, str) else r is not None

        r_raw = _response_scale(indicator.answer_type.value, r)
        # Apply polarity: for protective controls (risk when the control is
        # ABSENT) an affirmative answer lowers risk, so invert the raw axis
        # (5 <-> 1, 3 stays 3). Hazard-level indicators (risk when PRESENT) use
        # the raw axis directly.
        if indicator.polarity == Polarity.RISK_WHEN_ABSENT:
            r_scale = 6.0 - r_raw
        else:
            r_scale = r_raw

        # Likelihood, impact and detectability are always "higher = worse".
        # Detectability follows the FMEA convention: a higher value means the
        # problem is HARDER to detect, which increases risk.
        l_scale = _map_scale_1_5(l)
        i_scale = _map_scale_1_5(i)
        d_scale = _map_scale_1_5(d)

        # Composite severity on the 1..5 scale, then normalised to 0..1 so it is
        # independent of the weighting magnitudes below.
        base = (r_scale + l_scale + i_scale + d_scale) / 4.0
        severity = (base - 1.0) / 4.0

        dw = float(domain_weights.get(indicator.domain, 1.0))
        nw = float(nature_weight_modifier(indicator.nature))
        iw = float(indicator.base_weight)

        # The domain weight (dw) is constant across every indicator in a domain,
        # so it would cancel out of the weight-normalised mean below and have no
        # effect. It is therefore applied *after* normalisation in the
        # aggregator (as a sensitivity multiplier), and kept out of the
        # per-indicator contribution weight here.
        weight_ex_domain = nw * iw

        # Weighted contribution of this indicator to its domain's mean severity.
        # nw and iw vary within a domain, so they genuinely shape the ranking
        # and the aggregate; dw does not and is excluded.
        contribution = severity * weight_ex_domain

        local_scores[indicator_id] = float(contribution)
        details[indicator_id] = {
            "domain": indicator.domain.value,
            "category": indicator.category.value,
            "nature": indicator.nature.value,
            "polarity": indicator.polarity.value,
            "answered": bool(answered),
            "weights": {"domain": dw, "nature": nw, "indicator": iw},
            "domain_weight": dw,
            "weight_ex_domain": weight_ex_domain,
            "inputs": {"response": r, "likelihood": l, "impact": i, "detectability": d},
            "scaled": {"response": r_scale, "likelihood": l_scale, "impact": i_scale, "detectability": d_scale},
            "base": base,
            "severity": severity,
        }

    return ScoreResult(local_scores=local_scores, indicator_details=details)
