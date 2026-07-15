# Scoring method

PRAF converts each indicator's inputs into a normalised **0–100 risk index**
per domain, then classifies each domain against two thresholds.

## 1. Per-indicator inputs

Every indicator is scored from four inputs, each mapped to a 1–5 scale where
**higher always means more risk**:

| Input | Scale | Meaning of a high value |
| --- | --- | --- |
| Response | 1–5 | See *polarity* below |
| Likelihood (L) | 1–5 | More likely to occur |
| Impact (I) | 1–5 | More severe consequence |
| Detectability (D) | 1–5 | **Harder to detect** (FMEA convention) |

> **Detectability convention.** Following FMEA, a *higher* detectability value
> means the problem is *harder* to catch before it causes harm, and therefore
> *increases* risk. `5` = effectively undetectable, `1` = obvious/immediately
> caught. This is the opposite of "how detectable is it".

### Polarity

The meaning of the response depends on the indicator's **polarity**:

- **Risk when absent** (protective control, e.g. *"Are design assumptions
  documented?"*): an affirmative answer means the control exists, so risk is
  **low**. The raw yes/no axis (yes = 5, no = 1) is inverted to `6 − raw`.
- **Risk when present** (hazard level, e.g. *"Is there single-source
  dependency?"*): an affirmative / high answer means risk is **high**. The raw
  axis is used directly.

## 2. Composite severity

The four scaled inputs are averaged and normalised to `0–1`:

```
base     = (Response + L + I + D) / 4          # 1..5
severity = (base - 1) / 4                       # 0..1
```

## 3. Weighting

Each indicator carries a weight that reflects how much it matters in context:

```
weight = domain_weight × nature_modifier × indicator_base_weight
```

- **domain_weight** is activity-dependent (e.g. supplier selection raises the
  supply-chain domain weight).
- **nature_modifier** weights structural/governance risks above purely technical
  ones.
- **indicator_base_weight** is the indicator's intrinsic importance.

The indicator's weighted contribution is `severity × weight`.

## 4. Domain risk index (0–100)

A domain's index is the **weight-normalised mean** of its indicators'
severities, scaled to 0–100:

```
index = 100 × Σ(severity_i × weight_i) / Σ(weight_i)
```

Because it is normalised by the total weight, the index is always in
`[0, 100]` regardless of how many indicators a domain has or how large their
weights are. A domain of all-worst-case indicators scores 100; all-best scores
0. The same formula produces the category-level indices.

## 5. Classification

Each domain index is classified against two thresholds (defaults shown):

| Index | Level | Decision |
| --- | --- | --- |
| `< 40` | acceptable | proceed |
| `40 – <70` | action_required | revise |
| `≥ 70` | escalation_required | escalate |

The overall decision is the most severe domain decision.
