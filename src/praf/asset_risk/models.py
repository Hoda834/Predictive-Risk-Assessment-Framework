from dataclasses import dataclass
from typing import List


@dataclass
class Asset:
    asset_id: int
    name: str
    description: str
    owner: str
    category: str
    cia: List[str]
    personal_data: bool
    access: str


@dataclass
class Risk:
    risk_id: int
    asset_id: int
    event: str
    source: str
    cia: List[str]
    likelihood: str
    impact: str
    score: int
    suggested_treatment: str
    selected_controls: List[str]
    residual_likelihood: str
    residual_impact: str
    residual_score: int
