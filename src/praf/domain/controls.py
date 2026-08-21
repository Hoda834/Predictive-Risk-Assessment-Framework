"""Risk-control model: the bridge from initial to residual risk.

ISO 14971 distinguishes the risk *before* risk-control measures (initial risk)
from the risk *after* them (residual risk), and requires the link between a
hazard, the controls addressing it, and the residual acceptability decision to
be traceable. This module models that middle piece.

Effect model
------------
A control declares which indicators it addresses and how many *steps* it removes
from the scaled 1–5 likelihood and/or detectability axes of those indicators
(floored at 1, the best value). Impact is deliberately **not** reducible by a
control here: under ISO 14971 severity of harm is normally reduced only by
changing the design itself, which in this model means re-answering the
assessment, not annotating it with a control. This keeps residual-risk claims
conservative and auditable.

Only controls with status ``implemented`` or ``verified`` count toward residual
risk; ``planned`` controls are carried through the report as visible intent but
have no numeric effect. Unverified-but-implemented controls are flagged so a
reviewer can see how much of the residual case rests on unverified measures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple


class ControlStatus(str, Enum):
    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"


# Bounds for the per-axis reduction, in steps on the scaled 1..5 axis.
MAX_REDUCTION = 4


@dataclass(frozen=True)
class Control:
    control_id: str
    name: str
    indicator_ids: Tuple[str, ...]
    status: ControlStatus
    likelihood_reduction: int = 0
    detectability_reduction: int = 0
    description: str = ""
    evidence: str = ""

    @property
    def applies(self) -> bool:
        """Whether this control counts toward residual risk."""
        return self.status in (ControlStatus.IMPLEMENTED, ControlStatus.VERIFIED)


@dataclass(frozen=True)
class ControlParseResult:
    controls: List[Control]
    # Human-readable problems found while parsing (control skipped or partially
    # ignored). Structural garbage raises instead — see parse_controls.
    issues: List[str] = field(default_factory=list)


class ControlDefinitionError(ValueError):
    """Raised when the controls section is structurally invalid."""


def _int_in_range(value: Any, name: str, control_id: str) -> int:
    try:
        x = int(value)
    except (TypeError, ValueError):
        raise ControlDefinitionError(
            f"Control '{control_id}': {name} must be an integer, got {value!r}."
        )
    if not (0 <= x <= MAX_REDUCTION):
        raise ControlDefinitionError(
            f"Control '{control_id}': {name} must be in 0..{MAX_REDUCTION}, got {x}."
        )
    return x


def parse_controls(raw: Any, known_indicator_ids: List[str]) -> ControlParseResult:
    """Parse the ``controls`` section of an input payload.

    Structural problems (not a list, entry not an object, missing id, bad
    status, out-of-range reduction) raise :class:`ControlDefinitionError` —
    a malformed control must never be silently dropped from a residual-risk
    claim. References to unknown indicator ids are softer: the reference is
    ignored but reported as an issue, mirroring how unknown indicator inputs
    are handled elsewhere.
    """
    if raw is None:
        return ControlParseResult(controls=[])
    if not isinstance(raw, list):
        raise ControlDefinitionError(
            f"'controls' must be a list of objects, got {type(raw).__name__}."
        )

    known = set(known_indicator_ids)
    controls: List[Control] = []
    issues: List[str] = []
    seen_ids: set = set()

    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ControlDefinitionError(
                f"controls[{i}] must be an object, got {type(entry).__name__}."
            )
        control_id = str(entry.get("control_id", "")).strip()
        if not control_id:
            raise ControlDefinitionError(f"controls[{i}] is missing 'control_id'.")
        if control_id in seen_ids:
            raise ControlDefinitionError(f"Duplicate control_id '{control_id}'.")
        seen_ids.add(control_id)

        status_raw = str(entry.get("status", "")).strip().lower()
        try:
            status = ControlStatus(status_raw)
        except ValueError:
            valid = ", ".join(s.value for s in ControlStatus)
            raise ControlDefinitionError(
                f"Control '{control_id}': unknown status '{status_raw}'. Valid: {valid}."
            )

        raw_targets = entry.get("indicator_ids", [])
        if not isinstance(raw_targets, list) or not raw_targets:
            raise ControlDefinitionError(
                f"Control '{control_id}': 'indicator_ids' must be a non-empty list."
            )
        targets: List[str] = []
        for t in raw_targets:
            t = str(t)
            if t in known:
                targets.append(t)
            else:
                issues.append(
                    f"Control '{control_id}' references unknown indicator '{t}'; reference ignored."
                )
        if not targets:
            issues.append(
                f"Control '{control_id}' has no valid indicator references and has no effect."
            )

        lr = _int_in_range(entry.get("likelihood_reduction", 0), "likelihood_reduction", control_id)
        dr = _int_in_range(entry.get("detectability_reduction", 0), "detectability_reduction", control_id)
        if lr == 0 and dr == 0:
            issues.append(
                f"Control '{control_id}' declares no reduction on any axis and has no numeric effect."
            )

        controls.append(
            Control(
                control_id=control_id,
                name=str(entry.get("name", control_id)),
                indicator_ids=tuple(targets),
                status=status,
                likelihood_reduction=lr,
                detectability_reduction=dr,
                description=str(entry.get("description", "")),
                evidence=str(entry.get("evidence", "")),
            )
        )

    return ControlParseResult(controls=controls, issues=issues)
