from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict


class InputLoadError(Exception):
    """Raised when an input file cannot be read or is structurally invalid.

    Carries a human-readable message so the CLI can report a clear error instead
    of leaking a raw traceback.
    """


@dataclass(frozen=True)
class LoadedInputs:
    responses: Dict[str, Any]
    likelihood: Dict[str, Any]
    impact: Dict[str, Any]
    detectability: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    # Raw entries of the optional "controls" section; parsed/validated against
    # the indicator library later by praf.domain.controls.parse_controls.
    controls: list = field(default_factory=list)


def _as_dict(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = payload.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InputLoadError(
            f"Field '{key}' must be an object mapping indicator ids to values, "
            f"got {type(value).__name__}."
        )
    return dict(value)


def load_json_inputs(path: str) -> LoadedInputs:
    """Load and structurally validate a JSON input file.

    Raises :class:`InputLoadError` (not a raw ``FileNotFoundError`` /
    ``JSONDecodeError``) for a missing file, malformed JSON, or a payload whose
    top-level shape is wrong, so callers get an actionable message.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError as exc:
        raise InputLoadError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InputLoadError(f"Input file is not valid JSON ({path}): {exc}") from exc
    except OSError as exc:
        raise InputLoadError(f"Could not read input file {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise InputLoadError(
            f"Top-level JSON must be an object, got {type(payload).__name__}."
        )

    context = payload.get("context", {})
    if context is None:
        context = {}
    if not isinstance(context, dict):
        raise InputLoadError(
            f"Field 'context' must be an object, got {type(context).__name__}."
        )

    controls = payload.get("controls", [])
    if controls is None:
        controls = []
    if not isinstance(controls, list):
        raise InputLoadError(
            f"Field 'controls' must be a list, got {type(controls).__name__}."
        )

    return LoadedInputs(
        responses=_as_dict(payload, "responses"),
        likelihood=_as_dict(payload, "likelihood"),
        impact=_as_dict(payload, "impact"),
        detectability=_as_dict(payload, "detectability"),
        context=dict(context),
        controls=list(controls),
    )
