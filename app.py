import json
from pathlib import Path
import streamlit as st

from praf.domain import Activity, ProjectStage, Context, INDICATOR_LIBRARY
from praf.domain.domains import RiskDomain, activity_domain_weights
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

def active_domains_for_activity(activity: Activity) -> list[RiskDomain]:
    mapping = {
        Activity.PRODUCT_DESIGN: [
            RiskDomain.DESIGN_MATURITY,
            RiskDomain.REGULATORY_COMPLIANCE,
            RiskDomain.DATA_EVIDENCE,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.PROTOTYPE_DEVELOPMENT: [
            RiskDomain.MEASUREMENT_INTEGRITY,
            RiskDomain.DESIGN_MATURITY,
            RiskDomain.DATA_EVIDENCE,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.MANUFACTURING_SCALE_UP: [
            RiskDomain.MANUFACTURING,
            RiskDomain.SUPPLY_CHAIN,
            RiskDomain.REGULATORY_COMPLIANCE,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.SUPPLIER_SELECTION: [
            RiskDomain.SUPPLY_CHAIN,
            RiskDomain.MANUFACTURING,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.REGULATORY_PREPARATION: [
            RiskDomain.REGULATORY_COMPLIANCE,
            RiskDomain.DATA_EVIDENCE,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.DATA_COLLECTION: [
            RiskDomain.DATA_EVIDENCE,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.SYSTEM_DESIGN: [
            RiskDomain.DESIGN_MATURITY,
            RiskDomain.DATA_EVIDENCE,
            RiskDomain.DECISION_GOVERNANCE,
        ],
        Activity.PROCESS_OPTIMISATION: [
            RiskDomain.MANUFACTURING,
            RiskDomain.DECISION_GOVERNANCE,
        ],
    }
    return mapping.get(activity, list(RiskDomain))

def domain_label(d: RiskDomain) -> str:
    labels = {
        RiskDomain.DESIGN_MATURITY: "Design maturity",
        RiskDomain.REGULATORY_COMPLIANCE: "Regulatory and compliance",
        RiskDomain.MANUFACTURING: "Manufacturing variability",
        RiskDomain.MEASUREMENT_INTEGRITY: "Measurement integrity",
        RiskDomain.SUPPLY_CHAIN: "Supplier and supply chain",
        RiskDomain.DATA_EVIDENCE: "Data and evidence",
        RiskDomain.DECISION_GOVERNANCE: "Decision and governance",
    }
    return labels.get(d, d.value)

with st.sidebar:
    st.header("Context")
    activity_value = st.selectbox("Activity", options=[a.value for a in Activity], index=0)
    stage_value = st.selectbox("Stage", options=[s.value for s in ProjectStage], index=1)

ctx = Context(activity=Activity(activity_value), stage=ProjectStage(stage_value))
active_domains = active_domains_for_activity(ctx.activity)

st.subheader("Optional Input JSON")
example_path = Path("data/examples/example_inputs.json")
example_payload = {}
if example_path.exists():
    example_payload = json.loads(example_path.read_text(encoding="utf-8"))

uploaded = st.file_uploader("Upload JSON", type=["json"])
text_payload = st.text_area(
    "Paste JSON",
    value=json.dumps(example_payload, ensure_ascii=False, indent=2) if example_payload else "",
    height=180,
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

domain_to_indicators: dict[RiskDomain, list[str]] = {}
for indicator_id, indicator in INDICATOR_LIBRARY.items():
    if indicator.domain in active_domains:
        domain_to_indicators.setdefault(indicator.domain, []).append(indicator_id)

st.divider()
st.subheader("Risk Indicator Assessment")

responses = {}
likelihood = {}
impact = {}
detectability = {}

for d in active_domains:
    ids = domain_to_indicators.get(d, [])
    if not ids:
        continue

    st.markdown(f"### {domain_label(d)}")

    for indicator_id in ids:
        indicator = INDICATOR_LIBRARY[indicator_id]
        st.markdown(f"**{indicator_id}**  {indicator.question}")

        risk_active = True

        if indicator.answer_type.value == "yes_no":
            default = str(prefill_responses.get(indicator_id, "yes")).lower()
            idx = 0 if default in {"yes", "y", "true", "1"} else 1
            ans = st.radio(
                f"{indicator_id}_response",
                options=["yes", "no"],
                index=idx,
                horizontal=True,
                label_visibility="collapsed",
            )
            responses[indicator_id] = ans
            risk_active = (ans == "no")

        elif indicator.answer_type.value == "low_med_high":
            opts = ["low", "medium", "high"]
            default = str(prefill_responses.get(indicator_id, "medium")).lower()
            idx = opts.index(default) if default in opts else 1
            ans = st.selectbox(
                f"{indicator_id}_response",
                options=opts,
                index=idx,
                label_visibility="collapsed",
            )
            responses[indicator_id] = ans
            risk_active = (ans != "low")

        else:
            default_val = int(prefill_responses.get(indicator_id, 3)) if str(prefill_responses.get(indicator_id, "")).strip() else 3
            ans = st.slider(
                f"{indicator_id}_response",
                min_value=1,
                max_value=5,
                value=int(default_val),
                label_visibility="collapsed",
            )
            responses[indicator_id] = ans
            risk_active = (int(ans) >= 3)

        if risk_active:
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
        else:
            likelihood[indicator_id] = 1
            impact[indicator_id] = 1
            detectability[indicator_id] = 1

        st.divider()

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
    low_threshold=4.0,
    high_threshold=6.0,
)

decision = decide(classifications)
expl = explain(classifications, score_result.indicator_details, score_result.local_scores, top_n=3)
audit = build_audit_trail(classifications, decision, score_result.indicator_details, score_result.local_scores)

st.subheader("Decision Summary")

left, right = st.columns(2)

with left:
    st.write("Overall decision")
    st.write(decision.overall.value)

with right:
    st.write("Active domains")
    st.write([domain_label(d) for d in active_domains])

st.subheader("Domain Results")

domain_rows = {}
for d in active_domains:
    if d in classifications:
        domain_rows[d.value] = {
            "level": classifications[d].level.value,
            "score": round(float(classifications[d].score), 3),
            "top_indicators": [x[0] for x in expl.top_contributors_by_domain.get(d, [])],
        }

st.json(domain_rows)

with st.expander("Full audit and raw details"):
    st.json([{"key": a.key, "value": a.value} for a in audit])
