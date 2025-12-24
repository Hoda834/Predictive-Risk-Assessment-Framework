from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Tuple

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


APP_TITLE = "Predictive Risk Assessment Framework"
CONTROL_CATALOGUE_PATH = "data/control_catalogue.csv"
DECISION_MATRIX_PATH = "data/decision_matrices/approve_supplier_onboarding.json"


PROB_OPTS = ["Low", "Medium", "High"]


def _now_utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _coerce_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(v) for v in x]
    return [str(x)]


def _hide_risk_id_column(df):
    if df is None:
        return df
    cols = list(df.columns)
    for c in ["risk_id", "Risk ID", "id"]:
        if c in cols:
            return df.drop(columns=[c])
    return df


def _build_required_controls_table(
    decision_matrix: Dict[str, Any],
    readiness: Dict[str, Any],
    catalogue: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    required_controls = _coerce_list(decision_matrix.get("required_controls"))
    optional_controls = _coerce_list(decision_matrix.get("optional_controls"))
    evidence_expectations = decision_matrix.get("evidence_expectations", {}) or {}
    missing_required_controls = set(_coerce_list(readiness.get("missing_required_controls")))

    catalogue_by_id: Dict[str, Dict[str, Any]] = {str(c.get("id")): c for c in catalogue}
    rows: List[Dict[str, Any]] = []

    def control_name(control_id: str) -> str:
        c = catalogue_by_id.get(str(control_id), {})
        for k in ["name", "title", "control", "description"]:
            if k in c and str(c.get(k)).strip():
                return str(c.get(k)).strip()
        return ""

    for cid in required_controls:
        rows.append(
            {
                "Control": str(cid),
                "Control name": control_name(str(cid)),
                "Type": "Required",
                "Status": "Missing" if str(cid) in missing_required_controls else "Covered",
                "Evidence expected": "; ".join(_coerce_list(evidence_expectations.get(str(cid)))) if evidence_expectations else "",
            }
        )

    for cid in optional_controls:
        rows.append(
            {
                "Control": str(cid),
                "Control name": control_name(str(cid)),
                "Type": "Optional",
                "Status": "Optional",
                "Evidence expected": "; ".join(_coerce_list(evidence_expectations.get(str(cid)))) if evidence_expectations else "",
            }
        )

    return rows


def _build_action_plan(
    decision_matrix: Dict[str, Any],
    readiness: Dict[str, Any],
    risks: List[Risk],
) -> Dict[str, Any]:
    missing_required_controls = _coerce_list(readiness.get("missing_required_controls"))
    evidence_expectations = decision_matrix.get("evidence_expectations", {}) or {}

    actions: List[Dict[str, Any]] = []
    for cid in missing_required_controls:
        actions.append(
            {
                "Priority": 1,
                "Action": f"Implement required control {cid}",
                "Deliverables": "; ".join(_coerce_list(evidence_expectations.get(str(cid)))) if evidence_expectations else "Define evidence and implementation record",
                "Owner": "TBC",
                "Target date": "TBC",
            }
        )

    high_residual_threshold = int(readiness.get("high_residual_threshold", 0))
    high_residual_count = int(readiness.get("high_residual_risk_count", 0))

    if high_residual_count > 0:
        actions.append(
            {
                "Priority": 2,
                "Action": f"Reduce high residual risks (threshold {high_residual_threshold})",
                "Deliverables": "Residual risk mitigation plan; updated residual scoring; evidence of implemented treatments",
                "Owner": "TBC",
                "Target date": "TBC",
            }
        )

    if not actions:
        actions.append(
            {
                "Priority": 1,
                "Action": "Maintain readiness controls and monitoring cadence",
                "Deliverables": "Monitoring logs; periodic reviews; evidence retention",
                "Owner": "TBC",
                "Target date": "TBC",
            }
        )

    return {
        "missing_required_controls": missing_required_controls,
        "high_residual_threshold": high_residual_threshold,
        "high_residual_count": high_residual_count,
        "actions": actions,
    }


def _build_audit_bundle(
    decision_matrix: Dict[str, Any],
    readiness: Dict[str, Any],
    risks: List[Risk],
) -> Dict[str, Any]:
    required_controls = _coerce_list(decision_matrix.get("required_controls"))
    rules = decision_matrix.get("readiness_rules", {}) or {}

    triggered: List[Dict[str, Any]] = []

    if rules.get("not_ready_if_missing_any_required_control", False):
        missing = _coerce_list(readiness.get("missing_required_controls"))
        if missing:
            triggered.append(
                {
                    "rule": "not_ready_if_missing_any_required_control",
                    "result": "Triggered",
                    "details": {"missing_required_controls": missing},
                }
            )
        else:
            triggered.append(
                {
                    "rule": "not_ready_if_missing_any_required_control",
                    "result": "Not triggered",
                    "details": {"missing_required_controls": []},
                }
            )

    max_allowed = int(rules.get("max_allowed_high_residual_risks", 0))
    high_count = int(readiness.get("high_residual_risk_count", 0))
    thr = int(readiness.get("high_residual_threshold", 0))

    triggered.append(
        {
            "rule": "max_allowed_high_residual_risks",
            "result": "Triggered" if high_count > max_allowed else "Not triggered",
            "details": {
                "count": high_count,
                "threshold": thr,
                "max_allowed": max_allowed,
            },
        }
    )

    risk_scoring_note = {
        "initial_score": "Derived from Likelihood x Impact mapping (see calculate_score).",
        "residual_score": "Derived from Residual Likelihood x Residual Impact mapping (see calculate_score).",
        "treatment_suggestion": "Derived from score threshold logic (see suggest_treatment).",
    }

    return {
        "generated_at_utc": _now_utc_iso(),
        "decision_id": decision_matrix.get("decision_id"),
        "decision_title": decision_matrix.get("title"),
        "required_controls": required_controls,
        "triggered_rules": triggered,
        "readiness_status": readiness.get("readiness"),
        "readiness_reasons": readiness.get("reasons"),
        "risk_scoring_explainability": risk_scoring_note,
        "risk_count": len(risks),
    }


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title("Predictive Risk Assessment Framework")

    try:
        catalogue = load_control_catalogue(CONTROL_CATALOGUE_PATH)
    except Exception as e:
        st.error(f"Could not load control catalogue from {CONTROL_CATALOGUE_PATH}. Error: {e}")
        st.stop()

    control_ids = [str(c.get("id")) for c in catalogue if str(c.get("id", "")).strip()]

    try:
        decision_matrix = load_decision_matrix(DECISION_MATRIX_PATH)
    except Exception as e:
        st.error(f"Could not load decision matrix from {DECISION_MATRIX_PATH}. Error: {e}")
        st.stop()

    if "assets" not in st.session_state:
        st.session_state.assets = []
    if "risks" not in st.session_state:
        st.session_state.risks = []

    with st.sidebar:
        st.subheader("Session")
        if st.button("Reset all (assets and risks)"):
            st.session_state.assets = []
            st.session_state.risks = []
            st.rerun()

        st.caption("Data paths")
        st.code(f"{CONTROL_CATALOGUE_PATH}\n{DECISION_MATRIX_PATH}")

    tab_decision, tab_action, tab_audit = st.tabs(["Decision", "Action plan", "Audit & Explainability"])

    assets_by_id = {a.asset_id: a for a in st.session_state.assets} if st.session_state.assets else {}

    with tab_decision:
        st.subheader("Decision overview")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.write("Decision")
            st.write(str(decision_matrix.get("title", "")).strip())
        with c2:
            st.write("Decision ID")
            st.write(str(decision_matrix.get("decision_id", "")).strip())
        with c3:
            st.write("Scope")
            st.write("Supplier onboarding readiness")

        st.divider()
        st.subheader("1) Asset inventory")

        with st.form("add_asset", clear_on_submit=True):
            name = st.text_input("Asset name")
            description = st.text_area("Description", height=80)
            owner = st.text_input("Owner")
            category = st.text_input("Category")
            cia = st.multiselect("CIA relevance", ["C", "I", "A"])
            personal_data = st.checkbox("Contains personal data")
            access = st.text_input("Who should have access")
            submit_asset = st.form_submit_button("Add asset")

        if submit_asset and name.strip():
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
            assets_by_id = {a.asset_id: a for a in st.session_state.assets}

        if st.session_state.assets:
            st.dataframe(assets_to_df(st.session_state.assets), use_container_width=True)
        else:
            st.info("Add at least one asset to proceed.")

        st.divider()
        st.subheader("2) Risk register")

        if not st.session_state.assets:
            st.warning("Add an asset first, then define risks.")
        else:
            asset_id = st.selectbox("Select asset", options=list(assets_by_id.keys()))
            st.write(f"Selected asset: {assets_by_id[int(asset_id)].name}")

            with st.form("add_risk", clear_on_submit=True):
                title = st.text_input("Risk title")
                description = st.text_area("Risk description", height=90)
                owner = st.text_input("Risk owner")
                source = st.text_input("Source / cause")
                cia_aff = st.multiselect("CIA affected", ["C", "I", "A"])
                likelihood = st.selectbox("Likelihood", PROB_OPTS, index=1)
                impact = st.selectbox("Impact", PROB_OPTS, index=1)
                selected_controls = st.multiselect("Applicable controls", options=control_ids)
                residual_likelihood = st.selectbox("Residual likelihood", PROB_OPTS, index=1)
                residual_impact = st.selectbox("Residual impact", PROB_OPTS, index=1)
                submit_risk = st.form_submit_button("Add risk")

            if submit_risk and (title.strip() or description.strip()):
                score = int(calculate_score(likelihood, impact))
                treatment = suggest_treatment(score, threshold=4)
                residual_score = int(calculate_score(residual_likelihood, residual_impact))

                st.session_state.risks.append(
                    Risk(
                        risk_id=str(uuid.uuid4())[:8],
                        asset_id=int(asset_id),
                        title=title.strip() if title.strip() else description.strip()[:60],
                        description=description.strip(),
                        owner=owner.strip(),
                        source=source.strip(),
                        cia=cia_aff,
                        likelihood=likelihood,
                        impact=impact,
                        score=score,
                        suggested_treatment=treatment,
                        selected_controls=list(selected_controls),
                        residual_likelihood=residual_likelihood,
                        residual_impact=residual_impact,
                        residual_score=residual_score,
                    )
                )

            if st.session_state.risks:
                risk_df = risks_to_df(st.session_state.risks, assets_by_id)
                risk_df = _hide_risk_id_column(risk_df)
                st.dataframe(risk_df, use_container_width=True)
            else:
                st.info("Add at least one risk.")

        st.divider()
        st.subheader("3) Decision status")

        if not st.session_state.risks:
            st.info("Define risks to evaluate readiness.")
        else:
            readiness = evaluate_readiness(decision_matrix, st.session_state.risks)
            status = readiness.get("readiness")

            if status == "ready":
                st.success("READY")
            elif status == "conditionally_ready":
                st.warning("CONDITIONALLY READY")
            else:
                st.error("NOT READY")

            st.write("Reasons")
            st.write(readiness.get("reasons", []))

            st.write("Missing required controls")
            st.write(readiness.get("missing_required_controls", []))

            st.write("High residual risks")
            st.write(
                {
                    "count": readiness.get("high_residual_risk_count"),
                    "threshold": readiness.get("high_residual_threshold"),
                    "max_allowed": readiness.get("max_allowed_high_residual_risks"),
                }
            )

    with tab_action:
        st.subheader("Action plan for execution team")

        if not st.session_state.risks:
            st.info("Define risks first, then the action plan will be generated.")
        else:
            readiness = evaluate_readiness(decision_matrix, st.session_state.risks)

            st.write("Required and optional controls")
            controls_rows = _build_required_controls_table(decision_matrix, readiness, catalogue)
            st.dataframe(controls_rows, use_container_width=True)

            plan = _build_action_plan(decision_matrix, readiness, st.session_state.risks)

            st.divider()
            st.write("Prioritised actions to become READY")
            st.dataframe(plan["actions"], use_container_width=True)

            st.divider()
            st.write("Control coverage matrix")
            control_df = control_coverage_df(st.session_state.risks, catalogue)
            st.dataframe(control_df, use_container_width=True)

            st.divider()
            st.write("Risk register ranked")
            assets_by_id = {a.asset_id: a for a in st.session_state.assets}
            risk_df = risks_to_df(st.session_state.risks, assets_by_id)
            risk_df = _hide_risk_id_column(risk_df)
            st.dataframe(risk_df, use_container_width=True)

    with tab_audit:
        st.subheader("Audit and explainability pack")

        if not st.session_state.risks:
            st.info("Define risks first to generate the audit pack.")
        else:
            readiness = evaluate_readiness(decision_matrix, st.session_state.risks)

            audit_bundle = _build_audit_bundle(decision_matrix, readiness, st.session_state.risks)

            st.write("Triggered rules and rationale")
            st.json(audit_bundle["triggered_rules"])

            st.write("Scoring explainability (how the numbers were derived)")
            st.json(audit_bundle["risk_scoring_explainability"])

            st.write("Decision readiness evidence")
            st.json(
                {
                    "status": readiness.get("readiness"),
                    "reasons": readiness.get("reasons", []),
                    "missing_required_controls": readiness.get("missing_required_controls", []),
                    "high_residual_risk_count": readiness.get("high_residual_risk_count"),
                    "high_residual_threshold": readiness.get("high_residual_threshold"),
                    "max_allowed_high_residual_risks": readiness.get("max_allowed_high_residual_risks"),
                }
            )

            st.divider()
            st.subheader("Export")

            assets_by_id = {a.asset_id: a for a in st.session_state.assets}
            risk_df = risks_to_df(st.session_state.risks, assets_by_id)
            risk_df = _hide_risk_id_column(risk_df)
            control_df = control_coverage_df(st.session_state.risks, catalogue)

            pdf_bytes = build_pdf_report(
                context={
                    "decision_title": str(decision_matrix.get("title", "")),
                    "decision_id": str(decision_matrix.get("decision_id", "")),
                    "scope": "supplier_onboarding",
                    "generated_at_utc": _now_utc_iso(),
                },
                readiness={
                    "readiness": readiness.get("readiness"),
                    "reasons": readiness.get("reasons", []),
                    "missing_required_controls": readiness.get("missing_required_controls", []),
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

            report_json = {
                "meta": {
                    "generated_at_utc": _now_utc_iso(),
                    "app": "praf.streamlit",
                },
                "decision_matrix": decision_matrix,
                "readiness": readiness,
                "audit_bundle": audit_bundle,
            }
            st.download_button(
                "Download audit JSON",
                data=json.dumps(report_json, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="audit_pack.json",
                mime="application/json",
            )


if __name__ == "__main__":
    main()
