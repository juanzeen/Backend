from pydantic import BaseModel
from typing import TypedDict


# Player Expected Data
class PlayerInfos(TypedDict):
    player_id: int
    age: int


# Year
class ProjectedAvg(TypedDict):
    pts: float
    ast: float
    reb: float
    stl: float
    blk: float


class ConfidenceIntervals(TypedDict):
    pts_range: list[float]
    ast_range: list[float]
    reb_range: list[float]


class Params(TypedDict):
    age: int
    age_adjustment_pct: str


class YearPrediction(BaseModel):
    player_id: int
    full_name: str
    target_season: str
    projected_games_played: int
    projected_averages: ProjectedAvg
    confidence_intervals: ConfidenceIntervals
    params: Params
