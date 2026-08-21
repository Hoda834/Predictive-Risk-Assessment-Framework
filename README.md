# Predictive-Risk-Assessment-Framework

Design-stage risk triage and decision-support for early-stage POCT device development.

**What an assessment produces:** initial risk (before controls) → residual risk
(after quantified risk controls) → a gate decision on residual risk, plus full
hazard→control→residual **traceability**, a ±1 **sensitivity analysis** naming
fragile classifications, and a versioned, timestamped **audit trail**.

> **Status: prototype (v0.3.0) — decision support only.** PRAF is a structured,
> explainable scoring tool for surfacing and prioritising risk early. It is
> **not** a validated medical-device risk system and does not replace a
> manufacturer's ISO 14971 risk file or design controls. Its indicators,
> weights, and thresholds are governance defaults, not clinically derived, and
> carry no validation evidence. See
> [`docs/iso/risk_management_approach.md`](docs/iso/risk_management_approach.md)
> for scope, acceptability criteria, and validation status.

## Repository layout

```text
.
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── requirements.txt
├── app.py                      # optional Streamlit app (needs the [app] extra)
├── .github/workflows/ci.yml    # tests on Python 3.10–3.12 + golden-output check
├── src/praf/
│   ├── __init__.py             # __version__, MODEL_VERSION, SCHEMA_VERSION
│   ├── config/
│   │   ├── defaults.py         # scales + acceptability thresholds (40/70)
│   │   ├── schemas.py
│   │   └── validation.py       # input-completeness + threshold/weight checks
│   ├── domain/
│   │   ├── activities.py       # activities, project stages, context
│   │   ├── domains.py          # 7 risk domains + activity domain weights
│   │   ├── categories.py
│   │   ├── natures.py
│   │   ├── indicators.py       # built-in indicator library (I001–I012)
│   │   ├── controls.py         # risk-control model (status + quantified effect)
│   │   └── risk_patterns.py
│   ├── engine/
│   │   ├── scorer.py           # per-indicator scoring (polarity, 1–5 axes)
│   │   ├── aggregator.py       # 0–100 domain/category indices
│   │   ├── classifier.py       # acceptable / action / escalation bands
│   │   ├── severity_guard.py   # catastrophic-impact backstop (never lowers)
│   │   ├── residual.py         # residual risk: re-score after controls
│   │   ├── sensitivity.py      # ±1 OAT uncertainty analysis
│   │   ├── rules.py            # proceed / revise / escalate decision
│   │   ├── pipeline.py         # initial → residual → decision orchestration
│   │   ├── explainability.py   # top contributors per domain
│   │   ├── guidance.py         # pattern-based gate guidance (Streamlit app)
│   │   └── audit_trail.py      # provenance: timestamp, versions, thresholds
│   ├── io/
│   │   ├── loaders.py          # validated JSON input loading
│   │   └── exporters.py        # atomic JSON report export
│   └── cli/main.py
├── data/examples/
│   ├── example_inputs.json     # includes a worked controls section
│   ├── example_outputs.json    # golden output (pinned timestamp, CI-checked)
│   └── templates/              # illustrative CSV shapes (see note below)
├── docs/
│   ├── design_decisions.md     # ADRs: why each mechanism is the way it is
│   ├── worked_example.md       # every formula computed by hand
│   └── iso/
│       ├── risk_management_approach.md
│       └── scoring_method.md
├── scripts/generate_example_outputs.py   # deterministic (pinned timestamp)
└── tests/                      # 14 test modules, engine + IO + CLI + golden
```

## Installation

The core scoring engine has no third-party dependencies:

```bash
pip install -e .
```

The interactive app needs the optional `app` extra:

```bash
pip install -e ".[app]"
```

## Usage

Run the scoring pipeline on a JSON input file (see `data/examples/example_inputs.json`):

```bash
python -m praf.cli.main data/examples/example_inputs.json          # print report
python -m praf.cli.main data/examples/example_inputs.json out.json # also write it
```

The report contains, among others:

- `initial` / `residual` — risk before and after the declared controls, each
  with per-domain scores, levels, and severity-guard overrides; the top-level
  `overall_decision` is taken on residual risk.
- `traceability` — per indicator: question, initial severity, controls applied,
  residual severity, and the domain's initial → residual level.
- `sensitivity` — every domain-band flip under a single ±1 input change, and
  the resulting `fragile_domains` list.
- `input_completeness` — which indicators were fully answered; incomplete input
  is scored (missing values default to neutral) but flagged on stderr and in
  the report.

Risk controls are declared in the input's `controls` section (see the example
file): each control names the indicators it addresses, its status
(`planned` / `implemented` / `verified`), and its effect as integer step
reductions on the likelihood/detectability axes. Planned controls earn no
numeric credit; implemented ones apply but are flagged unverified.

Use `--generated-at <ISO-8601>` to pin the report timestamp for reproducible
output. Run `python -m praf.cli.main --help` for usage. A fully hand-computed
walkthrough of the example lives in
[`docs/worked_example.md`](docs/worked_example.md); design rationale in
[`docs/design_decisions.md`](docs/design_decisions.md).

Launch the interactive app (requires the `[app]` extra):

```bash
streamlit run app.py
```

> The CSV files under `data/examples/templates/` are **illustrative examples** of
> the indicator/weight shape. A CSV import path for custom libraries/weights is
> not yet wired into the engine; scoring today uses the built-in library.

Regenerate the example output (deterministic — the timestamp is pinned, and CI
fails if the tracked golden file drifts from a fresh run):

```bash
python scripts/generate_example_outputs.py
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```
