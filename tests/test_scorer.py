from praf.domain.activities import Activity, ProjectStage, Context
from praf.domain.domains import activity_domain_weights
from praf.engine.scorer import score_indicators


def test_score_indicators_returns_scores():
    ctx = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)
    domain_weights = activity_domain_weights(ctx.activity)

    responses = {"I001": "no"}
    likelihood = {"I001": 3}
    impact = {"I001": 3}
    detectability = {"I001": 3}

    result = score_indicators(responses, likelihood, impact, detectability, domain_weights)
    assert "I001" in result.local_scores
    assert result.local_scores["I001"] > 0.0
