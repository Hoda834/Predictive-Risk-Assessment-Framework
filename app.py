import uuid
import streamlit as st

from praf.asset_risk import (
    Asset,
    Risk,
    calculate_score,
    suggest_treatment,
    load_control_catalogue,
    load_decision_matrix,
    evaluate_readiness,
)

st.set_page_config(page_title="Predictive Risk Assessment Framework", layout="wide")
st.title("Predictive Risk Assessment Framework")

CONTROL_CATALOGUE_PATH = "data/control_catalogue.csv"
DECISION_MATRIX_PATH = "data/decision_matrices/approve_supplier_onboarding.json"

controls = load_control_catalogue(CONTROL_CATALOGUE_PATH)
control_ids = [c["id"] for c in controls]

if "assets" not in st.session_state:
    st.session_state.assets = []

if "risks" not in st.session_state:
    st.session_state.risks = []

page = st.sidebar.radio(
    "Section",
    options=["Assets", "Risks", "Outputs"],
    index=0,
)

# ---------------- ASSETS ----------------
if page == "Assets":
    st.subheader("Asset inventory")

    with st.form("add_asset", clear_on_submit=True):
        name = st.text_input("Asset name")
        description = st.text_area("Description", height=80)
        owner = st.text_input("Owner")
        category = st.text_input("Category")
        cia = st.multiselect("CIA relevance", ["C", "I", "A"])
        personal_data = st.checkbox("Contains personal data")
        access = st.text_input("Who should have access")
        submit = st.form_submit_button("Add asset")

    if submit and name.strip():
        st.session_state.assets.append(
            Asset(
                asset_id=len(st.session_state.assets) + 1,
                name=name.strip(),
                description=description.strip(),
                owner=owner.strip(),
                category=category.strip(),
                cia=cia,
                personal_data=personal_data,
                access=access.strip(),
            )
        )

    if st.session_state.assets:
        st.dataframe(
            [a.__dict__ for a in st.session_state.assets],
            use_container_width=True,
        )

# ---------------- RISKS ----------------
if page == "Risks":
    if not st.session_state.assets:
        st.error("Add at least one asset first.")
        st.stop()

    st.subheader("Risks on assets")

    asset_map = {a.asset_id: a for a in st.session_state.assets}
    asset_id = st.selectbox("Select asset", options=list(asset_map.keys()))

    with st.form("add_risk", clear_on_submit=True):
        event = st.text_area("Risk event", height=80)
        source = st.text_input("Source / cause")
        cia = st.multiselect("CIA affected", ["C", "I", "A"])
        likelihood = st.selectbox("Likelihood", ["Low", "Medium", "High"], index=1)
        impact = st.selectbox("Impact", ["Low", "Medium", "High"], index=1)
        selected_controls = st.multiselect("Applicable controls", control_ids)
        residual_likelihood = st.selectbox("Residual likelihood", ["Low", "Medium", "High"], index=1)
        residual_impact = st.selectbox("Residual impact", ["Low", "Medium", "High"], index=1)
        submit = st.form_submit_button("Add risk")

    if submit and event.strip():
        score = calculate_score(likelihood, impact)
        treatment = suggest_treatment(score)
        residual_score = calculate_score(residual_likelihood, residual_impact)

        st.session_state.risks.append(
            Risk(
                risk_id=str(uuid.uuid4())[:8],
                asset_id=asset_id,
                event=event.strip(),
                source=source.strip(),
                cia=cia,
                likelihood=likelihood,
                impact=impact,
                score=score,
                suggested_treatment=treatment,
                selected_controls=selected_controls,
                residual_likelihood=residual_likelihood,
                residual_impact=residual_impact,
                residual_score=residual_score,
            )
        )

    if st.session_state.risks:
        st.dataframe(
            [r.__dict__ for r in st.session_state.risks],
            use_container_width=True,
        )

# ---------------- OUTPUTS ----------------
if page == "Outputs":
    st.subheader("Decision readiness")

    if not st.session_state.risks:
        st.error("No risks defined.")
        st.stop()

    decision_matrix = load_decision_matrix(DECISION_MATRIX_PATH)
    result = evaluate_readiness(decision_matrix, st.session_state.risks)

    status = result["readiness"]

    if status == "ready":
        st.success("Decision status: READY")
    elif status == "conditionally_ready":
        st.warning("Decision status: CONDITIONALLY READY")
    else:
        st.error("Decision status: NOT READY")

    st.markdown("### Missing required controls")
    st.write(result["missing_required_controls"])

    st.markdown("### High residual risks")
    st.write(result["high_residual_risk_count"])

    st.markdown("### Reasons")
    st.write(result["reasons"])
