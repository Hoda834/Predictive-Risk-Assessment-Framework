from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Defaults:
    likelihood_scale_min: int = 1
    likelihood_scale_max: int = 5
    impact_scale_min: int = 1
    impact_scale_max: int = 5
    detectability_scale_min: int = 1
    detectability_scale_max: int = 5

    # Thresholds on the 0..100 domain risk index produced by the aggregator.
    #   index <  low_threshold                     -> acceptable
    #   low_threshold <= index < high_threshold     -> action_required
    #   index >= high_threshold                     -> escalation_required
    low_threshold: float = 40.0
    high_threshold: float = 70.0

    # ISO 14971 §4.4 requires documented risk-acceptability criteria. The bands
    # above are the framework's *default* criteria; they are a design-stage
    # governance policy, not a validated clinical threshold. See
    # docs/iso/scoring_method.md and docs/iso/risk_management_approach.md for the
    # rationale, and override them per project once product-specific harm
    # analysis exists.

    default_domain_weights: Dict[str, float] = None
    default_nature_weights: Dict[str, float] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "default_domain_weights", self.default_domain_weights or {})
        object.__setattr__(self, "default_nature_weights", self.default_nature_weights or {})
        # Fail fast on a misconfigured acceptability policy rather than silently
        # inverting every classification.
        from .validation import validate_thresholds

        validate_thresholds(self.low_threshold, self.high_threshold)
