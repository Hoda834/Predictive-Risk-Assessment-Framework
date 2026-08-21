from praf.domain.activities import Activity, ProjectStage, Context
from praf.engine.pipeline import run_assessment


def _entries(report):
    return {e["key"]: e["value"] for e in report["audit_trail"]}


def test_audit_trail_has_provenance_fields():
    ctx = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)
    res = run_assessment(
        {"I001": "no"}, {"I001": 5}, {"I001": 5}, {"I001": 5},
        ctx, generated_at="2026-01-01T00:00:00+00:00",
    )
    entries = _entries(res.report)

    # Provenance: who/when/which-version and the policy in force.
    assert entries["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert entries["tool_version"]
    assert entries["model_version"]
    assert entries["schema_version"]
    assert entries["thresholds"] == {"low": 40.0, "high": 70.0}
    assert entries["context"] == {"activity": "product_design", "stage": "design"}
    assert entries["input_completeness"]["total_indicators"] == 12

    # Results are still present.
    assert "overall_decision" in entries
    assert "domain_scores" in entries
    assert "indicator_details" in entries


def test_audit_trail_records_severity_override():
    ctx = Context(activity=Activity.PRODUCT_DESIGN, stage=ProjectStage.DESIGN)
    res = run_assessment(
        {"I004": "low"}, {"I004": 1}, {"I004": 5}, {"I004": 1},
        ctx, generated_at="2026-01-01T00:00:00+00:00",
    )
    entries = _entries(res.report)
    assert "severity_overrides" in entries
    assert entries["severity_overrides"][0]["indicator_id"] == "I004"
