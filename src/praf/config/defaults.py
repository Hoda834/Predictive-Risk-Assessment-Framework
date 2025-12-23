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

    low_threshold: float = 20.0
    high_threshold: float = 45.0

    default_domain_weights: Dict[str, float] = None
    default_nature_weights: Dict[str, float] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "default_domain_weights", self.default_domain_weights or {})
        object.__setattr__(self, "default_nature_weights", self.default_nature_weights or {})
