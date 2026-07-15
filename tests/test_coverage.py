"""Coverage / insufficient-data behaviour.

Locks in the fix for the silent-empty-input bug: "we have no data" must be
reported as INSUFFICIENT_DATA / gather_data, not as a confident medium risk.
"""

from praf.domain import INDICATOR_LIBRARY
from praf.domain.activities import Activity
from praf.domain.domains import RiskDomain, activity_domain_weights
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains, RiskLevel
from praf.engine.rules import decide, Decision
from praf.config.defaults import Defaults


def _classify(responses):
    dw = activity_domain_weights(Activity.PRODUCT_DESIGN)
    d = Defaults()
    scored = score_indicators(responses, {}, {}, {}, dw)
    agg = aggregate_scores(scored.indicator_details, scored.local_scores)
    cls = classify_domains(
        agg.domain_scores, d.low_threshold, d.high_threshold,
        coverage=agg.domain_coverage, coverage_threshold=d.coverage_threshold,
    )
    return agg, cls, decide(cls)


def test_empty_input_is_insufficient_data():
    agg, cls, decision = _classify({})
    assert decision.overall == Decision.GATHER_DATA
    assert all(c.level == RiskLevel.INSUFFICIENT_DATA for c in cls.values())
    assert all(c.coverage == 0.0 for c in cls.values())


def test_full_coverage_is_not_insufficient():
    responses = {i: "no" for i in INDICATOR_LIBRARY}
    agg, cls, decision = _classify(responses)
    assert all(c.coverage == 1.0 for c in cls.values())
    assert all(c.level != RiskLevel.INSUFFICIENT_DATA for c in cls.values())


def test_partial_coverage_flags_only_uncovered_domains():
    # Answer both supply-chain indicators only.
    agg, cls, decision = _classify({"I008": "yes", "I009": "no"})
    assert cls[RiskDomain.SUPPLY_CHAIN].coverage == 1.0
    assert cls[RiskDomain.SUPPLY_CHAIN].level != RiskLevel.INSUFFICIENT_DATA
    assert cls[RiskDomain.DESIGN_MATURITY].level == RiskLevel.INSUFFICIENT_DATA
    assert decision.overall == Decision.GATHER_DATA


def test_escalation_outranks_gather_data():
    # One fully-answered domain escalates; the rest are uncovered. A real
    # escalation must still surface as the overall decision.
    responses = {"I008": "yes", "I009": "no"}
    dw = activity_domain_weights(Activity.SUPPLIER_SELECTION)  # boosts supply_chain
    d = Defaults()
    scored = score_indicators(responses, {"I008": 5, "I009": 5}, {"I008": 5, "I009": 5}, {"I008": 5, "I009": 5}, dw)
    agg = aggregate_scores(scored.indicator_details, scored.local_scores)
    cls = classify_domains(
        agg.domain_scores, d.low_threshold, d.high_threshold,
        coverage=agg.domain_coverage, coverage_threshold=d.coverage_threshold,
    )
    decision = decide(cls)
    assert cls[RiskDomain.SUPPLY_CHAIN].level == RiskLevel.ESCALATION_REQUIRED
    assert decision.overall == Decision.ESCALATE
