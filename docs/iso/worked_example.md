# Worked example

Every number below is computed by hand from `data/examples/example_inputs.json`
and matches `data/examples/example_outputs.json` (regenerate with
`python scripts/generate_example_outputs.py`). Formulas: `docs/iso/scoring_method.md`.

Context: `activity = product_design`, `stage = design`. For this activity the
domain weights include `design_maturity = 1.25` and `manufacturing = 1.00`.

## 1. One indicator, initial risk — I001

*"Are key design assumptions explicitly documented?"* — yes/no, domain
`design_maturity`, nature `structural` (modifier **1.25**), base weight
**1.10**, polarity **risk-when-absent**.

Inputs: response `"no"`, likelihood `4`, impact `4`, detectability `4`.

| Step | Computation | Value |
| --- | --- | --- |
| Raw answer axis | `"no"` → 1 | 1.0 |
| Polarity (risk-when-absent) | `6 − 1` | **5.0** |
| Base | `(5 + 4 + 4 + 4) / 4` | 4.25 |
| Severity | `(4.25 − 1) / 4` | **0.8125** |
| Weight (ex-domain) | `1.25 × 1.10` | 1.375 |
| Contribution | `0.8125 × 1.375` | **1.1171875** |

## 2. Domain index — design_maturity

I001 is the only indicator in this domain, so the weight-normalised mean is:

```
base_index = 100 × 1.1171875 / 1.375 = 81.25
index      = min(100, 81.25 × 1.25)  = 100.0     → escalation_required (≥ 70)
```

## 3. Residual risk — control C001 on I001

C001 (*Design assumptions register with owner sign-off*, status **verified**)
reduces likelihood by 2 and detectability by 1. Impact and the response axis
are never touched by a control (ADR-007).

| Axis | Initial | Residual |
| --- | --- | --- |
| Response | 5.0 | 5.0 (unchanged) |
| Likelihood | 4.0 | **2.0** |
| Impact | 4.0 | 4.0 (unchanged) |
| Detectability | 4.0 | **3.0** |

```
base     = (5 + 2 + 4 + 3) / 4 = 3.5
severity = (3.5 − 1) / 4       = 0.625
index    = min(100, (100 × 0.625 × 1.375 / 1.375) × 1.25)
         = min(100, 62.5 × 1.25) = 78.125        → still escalation_required
```

Traceability row produced: `I001 → [C001] → severity 0.8125 → 0.625`,
domain level `escalation_required → escalation_required`, decision `escalate`.
The control helps but does not clear the gate — which the report shows honestly.

## 4. A residual band change — manufacturing

Two indicators: I006 (*batch-to-batch variability*, `"high"` → 5,
L 4 / I 4 / D 4, weight `1.05 × 1.10 = 1.155`) and I007 (*QC thresholds
defined?*, `"no"` → inverted 5, L 3 / I 4 / D 4, weight 1.155).

Initial:

```
severities:     I006 = 0.8125            I007 = 0.75
contributions:  I006 = 0.9384375         I007 = 0.86625
base_index = 100 × (0.9384375 + 0.86625) / (1.155 + 1.155) = 78.125
index      = 78.125 × 1.00 = 78.125       → escalation_required
```

C002 (*Automated QC trend monitoring*, status **implemented** → applies but is
flagged unverified) reduces likelihood by 1 and detectability by 2 on both:

```
I006: (5 + 3 + 4 + 2)/4 = 3.5  → severity 0.625
I007: (5 + 2 + 4 + 2)/4 = 3.25 → severity 0.5625
base_index = 100 × (0.721875 + 0.6496875) / 2.31 = 59.375
                                          → action_required (40 ≤ 59.375 < 70)
```

The domain drops a full band — and because C002 is only *implemented*, the CLI
warns: `residual risk relies on implemented-but-unverified controls: C002`.

## 5. What the planned control does NOT do

C003 (*second-source qualification*, status **planned**) targets I008. It
appears in the report (`controls_not_applied: ["C003"]`) but supply_chain keeps
its initial index (75.0, escalation_required): intent earns no numeric credit.

## 6. Decision and sensitivity

The gate decision is taken on residual risk: several domains remain in
escalation, so `overall_decision = escalate`. The sensitivity block perturbs
every effective L/I/D value by ±1 and re-runs the residual classification; for
this deep-red example no single step flips any band (`stable: true`). For a
borderline assessment the same block names each input whose ±1 change flips a
domain — those domains are listed in `fragile_domains` and deserve scrutiny
before the gate decision is trusted.
