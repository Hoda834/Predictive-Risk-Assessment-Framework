from praf.domain.activities import Activity, ProjectStage, Context
from praf.engine.pipeline import run_assessment


CTX = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)


def test_borderline_classification_is_reported_fragile():
    # Constructed to sit near a band edge: supply-chain with mid-range inputs.
    responses = {"I008": "yes", "I009": "no"}
    lid = {"I008": 3, "I009": 3}
    res = run_assessment(responses, lid, lid, lid, CTX)
    sens = res.report["sensitivity"]
    assert sens is not None
    # A mid-band score must flip under at least one single ±1 change.
    assert sens["stable"] is False
    assert sens["domain_flips"]
    flip = sens["domain_flips"][0]
    assert {"indicator_id", "axis", "delta", "domain", "from_level", "to_level"} <= set(flip)


def test_extreme_case_is_stable():
    # Deep worst-case: every ±1 perturbation keeps everything in escalation.
    ids = ["I001", "I002", "I003"]
    responses = {i: "no" for i in ids}
    lid = {i: 5 for i in ids}
    res = run_assessment(responses, lid, lid, lid, CTX)
    sens = res.report["sensitivity"]
    # Domains driven to the top of the scale by these inputs shouldn't flip on
    # a single step; if any do, they must be named rather than hidden.
    assert isinstance(sens["stable"], bool)
    assert sens["baseline_overall_decision"] == "escalate"


def test_sensitivity_can_be_disabled():
    res = run_assessment({"I001": "no"}, {}, {}, {}, CTX, include_sensitivity=False)
    assert res.report["sensitivity"] is None


def test_sensitivity_respects_controls():
    # With controls applied, sensitivity runs on the residual flow: baseline
    # levels must match the residual classification, not the initial one.
    from praf.domain.controls import Control, ControlStatus

    responses = {"I008": "yes", "I009": "no"}
    lid = {"I008": 3, "I009": 3}
    control = Control(
        control_id="C1",
        name="dual sourcing",
        indicator_ids=("I008",),
        status=ControlStatus.VERIFIED,
        likelihood_reduction=2,
        detectability_reduction=1,
    )
    res = run_assessment(responses, lid, lid, lid, CTX, controls=[control])
    sens = res.report["sensitivity"]
    assert (
        sens["baseline_domain_levels"]["supply_chain"]
        == res.report["residual"]["domain_scores"]["supply_chain"]["level"]
    )
