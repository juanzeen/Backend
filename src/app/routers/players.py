from fastapi import APIRouter, Depends, Path, HTTPException, Query
from typing import Annotated
from ..dependencies import DbDependency, RedisDependency
from ..utils.cache import get_cached_or_db
from ..utils.rate_limiter import rate_limit
from ..schemas.players import Player
from ..schemas.player_seasons import PlayerSeason
from ..schemas.base import (
    ResponseDict,
    ErrorResponseDict,
    PaginationResponse,
    PaginationParams,
)
from ..services.predictions import calculate_player_year_prediction
import math

router = APIRouter(prefix="/players", tags=["Current NBA Players"])
CURRENT_SEASON = "2026-27"


@router.get(
    "/",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Actual NBA players not found.",
        }
    },
    dependencies=[rate_limit(40, 60)],
)
async def get_nba_players(
    pagination: Annotated[PaginationParams, Query()], db: DbDependency
) -> PaginationResponse[Player] | ErrorResponseDict:
    np = db["players"]
    limit = pagination.limit
    skip = limit * (pagination.page - 1)
    total_players = await np.count_documents({})
    total_pages = math.ceil(total_players / limit)
    cursor = np.find({}).sort("_id", 1).skip(skip).limit(limit)
    players = await cursor.to_list()
    if players and len(players) > 0:
        return {
            "message": "Actual NBA players successfully retrieved.",
            "data": players,
            "pagination": {
                "page": pagination.page,
                "limit": pagination.limit,
                "total_items": total_players,
                "total_pages": total_pages,
                "has_next": pagination.page < total_pages,
                "has_previous": pagination.page > 1,
            },
        }
    raise HTTPException(
        status_code=404, detail={"message": "Actual NBA players not found."}
    )


@router.get(
    "/{id}",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Actual NBA player with id xx not found.",
        }
    },
    dependencies=[rate_limit(60, 60)],
)
async def get_nba_player_by_id(
    id: Annotated[
        int, Path(gt=10, lt=10000000, title="ID from the player who will be fetched")
    ],
    db: DbDependency,
    redis: RedisDependency,
) -> ResponseDict[Player] | ErrorResponseDict:
    np = db["players"]
    cache_key = f"players:id:{id}"
    player = await get_cached_or_db(
        redis=redis,
        cache_key=cache_key,
        fetch_from_db=np.find_one({"_id": id}),
    )
    if player:
        return {"message": "Player successfully retrieved.", "data": player}
    raise HTTPException(
        status_code=404, detail={"message": f"Player with id {id} not found."}
    )


@router.get(
    "/search/{slug}",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Actual NBA player with slug xxx-xxxx not found.",
        }
    },
    dependencies=[rate_limit(60, 60)],
)
async def get_nba_player_by_slug(
    slug: Annotated[
        str,
        Path(
            min_length=7,
            title="Slug from the player who will be fetched",
            description="Slug in the format name-lastname",
        ),
    ],
    db: DbDependency,
    redis: RedisDependency,
) -> ResponseDict[Player] | ErrorResponseDict:
    np = db["players"]
    cache_key = f"players:slug:{slug}"
    player = await get_cached_or_db(
        redis=redis,
        cache_key=cache_key,
        fetch_from_db=np.find_one({"slug": slug}),
    )
    if player:
        return {"message": "Player successfully retrieved.", "data": player}
    raise HTTPException(
        status_code=404, detail={"message": f"Player with slug {slug} not found."}
    )


