from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class AllowedAnswerType(str, Enum):
    YES_NO = "yes_no"
    LOW_MED_HIGH = "low_med_high"
    SCALE_1_5 = "scale_1_5"


@dataclass(frozen=True)
class WeightSet:
    domain: Dict[str, float]
    nature: Dict[str, float]
    indicator: Dict[str, float]
