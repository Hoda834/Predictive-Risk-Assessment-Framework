from typing import Dict, List
from .decision_matrix import covered_controls_from_risks, missing_required_controls


def evaluate_readiness(decision_matrix: Dict, risks: List) -> Dict:
    required_controls = decision_matrix.get("required_controls", [])
    readiness_rules = decision_matrix.get("readiness_rules", {})

    covered_controls = covered_controls_from_risks(risks)
    missing_controls = missing_required_controls(required_controls, covered_controls)

    not_ready = False
    reasons = []

    if readiness_rules.get("not_ready_if_missing_any_required_control", False):
        if missing_controls:
            not_ready = True
            reasons.append("Missing required controls")

    if readiness_rules.get("max_allowed_high_residual_risks", None) is not None:
        high_risks = [r for r in risks if getattr(r, "priority", "").lower() == "high"]
        if len(high_risks) > readiness_rules["max_allowed_high_residual_risks"]:
            not_ready = True
            reasons.append("Too many high residual risks")

    return {
        "ready": not not_ready,
        "missing_controls": missing_controls,
        "covered_controls": covered_controls,
        "reasons": reasons,
    }
