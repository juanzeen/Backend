from pydantic import BaseModel, BeforeValidator, Field
from typing import TypedDict, Annotated

PyObjectId = Annotated[int, BeforeValidator(int)]


class SeasonAverageStat(TypedDict):
    season: str
    value: float


class CareerPeaks(TypedDict):
    max_ppg: SeasonAverageStat
    max_apg: SeasonAverageStat
    max_rpg: SeasonAverageStat
    max_bpg: SeasonAverageStat
    max_spg: SeasonAverageStat


class CareerTotals(TypedDict):
    games_played: int
    pts: int
    ast: int
    reb: int
    stl: int
    blk: int


class Honors(TypedDict):
    all_stars: int
    mvps: int
    finals_mvps: int
    championships: int


class Season(TypedDict):
    season_year: str
    team: str
    games_played: int
    pts_avg: float
    ast_avg: float
    reb_avg: float
    blk_avg: float
    stl_avg: float


class HistoricalPlayer(BaseModel):
    id: PyObjectId = Field(default=None, alias="_id")
    full_name: str
    slug: str
    country: str
    position: str
    height: int
    career_span: str
    is_active: bool
    career_peaks: CareerPeaks
    career_totals: CareerTotals
    honors: Honors
    seasons: list[Season]
