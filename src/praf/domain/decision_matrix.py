from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class DecisionScenario(str, Enum):
    APPROVE_SUPPLIER_ONBOARDING = "approve_supplier_onboarding"


class ControlDomain(str, Enum):
    SUPPLIER_CONTROL = "supplier_control"
    PROCESS_CONTROL = "process_control"
    DESIGN_CONTROL = "design_control"
    DATA_MEASUREMENT_CONTROL = "data_measurement_control"
    EVIDENCE_VALIDATION_CONTROL = "evidence_validation_control"
    GOVERNANCE_DECISION_CONTROL = "governance_decision_control"
    REGULATORY_COMPLIANCE_CONTROL = "regulatory_compliance_control"
    OPERATIONAL_CONTINUITY_CONTROL = "operational_continuity_control"


@dataclass(frozen=True)
class ControlExpectation:
    control_id: str
    control_description: str
    expected_evidence: List[str]
    minimum_required: bool = True


@dataclass(frozen=True)
class DecisionMatrix:
    decision: DecisionScenario
    domains: Dict[ControlDomain, List[ControlExpectation]]


def build_supplier_onboarding_matrix() -> DecisionMatrix:
    d = DecisionScenario.APPROVE_SUPPLIER_ONBOARDING

    domains: Dict[ControlDomain, List[ControlExpectation]] = {
        ControlDomain.SUPPLIER_CONTROL: [
            ControlExpectation(
                control_id="SC01",
                control_description="Supplier qualification criteria defined and applied",
                expected_evidence=["Supplier qualification checklist", "Supplier assessment record"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="SC02",
                control_description="Supplier change notification mechanism defined",
                expected_evidence=["Change notification rule or clause", "Supplier agreement excerpt"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="SC03",
                control_description="Single source dependency identified and recorded",
                expected_evidence=["Dependency note", "Contingency outline"],
                minimum_required=False,
            ),
        ],
        ControlDomain.PROCESS_CONTROL: [
            ControlExpectation(
                control_id="PC01",
                control_description="Incoming inspection or acceptance criteria defined",
                expected_evidence=["Incoming inspection checklist", "Acceptance criteria"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="PC02",
                control_description="Rejection and escalation criteria defined",
                expected_evidence=["Escalation rule", "Rejection criteria note"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="PC03",
                control_description="Process impact of supplier variability assessed",
                expected_evidence=["Impact assessment note", "Monitoring plan"],
                minimum_required=False,
            ),
        ],
        ControlDomain.DESIGN_CONTROL: [
            ControlExpectation(
                control_id="DC01",
                control_description="Supplier related design assumptions documented",
                expected_evidence=["Assumptions log entry", "Design rationale note"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="DC02",
                control_description="Supplier specification dependency identified and referenced",
                expected_evidence=["Supplier specification reference", "Dependency mapping note"],
                minimum_required=False,
            ),
        ],
        ControlDomain.DATA_MEASUREMENT_CONTROL: [
            ControlExpectation(
                control_id="DM01",
                control_description="Supplier data sources identified and owned",
                expected_evidence=["Data source list", "Ownership assignment"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="DM02",
                control_description="Data or specification change tracking defined",
                expected_evidence=["Version tracking note", "Change log template"],
                minimum_required=False,
            ),
        ],
        ControlDomain.EVIDENCE_VALIDATION_CONTROL: [
            ControlExpectation(
                control_id="EV01",
                control_description="Evidence checklist defined for supplier onboarding",
                expected_evidence=["Evidence checklist", "Evidence review record"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="EV02",
                control_description="Evidence acceptance criteria defined",
                expected_evidence=["Acceptance criteria note"],
                minimum_required=True,
            ),
        ],
        ControlDomain.GOVERNANCE_DECISION_CONTROL: [
            ControlExpectation(
                control_id="GD01",
                control_description="Decision owner and approval criteria defined",
                expected_evidence=["Decision owner record", "Approval criteria document"],
                minimum_required=True,
            ),
            ControlExpectation(
                control_id="GD02",
                control_description="Decision log format and traceability defined",
                expected_evidence=["Decision log template", "Sample decision log entry"],
                minimum_required=False,
            ),
        ],
        ControlDomain.REGULATORY_COMPLIANCE_CONTROL: [
            ControlExpectation(
                control_id="RC01",
                control_description="Regulatory relevance assessed and recorded",
                expected_evidence=["Regulatory relevance note", "Documentation requirement list"],
                minimum_required=False,
            ),
        ],
        ControlDomain.OPERATIONAL_CONTINUITY_CONTROL: [
            ControlExpectation(
                control_id="OC01",
                control_description="Supplier failure scenarios and contingency defined",
                expected_evidence=["Failure scenario list", "Contingency note"],
                minimum_required=False,
            ),
        ],
    }

    return DecisionMatrix(decision=d, domains=domains)


def get_matrix(decision: DecisionScenario) -> DecisionMatrix:
    if decision == DecisionScenario.APPROVE_SUPPLIER_ONBOARDING:
        return build_supplier_onboarding_matrix()
    return build_supplier_onboarding_matrix()
