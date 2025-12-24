import json
from praf.asset_risk import load_decision_matrix, evaluate_readiness
import uuid
from pathlib import Path
import streamlit as st

from praf.domain import Activity, ProjectStage, Context
from praf.domain.risk_patterns import RiskPattern, UserRisk, suggest_pattern_from_text
from praf.engine.guidance import generate_guidance

st.set_page_config(page_title="Predictive Risk Assessment Framework", layout="wide")
st.title("Predictive Risk Assessment Framework")

if "risks" not in st.session_state:
    st.session_state.risks = []

with st.sidebar:
    st.header("Context")
    activity_value = st.selectbox("Activity", options=[a.value for a in Activity], index=0)
    stage_value = st.selectbox("Stage", options=[s.value for s in ProjectStage], index=1)

    st.header("Optional industry")
    industry_value = st.selectbox(
        "Industry",
        options=["generic", "medtech", "saas", "manufacturing", "finance", "other"],
        index=0,
    )

ctx = Context(activity=Activity(activity_value), stage=ProjectStage(stage_value))

st.subheader("Add risks")
st.write("Write risks freely. You will be required to map each risk to a pattern before guidance is generated.")

with st.form("add_risk_form", clear_on_submit=True):
    description = st.text_area("Risk description", height=90)
    owner = st.text_input("Owner", value="")
    submitted = st.form_submit_button("Add risk")

if submitted and description.strip():
    rid = str(uuid.uuid4())[:8]
    suggestion = suggest_pattern_from_text(description)
    st.session_state.risks.append(
        {
            "risk_id": rid,
            "description": description.strip(),
            "owner": owner.strip(),
            "suggested_pattern": suggestion.value,
            "pattern": None,
            "likelihood": 3,
            "impact": 3,
            "detectability": 3,
        }
    )

if not st.session_state.risks:
    st.stop()

st.divider()
st.subheader("Map risks to patterns")

pattern_options = [p.value for p in RiskPattern]

for idx, r in enumerate(st.session_state.risks):
    st.markdown(f"### Risk {idx + 1}: {r['risk_id']}")
    st.write(r["description"])

    c1, c2 = st.columns(2)
    with c1:
        st.write("Suggested pattern")
        st.write(r["suggested_pattern"])
    with c2:
        selected = st.selectbox(
            f"Pattern mapping {r['risk_id']}",
            options=pattern_options,
            index=pattern_options.index(r["suggested_pattern"]) if r["suggested_pattern"] in pattern_options else 0,
        )
        r["pattern"] = selected

    c3, c4, c5 = st.columns(3)
    with c3:
        r["likelihood"] = st.slider(f"Likelihood {r['risk_id']}", 1, 5, int(r["likelihood"]))
    with c4:
        r["impact"] = st.slider(f"Impact {r['risk_id']}", 1, 5, int(r["impact"]))
    with c5:
        r["detectability"] = st.slider(f"Detectability {r['risk_id']}", 1, 5, int(r["detectability"]))

    remove = st.button(f"Remove {r['risk_id']}")
    if remove:
        st.session_state.risks.pop(idx)
        st.rerun()

st.divider()

unmapped = [r for r in st.session_state.risks if not r.get("pattern")]
if unmapped:
    st.error("All risks must be mapped to a pattern before guidance can be generated.")
    st.stop()

risks = []
for r in st.session_state.risks:
    risks.append(
        UserRisk(
            risk_id=r["risk_id"],
            description=r["description"],
            owner=r.get("owner", ""),
            likelihood=int(r["likelihood"]),
            impact=int(r["impact"]),
            detectability=int(r["detectability"]),
            pattern=RiskPattern(r["pattern"]),
        )
    )

summary = generate_guidance(ctx, risks)

st.subheader("Decision gate guidance")
st.write(summary.overall_gate_guidance.value)
st.write(summary.rationale)

st.subheader("Action guidance by risk")

rows = []
for item in summary.items:
    r = next((x for x in risks if x.risk_id == item.risk_id), None)
    rows.append(
        {
            "risk_id": item.risk_id,
            "owner": r.owner if r else "",
            "pattern": item.pattern.value,
            "priority": item.priority,
            "gate_guidance": item.gate_guidance.value,
            "recommended_actions": " | ".join(item.recommended_actions),
            "expected_evidence": " | ".join(item.expected_evidence),
        }
    )

st.dataframe(rows, use_container_width=True)

with st.expander("Export as JSON"):
    export_payload = {
        "context": {
            "activity": ctx.activity.value,
            "stage": ctx.stage.value,
            "industry": industry_value,
        },
        "risks": [
            {
                "risk_id": r.risk_id,
                "description": r.description,
                "owner": r.owner,
                "pattern": r.pattern.value if r.pattern else None,
                "likelihood": r.likelihood,
                "impact": r.impact,
                "detectability": r.detectability,
            }
            for r in risks
        ],
        "guidance": {
            "overall_gate_guidance": summary.overall_gate_guidance.value,
            "rationale": summary.rationale,
            "items": [
                {
                    "risk_id": it.risk_id,
                    "pattern": it.pattern.value,
                    "priority": it.priority,
                    "gate_guidance": it.gate_guidance.value,
                    "why": it.why,
                    "recommended_actions": it.recommended_actions,
                    "expected_evidence": it.expected_evidence,
                }
                for it in summary.items
            ],
        },
    }
    st.json(export_payload)
