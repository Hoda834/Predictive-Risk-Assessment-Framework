from praf.domain.domains import RiskDomain
from praf.engine.classifier import classify_domains, RiskLevel
from praf.config.defaults import Defaults


def test_classify_domains_thresholds():
    d = Defaults()
    domain_scores = {
        RiskDomain.DESIGN_MATURITY: 25.0,   # below low -> acceptable
        RiskDomain.MANUFACTURING: 55.0,     # between -> action_required
        RiskDomain.REGULATORY_COMPLIANCE: 80.0,  # >= high -> escalation
    }
    results = classify_domains(domain_scores, d.low_threshold, d.high_threshold)
    assert results[RiskDomain.DESIGN_MATURITY].level == RiskLevel.ACCEPTABLE
    assert results[RiskDomain.MANUFACTURING].level == RiskLevel.ACTION_REQUIRED
    assert results[RiskDomain.REGULATORY_COMPLIANCE].level == RiskLevel.ESCALATION_REQUIRED


def test_classify_domains_boundaries():
    # Boundaries are inclusive on the upper level: index == threshold escalates.
    results = classify_domains(
        {RiskDomain.SUPPLY_CHAIN: 40.0, RiskDomain.DATA_EVIDENCE: 70.0},
        low_threshold=40.0,
        high_threshold=70.0,
    )
    assert results[RiskDomain.SUPPLY_CHAIN].level == RiskLevel.ACTION_REQUIRED
    assert results[RiskDomain.DATA_EVIDENCE].level == RiskLevel.ESCALATION_REQUIRED
