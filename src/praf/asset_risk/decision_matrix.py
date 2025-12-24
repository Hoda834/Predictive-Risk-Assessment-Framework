import json
from typing import Dict, List


def load_decision_matrix(path: str) -> Dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def covered_controls_from_risks(risks) -> List[str]:
    covered = set()
    for r in risks:
        for c in getattr(r, "selected_controls", []) or []:
            covered.add(str(c))
    return sorted(list(covered))


def missing_required_controls(required_controls: List[str], covered_controls: List[str]) -> List[str]:
    req = [str(x) for x in (required_controls or [])]
    cov = set(str(x) for x in (covered_controls or []))
    return [c for c in req if c not in cov]
