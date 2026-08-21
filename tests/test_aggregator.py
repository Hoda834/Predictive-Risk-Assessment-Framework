from praf.domain.domains import RiskDomain
from praf.engine.aggregator import aggregate_scores, _clamp_0_100


def test_clamp_floor_and_cap():
    assert _clamp_0_100(-5.0) == 0.0
    assert _clamp_0_100(150.0) == 100.0
    assert _clamp_0_100(42.0) == 42.0


def test_domain_index_bounded_and_capped_by_weight():
    # A large domain weight must not push the index above 100.
    details = {
        "X1": {
            "domain": RiskDomain.MANUFACTURING.value,
            "category": "batch_variability",
            "weight_ex_domain": 1.0,
            "domain_weight": 5.0,  # deliberately large
        }
    }
    local = {"X1": 1.0}  # severity 1.0 * weight 1.0
    agg = aggregate_scores(details, local)
    assert agg.domain_scores[RiskDomain.MANUFACTURING] == 100.0


def test_category_weight_is_order_independent():
    # Same category, two indicators carrying different domain weights. The result
    # must not depend on dict iteration order (previously last-write-wins).
    def build(order):
        details = {}
        for iid, dw in order:
            details[iid] = {
                "domain": RiskDomain.MANUFACTURING.value,
                "category": "qc_gaps",
                "weight_ex_domain": 1.0,
                "domain_weight": dw,
            }
        local = {iid: 0.5 for iid, _ in order}
        return aggregate_scores(details, local).category_scores["qc_gaps"]

    forward = build([("A", 1.0), ("B", 1.5)])
    reverse = build([("B", 1.5), ("A", 1.0)])
    assert forward == reverse
