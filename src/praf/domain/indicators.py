from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from praf.config.schemas import AllowedAnswerType
from .categories import RiskCategory
from .domains import RiskDomain
from .natures import RiskNature


class Polarity(str, Enum):
    """Direction of an indicator's response relative to risk.

    RISK_WHEN_ABSENT  -- the question asks whether a protective control is in
                         place (e.g. "Are assumptions documented?"). An
                         affirmative answer means the control exists, so risk is
                         LOW; a negative answer means risk is HIGH.
    RISK_WHEN_PRESENT -- the question asks about the presence/level of a hazard
                         (e.g. "Is there single-source dependency?"). An
                         affirmative / high answer means risk is HIGH.
    """

    RISK_WHEN_ABSENT = "risk_when_absent"
    RISK_WHEN_PRESENT = "risk_when_present"


@dataclass(frozen=True)
class Indicator:
    indicator_id: str
    question: str
    answer_type: AllowedAnswerType
    domain: RiskDomain
    category: RiskCategory
    nature: RiskNature
    base_weight: float = 1.0
    polarity: Polarity = Polarity.RISK_WHEN_ABSENT


INDICATOR_LIBRARY: Dict[str, Indicator] = {
    "I001": Indicator(
        indicator_id="I001",
        question="Are key design assumptions explicitly documented?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.DESIGN_MATURITY,
        category=RiskCategory.UNVALIDATED_ASSUMPTIONS,
        nature=RiskNature.STRUCTURAL,
        base_weight=1.10,
    ),
    "I002": Indicator(
        indicator_id="I002",
        question="Is there a traceable link from requirements to design decisions?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.REGULATORY_COMPLIANCE,
        category=RiskCategory.TRACEABILITY_GAPS,
        nature=RiskNature.STRUCTURAL,
        base_weight=1.15,
    ),
    "I003": Indicator(
        indicator_id="I003",
        question="Are acceptance criteria defined for key verification checks?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.REGULATORY_COMPLIANCE,
        category=RiskCategory.DOCUMENTATION_GAPS,
        nature=RiskNature.PROCESS,
        base_weight=1.05,
    ),
    "I004": Indicator(
        indicator_id="I004",
        question="How sensitive is the system to environmental conditions?",
        answer_type=AllowedAnswerType.LOW_MED_HIGH,
        domain=RiskDomain.MEASUREMENT_INTEGRITY,
        category=RiskCategory.ENVIRONMENTAL_SENSITIVITY,
        nature=RiskNature.TECHNICAL,
        base_weight=1.00,
        polarity=Polarity.RISK_WHEN_PRESENT,
    ),
    "I005": Indicator(
        indicator_id="I005",
        question="How likely is long-term drift without an early warning signal?",
        answer_type=AllowedAnswerType.LOW_MED_HIGH,
        domain=RiskDomain.MEASUREMENT_INTEGRITY,
        category=RiskCategory.DRIFT_STABILITY,
        nature=RiskNature.TECHNICAL,
        base_weight=1.05,
        polarity=Polarity.RISK_WHEN_PRESENT,
    ),
    "I006": Indicator(
        indicator_id="I006",
        question="How high is batch-to-batch variability exposure in consumables?",
        answer_type=AllowedAnswerType.LOW_MED_HIGH,
        domain=RiskDomain.MANUFACTURING,
        category=RiskCategory.BATCH_VARIABILITY,
        nature=RiskNature.PROCESS,
        base_weight=1.10,
        polarity=Polarity.RISK_WHEN_PRESENT,
    ),
    "I007": Indicator(
        indicator_id="I007",
        question="Is there a defined QC threshold set for critical-to-quality parameters?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.MANUFACTURING,
        category=RiskCategory.QC_GAPS,
        nature=RiskNature.PROCESS,
        base_weight=1.10,
    ),
    "I008": Indicator(
        indicator_id="I008",
        question="Is there single-source dependency for critical components?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.SUPPLY_CHAIN,
        category=RiskCategory.SINGLE_SOURCE_SUPPLIER,
        nature=RiskNature.EXTERNAL_DEPENDENCY,
        base_weight=1.20,
        polarity=Polarity.RISK_WHEN_PRESENT,
    ),
    "I009": Indicator(
        indicator_id="I009",
        question="Is supplier change control defined and enforced contractually?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.SUPPLY_CHAIN,
        category=RiskCategory.SUPPLIER_CHANGE_RISK,
        nature=RiskNature.EXTERNAL_DEPENDENCY,
        base_weight=1.10,
    ),
    "I010": Indicator(
        indicator_id="I010",
        question="Is the data capture plan defined for this stage of the project?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.DATA_EVIDENCE,
        category=RiskCategory.DATA_DEFINITION_GAPS,
        nature=RiskNature.DECISION_GOVERNANCE,
        base_weight=1.10,
    ),
    "I011": Indicator(
        indicator_id="I011",
        question="Is there an auditable record of key risk decisions and changes?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.DECISION_GOVERNANCE,
        category=RiskCategory.AUDIT_TRAIL_GAPS,
        nature=RiskNature.DECISION_GOVERNANCE,
        base_weight=1.15,
    ),
    "I012": Indicator(
        indicator_id="I012",
        question="Are escalation thresholds defined and applied consistently?",
        answer_type=AllowedAnswerType.YES_NO,
        domain=RiskDomain.DECISION_GOVERNANCE,
        category=RiskCategory.ESCALATION_GAPS,
        nature=RiskNature.DECISION_GOVERNANCE,
        base_weight=1.20,
    ),
}
