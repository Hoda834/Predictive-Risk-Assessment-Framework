from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Activity(str, Enum):
    PRODUCT_DESIGN = "product_design"
    PROTOTYPE_DEVELOPMENT = "prototype_development"
    MANUFACTURING_SCALE_UP = "manufacturing_scale_up"
    SUPPLIER_SELECTION = "supplier_selection"
    REGULATORY_PREPARATION = "regulatory_preparation"
    DATA_COLLECTION = "data_collection"
    SYSTEM_DESIGN = "system_design"
    PROCESS_OPTIMISATION = "process_optimisation"


class ProjectStage(str, Enum):
    CONCEPT = "concept"
    DESIGN = "design"
    PROTOTYPE = "prototype"
    PILOT = "pilot"
    SCALE_UP = "scale_up"


@dataclass(frozen=True)
class Context:
    activity: Activity
    stage: ProjectStage