# Seasons
@router.get(
    "/{player_id}/seasons",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Seasons from player with id xx not found.",
        }
    },
    dependencies=[rate_limit(20, 60)],
)
async def get_nba_player_seasons(
    player_id: Annotated[
        int, Path(gt=10, lt=10000000, title="ID from the player who will be fetched.")
    ],
    pagination: Annotated[PaginationParams, Query()],
    db: DbDependency,
) -> PaginationResponse[PlayerSeason] | ErrorResponseDict:
    ps = db["players_seasons"]
    limit = pagination.limit
    skip = limit * (pagination.page - 1)
    total_seasons = await ps.count_documents({"player_id": player_id})
    total_pages = math.ceil(total_seasons / limit)
    cursor = ps.find({"player_id": player_id}).sort("_id", 1).skip(skip).limit(limit)
    seasons = await cursor.to_list()

    if seasons and len(seasons) > 0:
        return {
            "message": f"Seasons from player with id {player_id} successfully retrieved.",
            "data": seasons,
            "pagination": {
                "page": pagination.page,
                "limit": pagination.limit,
                "total_items": total_seasons,
                "total_pages": total_pages,
                "has_next": pagination.page < total_pages,
                "has_previous": pagination.page > 1,
            },
        }

    raise HTTPException(
        status_code=404,
        detail={"message": f"Seasons from player with id {player_id} not found."},
    )


@router.get(
    "/{player_id}/seasons/{season_year}",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Season xxxx-xx from player with id xx not found.",
        }
    },
    dependencies=[rate_limit(20, 60)],
)
async def get_nba_player_season_by_year(
    player_id: Annotated[
        int, Path(gt=10, lt=10000000, title="ID from the player who will be fetched.")
    ],
    season_year: Annotated[
        str,
        Path(
            min_length=7,
            max_length=7,
            title="ID from the season which will be fetched.",
        ),
    ],
    db: DbDependency,
    redis: RedisDependency,
) -> ResponseDict[PlayerSeason] | ErrorResponseDict:
    ps = db["players_seasons"]
    ttl = 900 if season_year == CURRENT_SEASON else 86400
    cache_key = f"players:{player_id}:seasons:{season_year}"
    season = await get_cached_or_db(
        redis=redis,
        cache_key=cache_key,
        fetch_from_db=ps.find_one({"player_id": player_id, "season_year": season_year}),
        expire_seconds=ttl,
    )
    if season:
        return {
            "message": f"Season {season_year} from player with id {player_id} successfully retrieved.",
            "data": season,
        }
    raise HTTPException(
        status_code=404,
        detail={
            "message": f"Season {season_year} from player with id {player_id} not found."
        },
    )


@router.get(
    "/team/{team_abb}",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Players from team XXX not found.",
        }
    },
)
async def get_players_by_team(
    team_abb: Annotated[
        str,
        Path(
            min_length=3,
            max_length=3,
            title="Abbreviation from the team which will have players retrived",
        ),
    ],
    db: DbDependency,
    redis: RedisDependency,
) -> ResponseDict[list[Player]] | ErrorResponseDict:
    np = db["players"]
    normalized_abb = team_abb.upper()
    cache_key = f"players:team:{normalized_abb}"
    cursor = np.find({"team.abbreviation": normalized_abb}).sort("full_name", 1)
    players = await get_cached_or_db(
        redis=redis,
        cache_key=cache_key,
        fetch_from_db=cursor.to_list(),
        expire_seconds=7200,
    )
    if players and len(players) > 0:
        return {
            "message": f"Players from {normalized_abb} successfully retrieved.",
            "data": players,
        }
    raise HTTPException(
        status_code=404,
        detail={"message": f"Players from {normalized_abb} not found."},
    )

@router.get(
    "/{id}/predictions/season",
    status_code=200,
    responses={
        404: {
            "model": ErrorResponseDict,
            "description": "Actual NBA player with id xx not found.",
        }
    },
    dependencies=[rate_limit(60, 60)],
)
async def get_nba_player_year_prediction(
    id: Annotated[
        int, Path(gt=10, lt=10000000, title="ID from the player who will be fetched")
    ],
    db: DbDependency,
    redis: RedisDependency,
):
    np = db["players"]
    player = await np.find_one({"_id": id})
    if player:
        prediction_data = {"player_id": player.get("_id"), "age": player.get("age")}
        prediction = await calculate_player_year_prediction(player=prediction_data)
        return {"message": "Player prediction successfully calculated.", "data": {"prediction": prediction}}
    raise HTTPException(
        status_code=404, detail={"message": f"Player with id {id} not found."}
    )
