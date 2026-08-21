# Design decisions

Architecture Decision Records (ADRs) for PRAF. Each records what was decided,
why, and what was consciously traded away. Newer entries supersede older ones
only where they say so.

---

## ADR-001 · Averaged four-axis index, backstopped by a severity guard

**Decision.** The domain index is a weight-normalised mean of four 1–5 axes
(response, likelihood, impact, detectability), and a separate severity guard
raises a domain's band when any single indicator reaches catastrophic impact
(impact = 5), regardless of the average.

**Why.** The mean gives a smooth, explainable 0–100 ranking for triage. But a
mean can dilute a catastrophic hazard below the action threshold, which
violates the ISO 14971 principle that severity of harm drives risk. Rather than
switching to a multiplicative RPN (which has its own well-documented rank
pathologies), the mean is kept for ranking and an explicit, auditable override
supplies the severity floor. The guard can only ever raise a level.

**Trade-off.** Two mechanisms instead of one formula; every guard override is
recorded in the report to keep that legible.

## ADR-002 · Missing inputs score neutral but are loudly reported

**Decision.** A missing answer or axis value is scored with the neutral value 3
so a partial questionnaire still produces a result — but every gap is recorded
per indicator, aggregated into an `input_completeness` block, and warned about
on stderr by the CLI.

**Why.** Failing hard on the first missing value makes iterative, early-stage
use impossible. Defaulting to worst-case (5) makes an empty file escalate,
which trains users to ignore escalations. Neutral-plus-visible-flag keeps the
tool usable while making it impossible for a blank assessment to masquerade as
a complete one.

**Trade-off.** A consumer that ignores `input_completeness` can still over-read
an incomplete result; the CLI warning mitigates this.

## ADR-003 · Domain weight applied after normalisation

**Decision.** The activity-dependent domain weight multiplies the normalised
0–100 base index (capped at 100) instead of entering the per-indicator weights.

**Why.** It is constant across a domain's indicators, so inside the normalised
mean it cancels out exactly and has no effect — the "context-aware weighting"
would be dead code. Applying it after normalisation makes activity context
genuinely able to shift a classification.

## ADR-004 · Acceptability thresholds are governance defaults, validated at load

**Decision.** The 40/70 bands are explicit, documented defaults on `Defaults`,
rejected at construction if inverted, and recorded in every report.

**Why.** ISO 14971 requires documented acceptability criteria. PRAF cannot ship
clinically derived thresholds for an unknown product, so it ships governance
defaults and makes them visible, overridable, and impossible to misconfigure
silently.

## ADR-005 · Timestamps are injectable, and the example output is a golden file

**Decision.** `generated_at` can be pinned via API and CLI. The example output
is generated with a pinned timestamp, tracked in git, and asserted against a
fresh run in CI.

**Why.** An audit record needs a real timestamp; a regression reference needs
determinism. Injection provides both without a hidden clock dependency: scoring
drift now fails a test instead of slipping into history unnoticed.

## ADR-006 · Controls model with three statuses; only implemented/verified count

**Decision.** Risk controls declare which indicators they address and reduce
the scaled likelihood/detectability axes by integer steps (floored at 1).
`planned` controls are carried in the report but have no numeric effect;
`implemented` controls apply but are flagged unverified; `verified` controls
apply cleanly.

**Why.** Residual risk must not be claimable from intentions. Keeping planned
controls visible-but-inert lets teams model their roadmap without borrowing
credit from it, and flagging unverified controls shows a reviewer exactly how
much of the residual case rests on unverified measures.

## ADR-007 · Controls cannot reduce impact

**Decision.** A control's effect is limited to likelihood and detectability;
the impact axis is never modified by a control annotation.

**Why.** Under ISO 14971, severity of harm is normally reduced only by changing
the design itself. In this model a design change means re-answering the
assessment (new inputs), not annotating the old one. This keeps residual-risk
claims conservative — and it is why the severity guard still holds on residual
risk: you cannot buy off a catastrophic-impact hazard with a monitoring control.

## ADR-008 · One-at-a-time ±1 sensitivity, not probabilistic simulation

**Decision.** Uncertainty analysis perturbs each effective L/I/D value by ±1
(clamped), re-runs the full residual classification, and reports every band or
decision flip; domains that flip are named "fragile".

**Why.** The inputs are coarse expert judgements — ±1 is their honest error
bar. OAT is cheap (≤ 6 runs per indicator), fully deterministic, and each
reported flip names the exact input responsible, which is what makes the
result actionable at a design review. A Monte-Carlo layer would add
distributional assumptions the input data cannot support.

**Trade-off.** Joint perturbations (two inputs moving together) are not
explored; a classification can be OAT-stable but fragile to correlated error.
The method string in the report states the scope explicitly.

## ADR-009 · Core engine has zero runtime dependencies

**Decision.** `praf` installs with no third-party dependencies; streamlit lives
behind the optional `[app]` extra, pytest behind `[dev]`.

**Why.** A scoring library whose output may be filed in a quality record should
have the smallest reviewable surface possible. The web stack is an interface
concern, not an engine concern.
