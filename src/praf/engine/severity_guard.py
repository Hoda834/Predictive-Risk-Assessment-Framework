"""High-severity safeguard for the domain classification.

Motivation (ISO 14971). The domain index produced by the aggregator is a
weighted *mean* of four axes (response, likelihood, impact, detectability), each
contributing 25%. That is a useful aggregate ranking, but on its own it violates
a core principle of ISO 14971: risk is driven by **severity of harm**, and a
single catastrophic-severity hazard must not be diluted to "acceptable" just
because it sits among many low-scoring indicators or has a low likelihood.

This module applies an explicit, documented safeguard *after* classification: it
scans the individual indicators and, when one crosses a severity trigger, raises
(never lowers) the affected domain's classification level. Every override is
recorded so the reason is fully traceable in the audit trail.

This is intentionally additive to the averaged index rather than a rewrite of
the scoring maths: the index still drives the normal case, and the guard is the
minimum-severity backstop the averaged model lacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from praf.engine.classifier import DomainClassification, RiskLevel
from praf.domain.domains import RiskDomain


# Trigger thresholds on the scaled 1..5 axes. A catastrophic-impact hazard that
# is also likely to occur is escalated; a catastrophic-impact hazard on its own
# is, at minimum, flagged for action. These are governance defaults with the
# same status as the acceptability thresholds (see docs/iso/scoring_method.md);
# override per project once product-specific harm analysis exists.
CRITICAL_IMPACT = 5.0
HIGH_LIKELIHOOD = 4.0

_LEVEL_ORDER = {
    RiskLevel.ACCEPTABLE: 0,
    RiskLevel.ACTION_REQUIRED: 1,
    RiskLevel.ESCALATION_REQUIRED: 2,
}


@dataclass(frozen=True)
class SeverityOverride:
    domain: RiskDomain
    indicator_id: str
    impact: float
    likelihood: float
    from_level: RiskLevel
    to_level: RiskLevel
    reason: str


@dataclass(frozen=True)
class SeverityGuardResult:
    classifications: Dict[RiskDomain, DomainClassification]
    overrides: List[SeverityOverride]

    @property
    def triggered(self) -> bool:
        return bool(self.overrides)


def _max_level(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    return a if _LEVEL_ORDER[a] >= _LEVEL_ORDER[b] else b


def apply_severity_guard(
    classifications: Dict[RiskDomain, DomainClassification],
    indicator_details: Dict[str, Dict[str, Any]],
    *,
    critical_impact: float = CRITICAL_IMPACT,
    high_likelihood: float = HIGH_LIKELIHOOD,
) -> SeverityGuardResult:
    """Raise domain levels where an individual hazard's severity demands it.

    Returns a new classifications mapping (never mutates the input) plus a list
    of every override applied, for the audit trail.
    """
    # Required minimum level per domain, driven by the worst single indicator.
    required: Dict[RiskDomain, RiskLevel] = {}
    reasons: Dict[RiskDomain, SeverityOverride] = {}

    for indicator_id, meta in indicator_details.items():
        scaled = meta.get("scaled", {})
        impact = float(scaled.get("impact", 0.0))
        likelihood = float(scaled.get("likelihood", 0.0))
        domain = RiskDomain(meta["domain"])

        if impact >= critical_impact and likelihood >= high_likelihood:
            target = RiskLevel.ESCALATION_REQUIRED
            reason = (
                "catastrophic impact with high likelihood "
                f"(impact={impact:g}, likelihood={likelihood:g})"
            )
        elif impact >= critical_impact:
            target = RiskLevel.ACTION_REQUIRED
            reason = f"catastrophic impact (impact={impact:g})"
        else:
            continue

        current_required = required.get(domain, RiskLevel.ACCEPTABLE)
        if _LEVEL_ORDER[target] > _LEVEL_ORDER[current_required]:
            required[domain] = target
            reasons[domain] = SeverityOverride(
                domain=domain,
                indicator_id=indicator_id,
                impact=impact,
                likelihood=likelihood,
                from_level=classifications[domain].level if domain in classifications else RiskLevel.ACCEPTABLE,
                to_level=target,
                reason=reason,
            )

    new_classifications: Dict[RiskDomain, DomainClassification] = {}
    overrides: List[SeverityOverride] = []

    for domain, c in classifications.items():
        target = required.get(domain, c.level)
        upgraded = _max_level(c.level, target)
        if upgraded != c.level:
            override = reasons[domain]
            overrides.append(
                SeverityOverride(
                    domain=domain,
                    indicator_id=override.indicator_id,
                    impact=override.impact,
                    likelihood=override.likelihood,
                    from_level=c.level,
                    to_level=upgraded,
                    reason=override.reason,
                )
            )
            new_classifications[domain] = DomainClassification(
                domain=domain, score=c.score, level=upgraded
            )
        else:
            new_classifications[domain] = c

    return SeverityGuardResult(classifications=new_classifications, overrides=overrides)
