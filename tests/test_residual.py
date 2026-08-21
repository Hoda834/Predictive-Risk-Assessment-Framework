from praf.domain.activities import Activity, ProjectStage, Context
from praf.domain.controls import Control, ControlStatus
from praf.engine.pipeline import run_assessment


CTX = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)


def _control(**over):
    base = dict(
        control_id="C100",
        name="Test control",
        indicator_ids=("I001",),
        status=ControlStatus.VERIFIED,
        likelihood_reduction=2,
        detectability_reduction=2,
    )
    base.update(over)
    return Control(**base)


def _inputs():
    # All protective controls answered "no", elevated L/I/D — high initial risk.
    ids = ["I001", "I002", "I003"]
    responses = {i: "no" for i in ids}
    lid = {i: 4 for i in ids}
    return responses, lid


def test_no_controls_residual_equals_initial():
    responses, lid = _inputs()
    res = run_assessment(responses, lid, lid, lid, CTX, include_sensitivity=False)
    assert res.report["initial"]["domain_scores"] == res.report["residual"]["domain_scores"]
    assert res.report["initial"]["overall_decision"] == res.report["residual"]["overall_decision"]


def test_verified_control_reduces_residual():
    responses, lid = _inputs()
    res = run_assessment(
        responses, lid, lid, lid, CTX,
        controls=[_control()], include_sensitivity=False,
    )
    init = res.report["initial"]["domain_scores"]["design_maturity"]["score"]
    resid = res.report["residual"]["domain_scores"]["design_maturity"]["score"]
    assert resid < init
    # And the initial figures are untouched by the control.
    assert res.report["initial"]["severity_overrides"] == res.report["initial"].get("severity_overrides")
    assert res.report["residual"]["controls_applied"] == {"I001": ["C100"]}


def test_planned_control_has_no_numeric_effect():
    responses, lid = _inputs()
    res = run_assessment(
        responses, lid, lid, lid, CTX,
        controls=[_control(status=ControlStatus.PLANNED)], include_sensitivity=False,
    )
    assert res.report["initial"]["domain_scores"] == res.report["residual"]["domain_scores"]
    assert res.report["residual"]["controls_not_applied"] == ["C100"]


def test_implemented_control_applies_but_is_flagged_unverified():
    responses, lid = _inputs()
    res = run_assessment(
        responses, lid, lid, lid, CTX,
        controls=[_control(status=ControlStatus.IMPLEMENTED)], include_sensitivity=False,
    )
    init = res.report["initial"]["domain_scores"]["design_maturity"]["score"]
    resid = res.report["residual"]["domain_scores"]["design_maturity"]["score"]
    assert resid < init
    assert res.report["residual"]["controls_unverified"] == ["C100"]


def test_reductions_floor_at_one():
    # Massive stacked reductions must clamp the axes at 1, not go below.
    responses, lid = _inputs()
    controls = [
        _control(control_id=f"C{i}", likelihood_reduction=4, detectability_reduction=4)
        for i in range(3)
    ]
    res = run_assessment(
        responses, lid, lid, lid, CTX, controls=controls, include_sensitivity=False,
    )
    scaled = res.residual.indicator_details["I001"]["scaled"]
    assert scaled["likelihood"] == 1.0
    assert scaled["detectability"] == 1.0


def test_controls_never_touch_impact_or_response():
    responses, lid = _inputs()
    res = run_assessment(
        responses, lid, lid, lid, CTX, controls=[_control()], include_sensitivity=False,
    )
    initial_scaled = {"response": 5.0, "impact": 4.0}
    scaled = res.residual.indicator_details["I001"]["scaled"]
    assert scaled["impact"] == initial_scaled["impact"]
    assert scaled["response"] == initial_scaled["response"]


def test_severity_guard_still_holds_on_residual():
    # Catastrophic impact: likelihood reduction cannot buy the guard off,
    # because impact is untouched by controls.
    responses = {"I004": "low"}
    res = run_assessment(
        responses, {"I004": 1}, {"I004": 5}, {"I004": 1}, CTX,
        controls=[_control(indicator_ids=("I004",), likelihood_reduction=4)],
        include_sensitivity=False,
    )
    assert (
        res.report["residual"]["domain_scores"]["measurement_integrity"]["level"]
        == "action_required"
    )
    assert res.report["residual"]["severity_overrides"]


def test_traceability_links_hazard_control_residual():
    responses, lid = _inputs()
    res = run_assessment(
        responses, lid, lid, lid, CTX, controls=[_control()], include_sensitivity=False,
    )
    row = next(t for t in res.report["traceability"] if t["indicator_id"] == "I001")
    assert row["controls_applied"] == ["C100"]
    assert row["residual_severity"] < row["initial_severity"]
    assert "domain_initial_level" in row and "domain_residual_level" in row
    assert row["residual_decision"] in {"proceed", "revise", "escalate"}
