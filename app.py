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
    assets_to_df,
    risks_to_df,
    control_coverage_df,
)
from praf.engine.pdf_export import build_pdf_report

st.set_page_config(page_title="Asset Risk Control Planner", layout="wide")
st.title("Asset Risk Control Planner")

CONTROL_CATALOGUE_PATH = "data/control_catalogue.csv"
DECISION_MATRIX_PATH = "data/decision_matrices/approve_supplier_onboarding.json"

catalogue = load_control_catalogue(CONTROL_CATALOGUE_PATH)
control_ids = [c["id"] for c in catalogue]

if "assets" not in st.session_state:
    st.session_state.assets = []

if "risks" not in st.session_state:
    st.session_state.risks = []

page = st.sidebar.radio("Section", options=["Assets", "Risks", "Outputs"], index=0)

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
                personal_data=bool(personal_data),
                access=access.strip(),
            )
        )

    if st.session_state.assets:
        st.dataframe(assets_to_df(st.session_state.assets), use_container_width=True)

if page == "Risks":
    if not st.session_state.assets:
        st.error("Add at least one asset first.")
        st.stop()

    assets_by_id = {a.asset_id: a for a in st.session_state.assets}
    asset_id = st.selectbox("Select asset", options=list(assets_by_id.keys()))
    st.write(f"Selected asset: {assets_by_id[int(asset_id)].name}")

    prob_opts = ["Low", "Medium", "High"]

    with st.form("add_risk", clear_on_submit=True):
        title = st.text_input("Risk title")
        description = st.text_area("Risk description", height=90)
        owner = st.text_input("Risk owner")
        source = st.text_input("Source / cause")
        cia = st.multiselect("CIA affected", ["C", "I", "A"])
        likelihood = st.selectbox("Likelihood", prob_opts, index=1)
        impact = st.selectbox("Impact", prob_opts, index=1)
        selected_controls = st.multiselect("Applicable controls", options=control_ids)
        residual_likelihood = st.selectbox("Residual likelihood", prob_opts, index=1)
        residual_impact = st.selectbox("Residual impact", prob_opts, index=1)
        submit = st.form_submit_button("Add risk")

    if submit and (title.strip() or description.strip()):
        l = likelihood
        i = impact
        score = calculate_score(l, i)
        treatment = suggest_treatment(score, threshold=4)
        rl = residual_likelihood
        ri = residual_impact
        residual_score = calculate_score(rl, ri)

        st.session_state.risks.append(
            Risk(
                risk_id=str(uuid.uuid4())[:8],
                asset_id=int(asset_id),
                title=title.strip() if title.strip() else description.strip()[:60],
                description=description.strip(),
                owner=owner.strip(),
                source=source.strip(),
                cia=cia,
                likelihood=l,
                impact=i,
                score=int(score),
                suggested_treatment=treatment,
                selected_controls=list(selected_controls),
                residual_likelihood=rl,
                residual_impact=ri,
                residual_score=int(residual_score),
            )
        )

    if st.session_state.risks:
        df = risks_to_df(st.session_state.risks, assets_by_id)
        st.dataframe(df, use_container_width=True)

if page == "Outputs":
    if not st.session_state.risks:
        st.error("No risks defined.")
        st.stop()

    assets_by_id = {a.asset_id: a for a in st.session_state.assets}
    decision_matrix = load_decision_matrix(DECISION_MATRIX_PATH)
    readiness = evaluate_readiness(decision_matrix, st.session_state.risks)

    st.subheader("Decision readiness")
    status = readiness["readiness"]

    if status == "ready":
        st.success("READY")
    elif status == "conditionally_ready":
        st.warning("CONDITIONALLY READY")
    else:
        st.error("NOT READY")

    st.write("Reasons")
    st.write(readiness["reasons"])

    st.write("Missing required controls")
    st.write(readiness["missing_required_controls"])

    st.write("High residual risks")
    st.write(
        {
            "count": readiness["high_residual_risk_count"],
            "threshold": readiness["high_residual_threshold"],
            "max_allowed": readiness["max_allowed_high_residual_risks"],
        }
    )

    st.subheader("Risk register ranked")
    risk_df = risks_to_df(st.session_state.risks, assets_by_id)
    st.dataframe(risk_df, use_container_width=True)

    st.subheader("Control coverage matrix")
    control_df = control_coverage_df(st.session_state.risks, catalogue)
    st.dataframe(control_df, use_container_width=True)

    pdf_bytes = build_pdf_report(
        context={"decision_title": decision_matrix.get("title", ""), "scope": "generic"},
        readiness={
            "readiness": readiness["readiness"],
            "reasons": readiness["reasons"],
            "missing_required_controls": readiness["missing_required_controls"],
        },
        risk_df=risk_df,
        control_df=control_df,
    )

    st.download_button(
        "Download PDF report",
        data=pdf_bytes,
        file_name="decision_readiness_report.pdf",
        mime="application/pdf",
    )
