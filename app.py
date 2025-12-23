import uuid
import streamlit as st

from praf.domain import DecisionScenario, ControlDomain, UserRisk, get_matrix
from praf.engine.control_planner import (
    ControlStatus,
    ControlCheck,
    evaluate_decision_readiness,
    build_empty_control_checks,
)

st.set_page_config(page_title="Risk Guided Control Planner", layout="wide")
st.title("Risk Guided Control Planner")

if "risks" not in st.session_state:
    st.session_state.risks = []

if "control_checks" not in st.session_state:
    matrix0 = get_matrix(DecisionScenario.APPROVE_SUPPLIER_ONBOARDING)
    st.session_state.control_checks = build_empty_control_checks(matrix0)

decision_value = st.selectbox(
    "Decision scenario",
    options=[d.value for d in DecisionScenario],
    index=0,
)

decision = DecisionScenario(decision_value)
matrix = get_matrix(decision)

st.subheader("Add risks")
with st.form("add_risk_form", clear_on_submit=True):
    description = st.text_area("Risk description", height=90)
    owner = st.text_input("Owner", value="")
    submitted = st.form_submit_button("Add risk")

if submitted and description.strip():
    rid = str(uuid.uuid4())[:8]
    st.session_state.risks.append(
        {
            "risk_id": rid,
            "description": description.strip(),
            "owner": owner.strip(),
            "likelihood": 3,
            "impact": 3,
            "detectability": 3,
            "mapped_domain": None,
        }
    )

if not st.session_state.risks:
    st.stop()

st.divider()
st.subheader("Map risks to control domains and set L I D")

domain_options = ["select"] + [d.value for d in ControlDomain]

for idx, r in enumerate(st.session_state.risks):
    st.markdown(f"### Risk {idx + 1}: {r['risk_id']}")
    st.write(r["description"])

    sel = st.selectbox(
        f"Control domain mapping {r['risk_id']}",
        options=domain_options,
        index=0 if not r.get("mapped_domain") else domain_options.index(r["mapped_domain"]),
    )
    r["mapped_domain"] = None if sel == "select" else sel

    c1, c2, c3 = st.columns(3)
    with c1:
        r["likelihood"] = st.slider(f"Likelihood {r['risk_id']}", 1, 5, int(r["likelihood"]))
    with c2:
        r["impact"] = st.slider(f"Impact {r['risk_id']}", 1, 5, int(r["impact"]))
    with c3:
        r["detectability"] = st.slider(f"Detectability {r['risk_id']}", 1, 5, int(r["detectability"]))

    remove = st.button(f"Remove risk {r['risk_id']}")
    if remove:
        st.session_state.risks.pop(idx)
        st.rerun()

unmapped = [r for r in st.session_state.risks if not r.get("mapped_domain")]
if unmapped:
    st.error("All risks must be mapped to a control domain before readiness can be evaluated.")
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
            mapped_domain=ControlDomain(r["mapped_domain"]),
        )
    )

st.divider()
st.subheader("Control and evidence checklist")

if "control_checks" not in st.session_state or set(st.session_state.control_checks.keys()) != set([e.control_id for ds in matrix.domains.values() for e in ds]):
    st.session_state.control_checks = build_empty_control_checks(matrix)

for domain, expectations in matrix.domains.items():
    st.markdown(f"### {domain.value}")
    for exp in expectations:
        ck = st.session_state.control_checks.get(exp.control_id)
        if ck is None:
            ck = ControlCheck(control_id=exp.control_id, status=ControlStatus.MISSING, evidence_attached=False)

        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            st.write(f"{exp.control_id}  {exp.control_description}")
            st.write("Evidence expected: " + " | ".join(exp.expected_evidence))
        with c2:
            status_val = st.selectbox(
                f"Status {exp.control_id}",
                options=[s.value for s in ControlStatus],
                index=[s.value for s in ControlStatus].index(ck.status.value),
            )
        with c3:
            ev = st.checkbox(f"Evidence attached {exp.control_id}", value=bool(ck.evidence_attached))

        st.session_state.control_checks[exp.control_id] = ControlCheck(
            control_id=exp.control_id,
            status=ControlStatus(status_val),
            evidence_attached=bool(ev),
        )

st.divider()
st.subheader("Readiness output")

control_checks = dict(st.session_state.control_checks)
summary = evaluate_decision_readiness(decision, risks, control_checks)

st.write("Readiness")
st.write(summary.readiness)
st.write("Rationale")
st.write(summary.rationale)

st.subheader("Prioritised gaps")

rows = []
for g in summary.gaps:
    rows.append(
        {
            "priority": g.priority,
            "domain": g.domain.value,
            "control_id": g.control_id,
            "minimum_required": g.minimum_required,
            "status": g.status,
            "evidence_attached": g.evidence_attached,
            "linked_risks": ", ".join(g.linked_risks),
            "expected_evidence": " | ".join(g.evidence_expected),
        }
    )

st.dataframe(rows, use_container_width=True)

st.subheader("Domain severity focus")
st.dataframe(
    [{"domain": d, "max_severity_from_risks": s} for d, s in summary.prioritised_domains],
    use_container_width=True,
)
