from typing import List, Dict


def build_risk_control_matrix(risks: List, control_mapping: Dict) -> Dict:
    matrix = {}

    for risk in risks:
        risk_id = risk.risk_id
        matrix[risk_id] = {
            "description": risk.description,
            "owner": risk.owner,
            "pattern": risk.pattern.value,
            "controls": {},
        }

        mapped_controls = control_mapping.get(risk.pattern.value, [])

        for control in mapped_controls:
            matrix[risk_id]["controls"][control] = {
                "covered": True,
                "evidence_expected": None,
            }

    return matrix
