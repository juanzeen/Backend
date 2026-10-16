import asyncio
import logging
import os
import time
import sys
from typing import Any
from nba_api.stats.endpoints import commonallplayers, commonplayerinfo
from pymongo import UpdateOne
from ..dependencies import get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

DEFAULT_SEASON = os.getenv("CURRENT_SEASON", "2026-27")


async def sync_rosters(db: Any, season: str = DEFAULT_SEASON) -> int:
    logger.info("Starting weekly roster sync for season %s...", season)
    start_time = time.time()

    all_players_df = commonallplayers.CommonAllPlayers(
        season=season, is_only_current_season=1
    ).get_data_frames()[0]
    if all_players_df.empty:
        logger.warning(
            "No players info returned for season '%s'. "
            "The regular season may not have started yet (0 games played). Skipping weekly players sync.",
            season,
        )
        return {
            "players_updated": 0,
        }
    bulk_ops = []
    for _, row in all_players_df.iterrows():
        player_id = int(row["PERSON_ID"])
        team_id = int(row["TEAM_ID"]) if row["TEAM_ID"] else None
        team_abbr = str(row["TEAM_ABBREVIATION"]) if row["TEAM_ABBREVIATION"] else ""
        team_name = str(row["TEAM_NAME"]) if row["TEAM_NAME"] else ""

        if team_id and team_abbr:
            bulk_ops.append(
                UpdateOne(
                    {"_id": player_id},
                    {
                        "$set": {
                            "team.abbreviation": team_abbr,
                            "team.name": team_name,
                        }
                    },
                    upsert=False,
                )
            )

    if bulk_ops:
        result = await db["players_cron_test"].bulk_write(bulk_ops, ordered=False)
        logger.info(
            "Roster sync updated %d players (matched: %d, modified: %d).",
            len(bulk_ops),
            result.matched_count,
            result.modified_count,
        )

    elapsed = time.time() - start_time
    logger.info("Roster sync finished in %.2f seconds.", elapsed)
    return len(bulk_ops)


async def run_weekly_sync(season: str | None = None) -> None:
    target_season = season or DEFAULT_SEASON
    logger.info("=== Starting Weekly NBA Maintenance Job [%s] ===", target_season)
    start_total = time.time()

    db = get_db()
    await sync_rosters(db=db, season=target_season)

    total_elapsed = time.time() - start_total
    logger.info("=== Weekly NBA Sync Finished in %.2f seconds ===", total_elapsed)


if __name__ == "__main__":
    asyncio.run(run_weekly_sync())
