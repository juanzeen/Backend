from typing import TypedDict, Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict

PyObjectId = Annotated[int, BeforeValidator(int)]
1


class Record(TypedDict):
    wins: Optional[int]
    losses: Optional[int]
    win_pct: Optional[float]


class PowerRanking(TypedDict):
    rank: Optional[int]
    tier: Optional[str]
    power_score: Optional[float]
    trend: Optional[str]


class Metrics(TypedDict, total=False):
    pace: Optional[float]
    offensive_rating: Optional[float]
    defensive_rating: Optional[float]
    net_rating: Optional[float]
    pts_per_game: Optional[float]
    pts_allowed_per_game: Optional[float]
    ast_per_game: Optional[float]
    ast_allowed_per_game: Optional[float]
    reb_per_game: Optional[float]
    reb_allowed_per_game: Optional[float]
    dreb_per_game: Optional[float]
    dreb_allowed_per_game: Optional[float]
    oreb_per_game: Optional[float]
    oreb_allowed_per_game: Optional[float]
    stl_per_game: Optional[float]
    stl_allowed_per_game: Optional[float]
    blk_per_game: Optional[float]
    blk_allowed_per_game: Optional[float]


class SeasonStats(TypedDict):
    rank: Optional[int]
    record: Record
    power_ranking: PowerRanking
    metrics: Metrics


# Type aliases for alternative naming conventions
TeamRecord = Record
TeamPowerRanking = PowerRanking
TeamMetrics = Metrics
TeamSeason = SeasonStats


class Team(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId = Field(default=None, alias="_id")
    abbreviation: str
    name: str
    city: str
    conference: str
    division: str
    founded_in: int
    championships: int
    last_season: SeasonStats
    actual_season: SeasonStats
