from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LoadedInputs:
    responses: Dict[str, Any]
    likelihood: Dict[str, Any]
    impact: Dict[str, Any]
    detectability: Dict[str, Any]


def load_json_inputs(path: str) -> LoadedInputs:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    return LoadedInputs(
        responses=dict(payload.get("responses", {})),
        likelihood=dict(payload.get("likelihood", {})),
        impact=dict(payload.get("impact", {})),
        detectability=dict(payload.get("detectability", {})),
    )
