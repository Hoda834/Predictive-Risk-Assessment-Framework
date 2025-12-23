from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from praf.domain.decision_matrix import ControlDomain


@dataclass(frozen=True)
class UserRisk:
    risk_id: str
    description: str
    owner: str
    likelihood: int
    impact: int
    detectability: int
    mapped_domain: Optional[ControlDomain] = None

    def severity(self) -> int:
        return int(self.likelihood) + int(self.impact) + int(self.detectability)
