from praf.domain.activities import Activity, ProjectStage, Context
from praf.domain.domains import RiskDomain, activity_domain_weights
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains, RiskLevel
from praf.engine.severity_guard import apply_severity_guard
from praf.config.defaults import Defaults


def _classify(responses, likelihood, impact, detectability):
    ctx = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)
    dw = activity_domain_weights(ctx.activity)
    d = Defaults()
    scored = score_indicators(responses, likelihood, impact, detectability, dw)
    agg = aggregate_scores(scored.indicator_details, scored.local_scores)
    classifications = classify_domains(agg.domain_scores, d.low_threshold, d.high_threshold)
    return classifications, scored.indicator_details


def test_catastrophic_impact_is_not_averaged_into_acceptable():
    # I004 lives in MEASUREMENT_INTEGRITY. Low likelihood/detectability would
    # average the domain index below the acceptable threshold, but catastrophic
    # impact must force at least action_required.
    classifications, details = _classify(
        {"I004": "low"}, {"I004": 1}, {"I004": 5}, {"I004": 1}
    )
    before = classifications[RiskDomain.MEASUREMENT_INTEGRITY].level
    assert before == RiskLevel.ACCEPTABLE  # the averaged index alone

    result = apply_severity_guard(classifications, details)
    after = result.classifications[RiskDomain.MEASUREMENT_INTEGRITY].level
    assert after == RiskLevel.ACTION_REQUIRED
    assert result.triggered
    assert result.overrides[0].indicator_id == "I004"


def test_catastrophic_impact_with_high_likelihood_escalates():
    classifications, details = _classify(
        {"I004": "high"}, {"I004": 5}, {"I004": 5}, {"I004": 1}
    )
    result = apply_severity_guard(classifications, details)
    assert result.classifications[RiskDomain.MEASUREMENT_INTEGRITY].level == RiskLevel.ESCALATION_REQUIRED


def test_guard_never_lowers_a_level():
    # A domain already escalated by the index must stay escalated even if no
    # indicator trips the severity trigger.
    classifications, details = _classify(
        {"I004": "high"}, {"I004": 5}, {"I004": 4}, {"I004": 5}
    )
    result = apply_severity_guard(classifications, details)
    for domain, c in result.classifications.items():
        assert c.level == classifications[domain].level or c.level == RiskLevel.ESCALATION_REQUIRED


def test_guard_does_not_trigger_on_moderate_impact():
    classifications, details = _classify(
        {"I004": "medium"}, {"I004": 3}, {"I004": 3}, {"I004": 3}
    )
    result = apply_severity_guard(classifications, details)
    assert not result.triggered
