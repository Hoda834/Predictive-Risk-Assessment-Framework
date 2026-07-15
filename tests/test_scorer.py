from praf.domain.activities import Activity, ProjectStage, Context
from praf.domain.domains import activity_domain_weights
from praf.engine.scorer import score_indicators


def _score(responses, likelihood=None, impact=None, detectability=None):
    ctx = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)
    domain_weights = activity_domain_weights(ctx.activity)
    return score_indicators(
        responses,
        likelihood or {},
        impact or {},
        detectability or {},
        domain_weights,
    )


def test_score_indicators_returns_scores():
    result = _score({"I001": "no"}, {"I001": 3}, {"I001": 3}, {"I001": 3})
    assert "I001" in result.local_scores
    assert result.local_scores["I001"] > 0.0


def test_severity_is_normalised_0_1():
    # Worst-case inputs for a protective control -> severity 1.0.
    worst = _score({"I001": "no"}, {"I001": 5}, {"I001": 5}, {"I001": 5})
    assert worst.indicator_details["I001"]["severity"] == 1.0
    # Best-case inputs -> severity 0.0.
    best = _score({"I001": "yes"}, {"I001": 1}, {"I001": 1}, {"I001": 1})
    assert best.indicator_details["I001"]["severity"] == 0.0


def test_protective_control_polarity():
    # I001 is "risk when absent": answering "yes" (control present) is LOW risk.
    yes = _score({"I001": "yes"}, {"I001": 3}, {"I001": 3}, {"I001": 3})
    no = _score({"I001": "no"}, {"I001": 3}, {"I001": 3}, {"I001": 3})
    assert no.local_scores["I001"] > yes.local_scores["I001"]


def test_hazard_indicator_polarity():
    # I008 is "risk when present": answering "yes" (single-source) is HIGH risk.
    # This is the bug that was previously inverted.
    yes = _score({"I008": "yes"}, {"I008": 3}, {"I008": 3}, {"I008": 3})
    no = _score({"I008": "no"}, {"I008": 3}, {"I008": 3}, {"I008": 3})
    assert yes.local_scores["I008"] > no.local_scores["I008"]


def test_detectability_raises_risk():
    # Higher detectability value = harder to detect = more risk.
    hard = _score({"I001": "no"}, {"I001": 3}, {"I001": 3}, {"I001": 5})
    easy = _score({"I001": "no"}, {"I001": 3}, {"I001": 3}, {"I001": 1})
    assert hard.local_scores["I001"] > easy.local_scores["I001"]
