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

## 3. Within-domain weighting

Two weights vary *between* indicators of the same domain and so shape the
domain's aggregate:

```
w = nature_modifier × indicator_base_weight
```

- **nature_modifier** weights structural/governance risks above purely technical
  ones.
- **indicator_base_weight** is the indicator's intrinsic importance.

The indicator's weighted contribution is `severity × w`.

The **domain_weight** is deliberately *not* included here — it is constant
across every indicator in a domain and is applied later (step 5), because a
constant factor would cancel out of the normalised mean below and have no
effect.

## 4. Base domain index (0–100)

A domain's base index is the **weight-normalised mean** of its indicators'
severities, scaled to 0–100:

```
base_index = 100 × Σ(severity_i × w_i) / Σ(w_i)
```

Because it is normalised by the total weight, the index is always in
`[0, 100]` regardless of how many indicators a domain has or how large their
weights are. A domain of all-worst-case indicators scores 100; all-best scores
0. The same formula produces the category-level base indices.

## 4b. Context-aware domain weighting

The **domain_weight** is activity-dependent: the selected activity raises the
weight of the domains it emphasises (e.g. *supplier selection* raises the
supply-chain domain weight to 1.35, *regulatory preparation* raises regulatory
compliance to 1.40). It is applied as a sensitivity multiplier on the base
index and capped at 100:

```
index = min(100, base_index × domain_weight)
```

This means the same answers produce a higher risk index — and can cross into a
higher classification band — for the domains an activity makes most relevant.
Weights ≥ 1 only ever raise sensitivity; they never suppress risk.

## 5. Classification

Each domain index is classified against two thresholds (defaults shown):

| Index | Level | Decision |
| --- | --- | --- |
| `< 40` | acceptable | proceed |
| `40 – <70` | action_required | revise |
| `≥ 70` | escalation_required | escalate |

## 6. Input validation

Supplied input is validated before scoring. Values that were provided but
cannot be interpreted fail loudly instead of being silently coerced:

- Unknown indicator ids are rejected.
- Likelihood / impact / detectability values outside `1..5` are rejected.
- A response that does not match its indicator's answer type (e.g. a number for
  a yes/no question) is rejected.
- Unknown `activity` / `stage` values are rejected with the list of valid
  options.

All problems are reported together. A *missing* answer is not an error — it is
handled as reduced coverage (below).

## 7. Coverage and insufficient data

An indicator counts as **answered** only if the user supplied its response. A
domain's **coverage** is the fraction of its indicators that were answered:

```
coverage = answered_indicators / total_indicators
```

If a domain's coverage is below `coverage_threshold` (default 0.5), the domain
is reported as **insufficient_data** instead of a risk level, and its decision
is **gather_data**. This keeps "we don't have enough input to judge" distinct
from "the risk is medium".

## 8. Overall decision

The overall decision is the most severe per-domain decision, by the precedence:

```
escalate  >  gather_data  >  revise  >  proceed
```

A genuine escalation from a well-covered domain still wins, but insufficient
coverage outranks a routine `revise` so an unreliable verdict is never quietly
downgraded.
