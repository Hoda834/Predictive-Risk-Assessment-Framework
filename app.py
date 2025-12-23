import json
from pathlib import Path
import streamlit as st

from praf.domain import Activity, ProjectStage, Context, INDICATOR_LIBRARY
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
    activity_value = st.selectbox(
        "Activity",
        options=[a.value for a in Activity],
        index=0,
    )
    stage_value = st.selectbox(
        "Stage",
        options=[s.value for s in ProjectStage],
        index=1,
    )

ctx = Context(
    activity=Activity(activity_value),
    stage=ProjectStage(stage_value),
)

st.subheader("Optional Input JSON (prefill only)")

example_path = Path("data/examples/example_inputs.json")
example_payload = {}
if example_path.exists():
    example_payload = json.loads(example_path.read_text(encoding="utf-8"))

uploaded = st.file_uploader("Upload JSON", type=["json"])
text_payload = st.text_area(
    "Paste JSON",
    value=json.dumps(example_payload, ensure_ascii=False, indent=2) if example_payload else "",
    height=220,
)

prefill = {}
if uploaded is not None:
    prefill = json.loads(uploaded.read().decode("utf-8"))
elif text_payload.strip():
    prefill = json.loads(text_payload)

prefill_responses = dict(prefill.get("responses", {}))
prefill_likelihood = dict(prefill.get("likelihood", {}))
prefill_impact = dict(prefill.get("impact", {}))
prefill_detectability = dict(prefill.get("detectability", {}))

st.divider()
st.subheader("Risk Indicator Assessment")

responses = {}
likelihood = {}
impact = {}
detectability = {}

for indicator_id, indicator in INDICATOR_LIBRARY.items():
    st.markdown(f"**{indicator_id}**  {indicator.question}")

    if indicator.answer_type.value == "yes_no":
        default = str(prefill_responses.get(indicator_id, "yes")).lower()
        idx = 0 if default in {"yes", "y", "true", "1"} else 1
        responses[indicator_id] = st.radio(
            f"{indicator_id}_response",
            options=["yes", "no"],
            index=idx,
            horizontal=True,
            label_visibility="collapsed",
        )
    elif indicator.answer_type.value == "low_med_high":
        opts = ["low", "medium", "high"]
        default = str(prefill_responses.get(indicator_id, "medium")).lower()
        idx = opts.index(default) if default in opts else 1
        responses[indicator_id] = st.selectbox(
            f"{indicator_id}_response",
            options=opts,
            index=idx,
            label_visibility="collapsed",
        )
    else:
        default_val = int(prefill_responses.get(indicator_id, 3)) if str(prefill_responses.get(indicator_id, "")).strip() else 3
        responses[indicator_id] = st.slider(
            f"{indicator_id}_response",
            min_value=1,
            max_value=5,
            value=int(default_val),
            label_visibility="collapsed",
        )

    c1, c2, c3 = st.columns(3)

    with c1:
        likelihood[indicator_id] = st.slider(
            f"{indicator_id}_likelihood",
            min_value=1,
            max_value=5,
            value=int(prefill_likelihood.get(indicator_id, 3)),
        )
    with c2:
        impact[indicator_id] = st.slider(
            f"{indicator_id}_impact",
            min_value=1,
            max_value=5,
            value=int(prefill_impact.get(indicator_id, 3)),
        )
    with c3:
        detectability[indicator_id] = st.slider(
            f"{indicator_id}_detectability",
            min_value=1,
            max_value=5,
            value=int(prefill_detectability.get(indicator_id, 3)),
        )

    st.divider()

domain_weights = activity_domain_weights(ctx.activity)

score_result = score_indicators(
    responses=responses,
    likelihood=likelihood,
    impact=impact,
    detectability=detectability,
    domain_weights=domain_weights,
)

aggregated = aggregate_scores(
    score_result.indicator_details,
    score_result.local_scores,
)

classifications = classify_domains(
    aggregated.domain_scores,
    low_threshold=defaults.low_threshold,
    high_threshold=defaults.high_threshold,
)

decision = decide(classifications)

expl = explain(
    classifications,
    score_result.indicator_details,
    score_result.local_scores,
    top_n=5,
)

audit = build_audit_trail(
    classifications,
    decision,
    score_result.indicator_details,
    score_result.local_scores,
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Overall Decision")
    st.write(decision.overall.value)

    st.subheader("Per Domain Decision")
    st.json({d.value: decision.per_domain[d].value for d in decision.per_domain})

with col2:
    st.subheader("Domain Scores")
    st.json(
        {
            d.value: {
                "score": classifications[d].score,
                "level": classifications[d].level.value,
            }
            for d in classifications
        }
    )

st.subheader("Top Contributors By Domain")
st.json({d.value: expl.top_contributors_by_domain.get(d, []) for d in classifications})

st.subheader("Audit Trail")
st.json([{"key": a.key, "value": a.value} for a in audit])
