# Changelog

All notable changes to PRAF are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semver.

Two versions are tracked deliberately:

- **Package version** (`praf.__version__`, below) — the software.
- **Risk-model version** (`praf.MODEL_VERSION`) — the indicator library, weight
  tables, thresholds, and control-effect semantics. Every report records both,
  so a stored assessment is traceable to the exact model that produced it.

## [0.3.0] — 2026-07-31 · model `risk-model-2026.2`

### Added
- **Initial vs residual risk.** Risk controls (`controls` section of the input)
  with a quantified effect model: each control reduces the scaled likelihood
  and/or detectability of the indicators it addresses (impact is deliberately
  not reducible by annotation — see `docs/design_decisions.md` ADR-007).
  `planned` controls carry no numeric effect; `implemented` ones apply but are
  flagged unverified; `verified` ones apply cleanly.
- **Traceability block**: per indicator — question, initial severity, controls
  applied, residual severity, initial/residual domain level, residual decision.
- **Sensitivity (uncertainty) analysis**: one-at-a-time ±1 perturbation of every
  effective likelihood/impact/detectability value; reports each domain-band or
  overall-decision flip and names fragile domains.
- **Golden regression**: `data/examples/example_outputs.json` is now tracked,
  generated with a pinned timestamp (`--generated-at`), and asserted against a
  fresh run in `tests/test_reproducibility.py`.
- CI workflow (GitHub Actions) running the suite on Python 3.10–3.12.
- `docs/design_decisions.md` (ADRs) and `docs/worked_example.md` (hand-computed
  example of every formula).
- CLI `--generated-at` flag for reproducible reports.

### Changed
- The gate decision (`overall_decision`) is now taken on **residual** risk; the
  initial figures are reported alongside. With no controls supplied, residual
  equals initial by construction, so existing consumers see no change.
- `MODEL_VERSION` bumped to `risk-model-2026.2` (control-effect semantics added).

## [0.2.0] — 2026-07-31 · model `risk-model-2026.1`

### Added
- Severity guard: a catastrophic-impact backstop that raises (never lowers) a
  domain's classification, so a high-severity hazard cannot be averaged into
  "acceptable" (ISO 14971 alignment).
- Input validation and completeness reporting (missing / unknown / out-of-range
  values are surfaced instead of silently imputed).
- Audit-trail provenance: UTC timestamp, tool version, model version, schema
  version, thresholds in force, context, input completeness, severity overrides.
- Pipeline orchestration module (`engine/pipeline.py`); CLI usage/help, friendly
  errors, optional output file; atomic JSON export.
- Test suite expanded 11 → 38.

### Fixed
- Order-dependent category domain-weight aggregation (last-write-wins → max).
- Inverted acceptability thresholds (`low >= high`) now rejected.
- Streamlit app `pop(idx)`-during-iteration removal bug.
- Dependency spec inconsistency; streamlit moved to the optional `[app]` extra.

## [0.1.0] · model `risk-model-2026.1` (implicit)

Initial prototype: indicator library (I001–I012), 7 risk domains, averaged
0–100 domain index, three-band classification, Streamlit guidance app.
