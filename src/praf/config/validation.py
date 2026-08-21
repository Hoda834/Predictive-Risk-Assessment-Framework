"""Input and configuration validation.

The scoring engine is deliberately tolerant so a partially-filled questionnaire
still produces a result, but *silent* tolerance is an integrity problem for an
auditable tool: a blank or malformed input must never masquerade as a complete
assessment. This module makes the tolerance **explicit** by producing a
structured report of everything that was missing, unknown, or out of range, so
the caller can surface it (and an auditor can see it) instead of it being hidden
behind a neutral default.

It also validates configuration (acceptability thresholds and weights) up front,
turning silently-inverted or nonsensical settings into a clear error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping


# Axes that make up a single indicator assessment.
_AXES = ("response", "likelihood", "impact", "detectability")

# Numeric axes are read on a 1..5 scale.
_SCALE_MIN = 1.0
_SCALE_MAX = 5.0


class ConfigValidationError(ValueError):
    """Raised when engine configuration (thresholds/weights) is invalid."""


@dataclass(frozen=True)
class InputValidationReport:
    """A structured account of the quality of an input payload.

    Nothing here stops scoring; it exists so incompleteness is *visible* rather
    than silently imputed to the neutral value.
    """

    total_indicators: int
    # indicator_id -> list of axes that were absent (and therefore defaulted).
    missing: Dict[str, List[str]] = field(default_factory=dict)
    # indicator ids present in the input that are not in the library.
    unknown_indicator_ids: List[str] = field(default_factory=list)
    # indicator_id -> list of axes whose numeric value fell outside 1..5 and
    # was clamped.
    out_of_range: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        """True only if every library indicator had all four axes supplied."""
        return not self.missing and not self.unknown_indicator_ids

    @property
    def indicators_fully_answered(self) -> int:
        return self.total_indicators - len(self.missing)

    @property
    def completeness_ratio(self) -> float:
        if self.total_indicators <= 0:
            return 0.0
        return self.indicators_fully_answered / self.total_indicators

    def as_dict(self) -> Dict[str, Any]:
        return {
            "complete": self.complete,
            "completeness_ratio": round(self.completeness_ratio, 4),
            "indicators_fully_answered": self.indicators_fully_answered,
            "total_indicators": self.total_indicators,
            "missing": self.missing,
            "unknown_indicator_ids": self.unknown_indicator_ids,
            "out_of_range": self.out_of_range,
        }


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value.strip())
            return True
        except ValueError:
            return False
    return False


def _numeric_out_of_range(value: Any) -> bool:
    if not _is_number(value):
        return False
    x = float(value.strip()) if isinstance(value, str) else float(value)
    return x < _SCALE_MIN or x > _SCALE_MAX


def validate_inputs(
    library_ids: List[str],
    responses: Mapping[str, Any],
    likelihood: Mapping[str, Any],
    impact: Mapping[str, Any],
    detectability: Mapping[str, Any],
) -> InputValidationReport:
    """Compare an input payload against the indicator library.

    Reports, per indicator, which of the four axes were missing; which numeric
    values were out of the 1..5 range (and so will be clamped); and any
    indicator ids supplied that the library does not recognise.
    """
    axis_maps = {
        "response": responses,
        "likelihood": likelihood,
        "impact": impact,
        "detectability": detectability,
    }

    missing: Dict[str, List[str]] = {}
    out_of_range: Dict[str, List[str]] = {}

    for indicator_id in library_ids:
        absent = [axis for axis in _AXES if axis_maps[axis].get(indicator_id) is None]
        if absent:
            missing[indicator_id] = absent

        oor = [
            axis
            for axis in _AXES
            if _numeric_out_of_range(axis_maps[axis].get(indicator_id))
        ]
        if oor:
            out_of_range[indicator_id] = oor

    library_set = set(library_ids)
    supplied = set().union(*(set(m.keys()) for m in axis_maps.values()))
    unknown = sorted(supplied - library_set)

    return InputValidationReport(
        total_indicators=len(library_ids),
        missing=missing,
        unknown_indicator_ids=unknown,
        out_of_range=out_of_range,
    )


def validate_thresholds(low_threshold: float, high_threshold: float) -> None:
    """Ensure the acceptability bands are well-formed.

    A silently inverted pair (low >= high) would flip the entire classification
    without any error, so it is rejected up front.
    """
    low = float(low_threshold)
    high = float(high_threshold)
    if not (0.0 <= low < high <= 100.0):
        raise ConfigValidationError(
            "Invalid thresholds: require 0 <= low < high <= 100, "
            f"got low={low}, high={high}."
        )


def validate_domain_weights(domain_weights: Mapping[Any, float]) -> None:
    """Reject negative domain weights (which would invert a domain's risk)."""
    for domain, weight in domain_weights.items():
        w = float(weight)
        if w < 0.0:
            raise ConfigValidationError(
                f"Domain weight for {domain!r} must be non-negative, got {w}."
            )
