from praf.domain.domains import RiskDomain
from praf.engine.classifier import classify_domains, RiskLevel


def test_classify_domains_thresholds():
    domain_scores = {RiskDomain.DESIGN_MATURITY: 10.0, RiskDomain.REGULATORY_COMPLIANCE: 50.0}
    results = classify_domains(domain_scores, low_threshold=20.0, high_threshold=45.0)
    assert results[RiskDomain.DESIGN_MATURITY].level == RiskLevel.ACCEPTABLE
    assert results[RiskDomain.REGULATORY_COMPLIANCE].level == RiskLevel.ESCALATION_REQUIRED
