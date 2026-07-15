from __future__ import annotations

from typing import Any, Dict, List, Tuple

from praf.domain import INDICATOR_LIBRARY
from praf.domain.activities import Activity, ProjectStage
from praf.config.schemas import AllowedAnswerType


class InputValidationError(ValueError):
    """Raised when supplied input is structurally invalid.

    Carries the full list of problems so the caller can report all of them at
    once rather than failing on the first.
    """

    def __init__(self, errors: List[str]) -> None:
        self.errors = list(errors)
        message = "Input validation failed:\n" + "\n".join(f"  - {e}" for e in self.errors)
        super().__init__(message)


def _is_number_in_range(value: Any, lo: float, hi: float) -> bool:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return False
    return lo <= x <= hi


def _response_valid(answer_type: AllowedAnswerType, value: Any) -> bool:
    if answer_type == AllowedAnswerType.YES_NO:
        if isinstance(value, bool):
            return True
        return str(value).strip().lower() in {"yes", "y", "true", "1", "no", "n", "false", "0"}
    if answer_type == AllowedAnswerType.LOW_MED_HIGH:
        if str(value).strip().lower() in {"low", "l", "medium", "med", "m", "high", "h"}:
            return True
        return _is_number_in_range(value, 1, 5)
    if answer_type == AllowedAnswerType.SCALE_1_5:
        return _is_number_in_range(value, 1, 5)
    return False


def validate_context(activity: str, stage: str) -> Tuple[Activity, ProjectStage]:
    """Resolve activity/stage strings, raising a clear error for bad values."""
    errors: List[str] = []
    act: Activity = None  # type: ignore[assignment]
    stg: ProjectStage = None  # type: ignore[assignment]

    try:
        act = Activity(activity)
    except ValueError:
        errors.append(
            f"unknown activity {activity!r}; valid: {', '.join(a.value for a in Activity)}"
        )
    try:
        stg = ProjectStage(stage)
    except ValueError:
        errors.append(
            f"unknown stage {stage!r}; valid: {', '.join(s.value for s in ProjectStage)}"
        )

    if errors:
        raise InputValidationError(errors)
    return act, stg


def validate_inputs(
    responses: Dict[str, Any],
    likelihood: Dict[str, Any],
    impact: Dict[str, Any],
    detectability: Dict[str, Any],
) -> None:
    """Reject unknown indicator ids and out-of-range / malformed values.

    Missing answers are *not* an error here -- an unanswered indicator is
    handled as reduced coverage downstream. This only rejects values that were
    actually supplied but cannot be interpreted, so bad input fails loudly
    instead of being silently coerced to a neutral score.
    """
    errors: List[str] = []
    valid_ids = set(INDICATOR_LIBRARY.keys())

    named_maps = (
        ("responses", responses),
        ("likelihood", likelihood),
        ("impact", impact),
        ("detectability", detectability),
    )

    for field, mapping in named_maps:
        for key in mapping:
            if key not in valid_ids:
                errors.append(f"{field}: unknown indicator id {key!r}")

    for field, mapping in (("likelihood", likelihood), ("impact", impact), ("detectability", detectability)):
        for key, value in mapping.items():
            if key not in valid_ids:
                continue
            if not _is_number_in_range(value, 1, 5):
                errors.append(f"{field}[{key!r}]: {value!r} is not a number in 1..5")

    for key, value in responses.items():
        if key not in valid_ids:
            continue
        indicator = INDICATOR_LIBRARY[key]
        if not _response_valid(indicator.answer_type, value):
            errors.append(
                f"responses[{key!r}]: {value!r} is not valid for answer type "
                f"{indicator.answer_type.value}"
            )

    if errors:
        raise InputValidationError(errors)
