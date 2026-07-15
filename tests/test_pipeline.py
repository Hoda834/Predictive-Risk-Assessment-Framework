"""End-to-end regression tests for the scoring pipeline.

These lock in the fix for the "dead classifier" bug: with the calibrated
0-100 index and thresholds, a high-risk input must be able to escalate and a
low-risk input must proceed.
"""

from praf.domain import INDICATOR_LIBRARY
from praf.domain.activities import Activity, ProjectStage, Context
from praf.domain.domains import activity_domain_weights
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains, RiskLevel
from praf.engine.rules import decide, Decision
from praf.config.defaults import Defaults


def _run(responses, lid):
    ctx = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)
    dw = activity_domain_weights(ctx.activity)
    d = Defaults()
    scored = score_indicators(responses, lid, lid, lid, dw)
    agg = aggregate_scores(scored.indicator_details, scored.local_scores)
    classifications = classify_domains(agg.domain_scores, d.low_threshold, d.high_threshold)
    return agg, classifications, decide(classifications)


def _all_ids():
    return list(INDICATOR_LIBRARY.keys())


def test_worst_case_escalates():
    ids = _all_ids()
    # "no" is worst for protective controls; the hazard indicators default to
    # neutral text here but max L/I/D drives them up regardless.
    responses = {i: "no" for i in ids}
    lid = {i: 5 for i in ids}
    _, classifications, decision = _run(responses, lid)
    assert decision.overall == Decision.ESCALATE
    assert any(c.level == RiskLevel.ESCALATION_REQUIRED for c in classifications.values())


def test_best_case_proceeds():
    ids = _all_ids()
    responses = {i: "yes" for i in ids}
    lid = {i: 1 for i in ids}
    _, classifications, decision = _run(responses, lid)
    assert decision.overall == Decision.PROCEED
    assert all(c.level == RiskLevel.ACCEPTABLE for c in classifications.values())


def test_domain_index_bounded_0_100():
    ids = _all_ids()
    agg, _, _ = _run({i: "no" for i in ids}, {i: 5 for i in ids})
    for score in agg.domain_scores.values():
        assert 0.0 <= score <= 100.0
