import json
from typing import Dict, List


def load_decision_matrix(path: str) -> Dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def covered_controls_from_risks(risks) -> List[str]:
    covered = set()
    for r in risks:
        for c in r.selected_controls:
            covered.add(c)
    return sorted(list(covered))


def missing_required_controls(required_controls: List[str], covered_controls: List[str]) -> List[str]:
    return [c for c in required_controls if c not in covered_controls]
