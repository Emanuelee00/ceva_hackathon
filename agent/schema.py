"""Pydantic schema for the router's constrained JSON output. Kept small on
purpose: the smaller the JSON the local model must emit, the more reliable
a 3B model is at getting it right.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ToolName(str, Enum):
    EMPTY_KM_COST = "empty_km_cost"
    MATCHING_OPPORTUNITY = "matching_opportunity"
    GEO_MISMATCH = "geo_mismatch"
    FLEET_CONCENTRATION = "fleet_concentration"
    DELAY_ANALYSIS = "delay_analysis"
    LOADING_FACTOR_ALERT = "loading_factor_alert"
    OUT_OF_SCOPE = "out_of_scope"


class RouterDecision(BaseModel):
    tool: ToolName = Field(description="Which analysis to run, or out_of_scope if the question isn't about this dataset")
    top_n: int = Field(default=10, description="Number of top rows, only used by tools that rank results")
