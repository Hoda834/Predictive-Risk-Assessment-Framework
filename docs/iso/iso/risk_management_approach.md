# Risk management approach

This document describes how the Predictive Risk Assessment Framework (PRAF)
supports design-stage risk management for early-stage point-of-care testing
(POCT) device development. It is written to be read alongside `scoring_method.md`
(the scoring mechanics) and is structured to map onto the planning content ISO
14971 expects of a risk management process.

> **Scope note.** PRAF is a *decision-support and triage* tool for the design
> stage. It does **not** replace a manufacturer's risk management file, hazard
> analysis, or design controls. It helps teams surface and prioritise risk areas
> early; the formal risk record remains the manufacturer's responsibility.

## 1. Intended use and scope

- **Intended use:** to give design-stage teams a structured, repeatable,
  explainable first-pass view of where risk concentrates across seven risk
  domains, so effort and escalation are directed early.
- **In scope:** qualitative/semi-quantitative indicator scoring, domain
  classification, decision-gate guidance, and a traceable record of each run.
- **Out of scope:** clinical performance evaluation, statistical validation of
  the device, formal harm/hazard analysis, and any use as the system of record
  for regulatory submission.

## 2. Relationship to standards

PRAF is *informed by*, and intended to feed into, the following. It does **not**
claim conformity to them on its own.

| Standard | How PRAF relates |
| --- | --- |
| ISO 14971 (risk management for medical devices) | Domain/indicator triage, acceptability thresholds, and the severity guard reflect its risk-based thinking; PRAF output is an input to the manufacturer's 14971 process, not a substitute. |
| ISO 13485 (QMS) | Each run emits a versioned, timestamped record (§5) intended to be filed as an ISO 13485 record. |
| IEC 62304 (software lifecycle) | The engine is versioned (`MODEL_VERSION`, `tool_version`) and unit-tested; full software validation is **not yet done** (§6). |
| ISO 15189 / CLSI (lab & POCT quality) | Indicator content is oriented to POCT concerns (measurement integrity, batch variability, QC); indicators are **not** yet cross-referenced to specific clauses. |

## 3. Risk acceptability criteria

The default acceptability policy is two thresholds on the 0–100 domain index:
`< 40` acceptable, `40–<70` action required, `≥ 70` escalation required
(see `scoring_method.md` §5). In addition, a **severity guard** (§6 there) raises
a domain's level when an individual hazard reaches catastrophic impact,
regardless of the averaged index.

These criteria are **governance defaults**, chosen for triage, and are
configurable per project. They are **not** derived from device-specific harm
analysis. A project applying PRAF should review and, where appropriate, replace
them once product-specific severity/probability definitions exist, and record
that decision.

## 4. Process

1. **Context** — select the project activity and stage; this sets
   activity-dependent domain sensitivity weights.
2. **Assessment** — answer the indicator library (response + likelihood, impact,
   detectability per indicator).
3. **Initial risk** — the engine computes domain indices, applies the severity
   guard, and classifies each domain *before* risk controls.
4. **Risk controls & residual risk** — declared controls (with status and a
   quantified likelihood/detectability effect) are applied and the
   classification is recomputed. Only implemented/verified controls earn
   numeric credit; planned ones are reported as intent. Impact is never reduced
   by a control (see `docs/design_decisions.md`, ADR-007).
5. **Decision gate** — the overall gate (proceed / revise / escalate) is taken
   on **residual** risk, with initial figures reported alongside.
6. **Traceability** — each indicator is linked to the controls applied to it and
   the resulting level change (hazard → control → residual decision).
7. **Sensitivity** — every input is perturbed ±1 and re-classified; fragile
   domains (band flips under a single step) are named in the report.
8. **Record** — a full audit record is produced (§5).
9. **Review** — results — especially severity overrides, unverified controls,
   fragile domains, and the input completeness report — are reviewed by the
   responsible owner before action.

## 5. Records and traceability

Every run produces an audit trail containing:

- **Provenance:** UTC timestamp, software version, risk-model version, and
  report-schema version.
- **Policy in force:** the acceptability thresholds used.
- **Context:** activity and stage.
- **Input completeness:** which indicators were fully answered, which values were
  missing (and therefore defaulted), and any unrecognised inputs.
- **Results:** initial *and* residual per-domain scores and levels, the overall
  decision (taken on residual risk), and any severity-guard overrides with
  their triggering indicator and reason.
- **Controls:** every declared control with status, effect, and whether it was
  applied; unverified-but-applied controls are flagged.
- **Traceability:** per indicator — question, initial severity, controls
  applied, residual severity, and the domain's initial → residual level.
- **Sensitivity:** the ±1 perturbation results, including every band flip and
  the list of fragile domains.
- **Full detail:** per-indicator inputs, scaled values, and contributions.

Because the model version is recorded, a stored result can be tied to the exact
indicator library, weights, and thresholds that produced it. The trail is a
structured record; it is **not** cryptographically signed or tamper-evident, so
integrity/retention controls (e.g. for 21 CFR Part 11) must be provided by the
surrounding quality system.

## 6. Validation status (read this before relying on output)

**PRAF is a prototype and has NOT been validated as a medical-device risk tool.**

- The indicator content, weights, and thresholds are **expert-shaped defaults,
  not empirically or clinically derived**, and carry no validation evidence.
- There is unit-test coverage of the engine's behaviour, but **no formal software
  validation (IEC 62304 / ISO 13485 §4.1.6), no traceability matrix, and no
  design history file**.
- Output is **decision support only**. It must not be used as the sole basis for
  a safety or regulatory decision, and any use in a regulated context requires
  independent verification and validation by the manufacturer.

## 7. Roles

- **Assessor** — completes the indicator inputs for a given context.
- **Risk owner** — reviews results, severity overrides, and completeness, and
  decides on actions/escalation.
- **Quality function** — owns threshold/weight configuration, model versioning,
  and retention of the audit records.
