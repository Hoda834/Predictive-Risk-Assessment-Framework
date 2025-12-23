import json
from pathlib import Path
import streamlit as st

from praf.domain import Activity, ProjectStage, Context
from praf.domain.domains import activity_domain_weights
from praf.engine.scorer import score_indicators
from praf.engine.aggregator import aggregate_scores
from praf.engine.classifier import classify_domains
from praf.engine.rules import decide
from praf.engine.explainability import explain
from praf.engine.audit_trail import build_audit_trail
from praf.config.defaults import Defaults

st.set_page_config(page_title="Predictive Risk Assessment Framework", layout="wide")

st.title("Predictive Risk Assessment Framework")

defaults = Defaults()

with st.sidebar:
    st.header("Context")
    activity = st.selectbox(
        "Activity",
        options=[a.value for a in Activity],
        index=0,
    )
    stage = st.selectbox(
        "Stage",
        options=[s.value for s in ProjectStage],
        index=1,
    )

st.subheader("Input JSON")
st.write("Either paste JSON or upload a file matching the example structure.")

example_path = Path("data/examples/example_inputs.json")
example_payload = {}
if example_path.exists():
    example_payload = json.loads(example_path.read_text(encoding="utf-8"))

uploaded = st.file_uploader("Upload JSON", type=["json"])
text_payload = st.text_area(
    "Paste JSON",
    value=json.dumps(example_payload, ensure_ascii=False, indent=2) if example_payload else "",
    height=260,
)

payload = None
if uploaded is not None:
    payload = json.loads(uploaded.read().decode("utf-8"))
else:
    if text_payload.strip():
        payload = json.loads(text_payload)

if payload is None:
    st.stop()

responses = dict(payload.get("responses", {}))
likelihood = dict(payload.get("likelihood", {}))
impact = dict(payload.get("impact", {}))
detectability = dict(payload.get("detectability", {}))

ctx = Context(activity=Activity(activity), stage=ProjectStage(stage))
domain_weights = activity_domain_weights(ctx.activity)

score_result = score_indicators(
    responses=responses,
    likelihood=likelihood,
    impact=impact,
    detectability=detectability,
    domain_weights=domain_weights,
)

aggregated = aggregate_scores(score_result.indicator_details, score_result.local_scores)
classifications = classify_domains(
    aggregated.domain_scores,
    low_threshold=defaults.low_threshold,
    high_threshold=defaults.high_threshold,
)
decision = decide(classifications)
expl = explain(classifications, score_result.indicator_details, score_result.local_scores, top_n=5)
audit = build_audit_trail(classifications, decision, score_result.indicator_details, score_result.local_scores)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Overall Decision")
    st.write(decision.overall.value)

    st.subheader("Per Domain Decision")
    st.json({d.value: decision.per_domain[d].value for d in decision.per_domain})

with col2:
    st.subheader("Domain Scores")
    st.json({d.value: {"score": classifications[d].score, "level": classifications[d].level.value} for d in classifications})

st.subheader("Top Contributors By Domain")
st.json({d.value: expl.top_contributors_by_domain.get(d, []) for d in classifications})

st.subheader("Audit Trail")
st.json([{"key": a.key, "value": a.value} for a in audit])
