from typing import Dict, List
from praf.asset_risk.decision_matrix import covered_controls_from_risks, missing_required_controls


def count_high_residual_risks(risks, threshold: int = 4) -> int:
    return sum(1 for r in risks if int(r.residual_score) >= threshold)


def evaluate_readiness(decision_matrix: Dict, risks: List) -> Dict:
    required_controls = decision_matrix.get("required_controls", [])
    optional_controls = decision_matrix.get("optional_controls", [])
    rules = decision_matrix.get("readiness_rules", {})

    covered_controls = covered_controls_from_risks(risks)
    missing_required = missing_required_controls(required_controls, covered_controls)

    high_residual_count = count_high_residual_risks(risks)

    readiness = "ready"
    reasons = []

    if rules.get("not_ready_if_missing_any_required_control", False):
        if missing_required:
            readiness = "not_ready"
            reasons.append("Missing required controls")

    max_high = rules.get("max_allowed_high_residual_risks")
    if max_high is not None and high_residual_count > int(max_high):
        readiness = "not_ready"
        reasons.append("High residual risks remain")

    if readiness == "ready" and (missing_required or high_residual_count > 0):
        readiness = "conditionally_ready"

    return {
        "readiness": readiness,
        "covered_controls": covered_controls,
        "missing_required_controls": missing_required,
        "optional_controls": optional_controls,
        "high_residual_risk_count": high_residual_count,
        "reasons": reasons,
    }
