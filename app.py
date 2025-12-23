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

def indicator_controls(indicator_id: str) -> list[str]:
    mapping = {
        "I001": ["Create an assumptions log", "Add design rationale note", "Schedule design review checkpoint"],
        "I002": ["Create traceability matrix", "Link requirements to design decisions", "Record verification mapping"],
        "I003": ["Define acceptance criteria", "Create verification checklist", "Add sign off step to design review"],
        "I004": ["Define environmental operating range", "Plan sensitivity testing", "Add environmental controls to spec"],
        "I005": ["Define drift indicators", "Plan stability verification", "Add recalibration trigger criteria"],
        "I006": ["Define CTQ parameters", "Plan batch variability review", "Set sampling and inspection rules"],
        "I007": ["Define QC thresholds", "Create QC release criteria", "Document nonconformance handling"],
        "I008": ["Identify second source", "Create supplier risk rating", "Define contingency plan"],
        "I009": ["Add supplier change control clause", "Define incoming inspection", "Set periodic supplier review"],
        "I010": ["Define data capture plan", "Assign data owner", "Define data quality checks"],
        "I011": ["Create decision log template", "Log key decisions and changes", "Define audit trail ownership"],
        "I012": ["Define escalation thresholds", "Assign escalation owner", "Define stop revise proceed criteria"],
    }
    return mapping.get(indicator_id, ["Define corrective action", "Assign owner", "Reassess after completion"])

def is_risk_active(answer_type: str, answer) -> bool:
    if answer_type == "yes_no":
        return str(answer).strip().lower() in {"no", "n", "false", "0"}
    if answer_type == "low_med_high":
        return str(answer).strip().lower() in {"medium", "high"}
    if answer_type == "scale_1_5":
        try:
            return int(answer) >= 3
        except Exception:
            return True
    return True

with st.sidebar:
    st.header("Context")
    activity_value = st.selectbox("Activity", options=[a.value for a in Activity], index=0)
    stage_value = st.selectbox("Stage", options=[s.value for s in ProjectStage], index=1)

ctx = Context(activity=Activity(activity_value), stage=ProjectStage(stage_value))
active_domains = active_domains_for_activity(ctx.activity)

example_path = Path("data/examples/example_inputs.json")
example_payload = {}
if example_path.exists():
    example_payload = json.loads(example_path.read_text(encoding="utf-8"))

uploaded = st.file_uploader("Upload JSON (optional)", type=["json"])
text_payload = st.text_area(
    "Paste JSON (optional)",
    value=json.dumps(example_payload, ensure_ascii=False, indent=2) if example_payload else "",
    height=160,
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

domain_to_ids: dict[RiskDomain, list[str]] = {}
for indicator_id, indicator in INDICATOR_LIBRARY.items():
    if indicator.domain in active_domains:
        domain_to_ids.setdefault(indicator.domain, []).append(indicator_id)

st.divider()
st.subheader("Assessment")

responses = {}
likelihood = {}
impact = {}
detectability = {}

for d in active_domains:
    ids = domain_to_ids.get(d, [])
    if not ids:
        continue

    st.markdown(f"### {domain_label(d)}")

    for indicator_id in ids:
        indicator = INDICATOR_LIBRARY[indicator_id]
        st.markdown(f"**{indicator_id}**  {indicator.question}")

        ans = None
        if indicator.answer_type.value == "yes_no":
            default = str(prefill_responses.get(indicator_id, "yes")).strip().lower()
            idx = 0 if default in {"yes", "y", "true", "1"} else 1
            ans = st.radio(
                f"{indicator_id}_response",
                options=["yes", "no"],
                index=idx,
                horizontal=True,
                label_visibility="collapsed",
            )
        elif indicator.answer_type.value == "low_med_high":
            opts = ["low", "medium", "high"]
            default = str(prefill_responses.get(indicator_id, "medium")).strip().lower()
            idx = opts.index(default) if default in opts else 1
            ans = st.selectbox(
                f"{indicator_id}_response",
                options=opts,
                index=idx,
                label_visibility="collapsed",
            )
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
        active = is_risk_active(indicator.answer_type.value, ans)

        if active:
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

raw_classifications = classify_domains(
    aggregated.domain_scores,
    low_threshold=4.0,
    high_threshold=6.0,
)

decision = decide(raw_classifications)
expl = explain(raw_classifications, score_result.indicator_details, score_result.local_scores, top_n=3)

domain_scores = {d: float(aggregated.domain_scores.get(d, 0.0)) for d in active_domains}
max_score = max(domain_scores.values()) if domain_scores else 1.0
if max_score <= 0.0:
    max_score = 1.0

normalised_domain_scores = {d: (domain_scores[d] / max_score) * 100.0 for d in domain_scores}

st.subheader("Risk Register Output")

rows = []
for d in active_domains:
    if d not in raw_classifications:
        continue
    level = raw_classifications[d].level.value
    top_ids = [x[0] for x in expl.top_contributors_by_domain.get(d, [])]
    rows.append(
        {
            "Domain": domain_label(d),
            "Level": level,
            "Score_0_100": round(float(normalised_domain_scores.get(d, 0.0)), 1),
            "Top_indicators": ", ".join(top_ids),
        }
    )

st.dataframe(rows, use_container_width=True)

st.subheader("Controls and Evidence")

control_rows = []
for d in active_domains:
    top_ids = [x[0] for x in expl.top_contributors_by_domain.get(d, [])]
    for iid in top_ids:
        indicator = INDICATOR_LIBRARY[iid]
        active = is_risk_active(indicator.answer_type.value, responses.get(iid))
        if not active:
            continue
        actions = indicator_controls(iid)
        control_rows.append(
            {
                "Indicator": iid,
                "Domain": domain_label(d),
                "Required_controls": " | ".join(actions),
                "Evidence_expected": "Updated artefact and audit log entry",
            }
        )

if control_rows:
    st.dataframe(control_rows, use_container_width=True)
else:
    st.write("No active risks identified based on current responses.")

with st.expander("Debug details"):
    st.json(
        {
            "context": {"activity": ctx.activity.value, "stage": ctx.stage.value},
            "overall_decision": decision.overall.value,
            "domain_scores_raw": {k.value: v for k, v in domain_scores.items()},
            "domain_scores_0_100": {k.value: round(v, 2) for k, v in normalised_domain_scores.items()},
        }
    )
