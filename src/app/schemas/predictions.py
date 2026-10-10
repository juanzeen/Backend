from pydantic import BaseModel
from typing import TypedDict


# Player Expected Data
class PlayerInfos(TypedDict):
    player_id: int
    age: int


# Season
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
    stl_range: list[float]
    blk_range: list[float]


class Params(TypedDict):
    age: int
    age_adjustment_pct: str


class SeasonPrediction(BaseModel):
    player_id: int
    full_name: str
    projected_averages: ProjectedAvg
    confidence_intervals: ConfidenceIntervals
    params: Params


# Matchup
# Opponent team average allowed values for each stat
class DefenseFactors(TypedDict):
    pts: float
    ast: float
    reb: float
    stl: float
    blk: float


class MatchFactors(TypedDict):
    pace_factor: float
    defense_factors: DefenseFactors
    is_home: bool


class MatchupPrediction(BaseModel):
    player_id: int
    full_name: str
    opponent_id: int
    opponent_name: str
    projected_averages: ProjectedAvg
    confidence_intervals: ConfidenceIntervals
    factors: MatchFactors
