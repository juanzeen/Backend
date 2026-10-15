import asyncio
import json
import logging
import os
import time
from typing import Any
import pandas as pd
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    leaguestandingsv3,
    leaguedashplayerstats,
    playergamelogs,
)
from nba_api.stats.static import teams
from nba_api.stats.library.http import NBAStatsHTTP
from pymongo import UpdateOne
from app.dependencies import get_db, get_redis
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_SEASON = os.getenv("CURRENT_SEASON", "2025-26")

NBAStatsHTTP().headers.update(
    {
        "Origin": "https://www.nba.com",
        "Referer": "https://www.nba.com/",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }
)


# Helpers
def get_tier_by_rank(rank: int) -> str:
    if rank <= 5:
        return "Championship Contender"
    if rank <= 10:
        return "Playoff Contender"
    if rank <= 18:
        return "Play-in Contender"
    if rank <= 24:
        return "Lottery"
    return "Rebuilding"


def get_yesterday() -> str:
    today = datetime.now(ZoneInfo("America/New_York"))
    return (today - timedelta(days=1)).strftime("%Y-%m-%d")


def get_peak(df, stat_col):
    if df.empty or df[stat_col].max() == 0:
        top_row = df.iloc[0]
        val = 0
    else:
        top_row = df.loc[df[stat_col].idxmax()]
        val = int(top_row[stat_col])

    return {
        "value": val,
        "date": str(top_row["formatted_date"]),
        "opponent": str(top_row["opponent"]),
        "game_id": int(top_row["Game_ID"]),
    }


# Jobs
async def sync_teams(
    db: Any,
    redis: Any = None,
    season: str = DEFAULT_SEASON,
) -> dict[str, Any]:
    logger.info("Starting teams sync for season %s...", season)
    start_time = time.time()

    standings_df = leaguestandingsv3.LeagueStandingsV3(season=season).get_data_frames()[
        0
    ]
    stats_df = leaguedashteamstats.LeagueDashTeamStats(
        season=season, per_mode_detailed="PerGame"
    ).get_data_frames()[0]
    time.sleep(1.0)
    adv_df = leaguedashteamstats.LeagueDashTeamStats(
        measure_type_detailed_defense="Advanced", season=season
    ).get_data_frames()[0]
    time.sleep(1.0)
    opp_df = leaguedashteamstats.LeagueDashTeamStats(
        measure_type_detailed_defense="Opponent",
        per_mode_detailed="PerGame",
        season=season,
    ).get_data_frames()[0]
    standings_map = (
        standings_df.set_index("TeamID") if not standings_df.empty else pd.DataFrame()
    )
    stats_map = stats_df.set_index("TEAM_ID") if not stats_df.empty else pd.DataFrame()
    adv_map = adv_df.set_index("TEAM_ID") if not adv_df.empty else pd.DataFrame()
    opp_map = opp_df.set_index("TEAM_ID") if not opp_df.empty else pd.DataFrame()

    if adv_df.empty or opp_df.empty:
        logger.warning(
            "No team advanced/opponent stats returned for season '%s'. "
            "The regular season may not have started yet (0 games played). Skipping teams sync.",
            season,
        )
        return {
            "teams_updated": 0,
            "league_averages": {},
            "elapsed_seconds": round(time.time() - start_time, 2),
        }

    league_averages = {
        "pace": round(float(adv_df["PACE"].mean()), 1),
        "defensive_rating": round(float(adv_df["DEF_RATING"].mean()), 1),
        "pts": round(float(opp_df["OPP_PTS"].mean()), 1),
        "reb": round(float(opp_df["OPP_REB"].mean()), 1),
        "ast": round(float(opp_df["OPP_AST"].mean()), 1),
        "stl": round(float(opp_df["OPP_STL"].mean()), 1),
        "blk": round(float(opp_df["OPP_BLK"].mean()), 1),
    }

    net_ratings = adv_df["NET_RATING"].astype(float).tolist()
    min_net = min(net_ratings)
    max_net = max(net_ratings)
    net_range = max_net - min_net if max_net != min_net else 1.0

    team_data = []
    for team_id in adv_map.index:
        s_row = standings_map.loc[team_id] if team_id in standings_map.index else {}
        t_row = stats_map.loc[team_id] if team_id in stats_map.index else {}
        a_row = adv_map.loc[team_id]
        o_row = opp_map.loc[team_id]

        win_pct = float(a_row["W_PCT"])
        net_rating = float(a_row["NET_RATING"])
        norm_net = (net_rating - min_net) / net_range
        power_score = round((win_pct * 0.40 + norm_net * 0.60) * 100, 1)

        team_entry = {
            "team_id": int(team_id),
            "name": a_row["TEAM_NAME"],
            "season_rank": int(s_row.get("PlayoffRank", 0)),
            "win_pct": win_pct,
            "wins": int(a_row["W"]),
            "losses": int(a_row["L"]),
            "power_score": power_score,
            "metrics": {
                "pace": float(a_row["PACE"]),
                "offensive_rating": float(a_row["OFF_RATING"]),
                "defensive_rating": float(a_row["DEF_RATING"]),
                "net_rating": net_rating,
                "pts_per_game": float(s_row.get("PointsPG", 0.0)),
                "pts_allowed_per_game": float(o_row["OPP_PTS"]),
                "reb_per_game": float(t_row.get("REB", 0.0)),
                "reb_allowed_per_game": float(o_row["OPP_REB"]),
                "dreb_per_game": float(t_row.get("DREB")),
                "dreb_allowed_per_game": float(o_row.get("OPP_DREB")),
                "oreb_per_game": float(t_row.get("OREB")),
                "oreb_allowed_per_game": float(o_row.get("OPP_OREB")),
                "ast_per_game": float(t_row.get("AST")),
                "ast_allowed_per_game": float(o_row["OPP_AST"]),
                "stl_per_game": float(t_row.get("STL")),
                "stl_allowed_per_game": float(o_row["OPP_STL"]),
                "blk_per_game": float(t_row.get("BLK")),
                "blk_allowed_per_game": float(o_row["OPP_BLK"]),
            },
        }
        print(team_entry)
        team_data.append(team_entry)

    team_data.sort(key=lambda x: x["power_score"], reverse=True)
    bulk_ops = []

    for rank, item in enumerate(team_data, start=1):
        tier = get_tier_by_rank(rank)
        season_rank = item["season_rank"]
        trend = (
            f"+{season_rank - rank}" if season_rank > rank else str(season_rank - rank)
        )

        power_ranking_payload = {
            "rank": rank,
            "tier": tier,
            "power_score": item["power_score"],
            "trend": trend,
        }

        target_doc = {
            "actual_season.rank": season_rank,
            "actual_season.record": {
                "wins": item["wins"],
                "losses": item["losses"],
                "win_pct": item["win_pct"],
            },
            "actual_season.power_ranking": power_ranking_payload,
            "actual_season.metrics": item["metrics"],
        }
        bulk_ops.append(
            UpdateOne({"_id": item["team_id"]}, {"$set": target_doc}, upsert=True)
        )

    if bulk_ops:
        await db["teams_cron_test"].bulk_write(bulk_ops, ordered=False)
        logger.info("Updated %d teams in MongoDB collection 'teams'.", len(bulk_ops))

    if redis is not None:
        try:
            await redis.set("league_averages", json.dumps(league_averages), ex=86400)
            logger.info(
                "Pre-warmed Redis cache: 'teams:power_rankings' and 'league_averages'."
            )
        except Exception as e:
            logger.warning("Failed to pre-warm Redis cache: %s", e)

    elapsed = time.time() - start_time
    logger.info("Teams sync completed in %.2f seconds.", elapsed)
    return {
        "teams_updated": len(bulk_ops),
        "league_averages": league_averages,
        "elapsed_seconds": round(elapsed, 2),
    }


async def sync_players(
    db: Any,
    season: str = DEFAULT_SEASON,
) -> dict[str, Any]:
    date = get_yesterday()
    logger.info(
        "Starting unified players & player_seasons sync for season %s (game date: %s)...",
        season,
        date,
    )
    start_time = time.time()

    totals_df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed="Totals"
    ).get_data_frames()[0]
    per_game_df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed="PerGame"
    ).get_data_frames()[0]

    if totals_df.empty or per_game_df.empty:
        logger.warning(
            "No player stats returned for season '%s'. The regular season may not have started yet. Skipping players sync.",
            season,
        )
        return {"players_updated": 0, "seasons_updated": 0, "elapsed_seconds": 0.0}

    totals_map = totals_df.set_index("PLAYER_ID")
    per_game_map = per_game_df.set_index("PLAYER_ID")

    player_bulk_ops = []

    for _, row in totals_df.iterrows():
        player_id = int(row["PLAYER_ID"])
        gp = int(row["GP"])
        pts = int(row["PTS"])
        reb = int(row["REB"])
        ast = int(row["AST"])
        stl = int(row["STL"])
        blk = int(row["BLK"])

        avg_row = per_game_map.loc[player_id] if player_id in per_game_map.index else {}
        avg_pts = float(avg_row.get("PTS", round(pts / gp, 1) if gp > 0 else 0.0))
        avg_ast = float(avg_row.get("AST", round(ast / gp, 1) if gp > 0 else 0.0))
        avg_reb = float(avg_row.get("REB", round(reb / gp, 1) if gp > 0 else 0.0))
        avg_stl = float(avg_row.get("STL", round(stl / gp, 1) if gp > 0 else 0.0))
        avg_blk = float(avg_row.get("BLK", round(blk / gp, 1) if gp > 0 else 0.0))

        update_payload = {
            "season.totals": {
                "games": gp,
                "points": pts,
                "assists": ast,
                "rebounds": reb,
                "blocks": blk,
                "steals": stl,
            },
            "season.avg": {
                "points": round(avg_pts, 1),
                "assists": round(avg_ast, 1),
                "rebounds": round(avg_reb, 1),
                "blocks": round(avg_blk, 1),
                "steals": round(avg_stl, 1),
            },
        }
        player_bulk_ops.append(
            UpdateOne({"_id": player_id}, {"$set": update_payload}, upsert=False)
        )

    if player_bulk_ops:
        await db["players_cron_test"].bulk_write(player_bulk_ops, ordered=False)
        logger.info(
            "Updated %d players in collection '%s'.", len(player_bulk_ops), "players"
        )

    logs_df = playergamelogs.PlayerGameLogs(
        season_nullable=season,
        date_from_nullable="2025-10-22",
        date_to_nullable="2025-10-22",
    ).get_data_frames()[0]

    if logs_df.empty:
        logger.info(
            "No games played on %s. Completed player sync without season game additions.",
            date,
        )
        elapsed = time.time() - start_time
        return {
            "players_updated": len(player_bulk_ops),
            "seasons_updated": 0,
            "elapsed_seconds": round(elapsed, 2),
        }

    pids = logs_df["PLAYER_ID"].unique().tolist()
    logger.info(
        "Fetched %d game logs for %d active players on %s.",
        len(logs_df),
        len(pids),
        date,
    )

    active_season_ids = [f"{pid}_{season}" for pid in pids]
    existing_docs = (
        await db["players_seasons"]
        .find({"_id": {"$in": active_season_ids}})
        .to_list(length=None)
    )
    existing_map = {doc["_id"]: doc for doc in existing_docs}

    season_bulk_ops = []
    for pid in pids:
        season_id = f"{pid}_{season}"
        p_game_rows = logs_df[logs_df["PLAYER_ID"] == pid]

        doc = existing_map.get(season_id)
        if not doc:
            first_row = p_game_rows.iloc[0]
            matchup = str(first_row["MATCHUP"])
            team_abbr = matchup.split()[0]
            team_data = teams.find_team_by_abbreviation(team_abbr)
            team_name = (
                team_data["full_name"] if team_data else str(first_row["TEAM_NAME"])
            )

            doc = {
                "_id": season_id,
                "player_id": int(pid),
                "season_year": season,
                "team": {
                    "abbreviation": team_abbr,
                    "name": team_name,
                },
                "season_totals": {},
                "season_averages": {},
                "season_peaks": {
                    "max_pts": {"value": 0, "date": "", "opponent": "", "game_id": 0},
                    "max_ast": {"value": 0, "date": "", "opponent": "", "game_id": 0},
                    "max_reb": {"value": 0, "date": "", "opponent": "", "game_id": 0},
                    "max_stl": {"value": 0, "date": "", "opponent": "", "game_id": 0},
                    "max_blk": {"value": 0, "date": "", "opponent": "", "game_id": 0},
                },
                "performance_vs_teams": [],
                "games": [],
            }

        existing_game_ids = {g["game_id"] for g in doc.get("games", [])}

        for _, row in p_game_rows.iterrows():
            game_id = int(row["GAME_ID"])
            matchup = str(row["MATCHUP"])
            opponent = matchup.split()[-1]
            is_home = "vs." in matchup
            game_date = str(row["GAME_DATE"])

            new_game = {
                "game_id": game_id,
                "date": game_date,
                "opponent": opponent,
                "result": str(row["WL"]),
                "is_home": is_home,
                "is_playoffs": False,
                "minutes": str(row["MIN"]),
                "pts": int(row["PTS"]),
                "ast": int(row["AST"]),
                "reb": int(row["REB"]),
                "stl": int(row["STL"]),
                "blk": int(row["BLK"]),
                "fg_pct": round(float(row["FG_PCT"]), 3)
                if pd.notna(row["FG_PCT"])
                else 0.0,
                "fg3_pct": round(float(row["FG3_PCT"]), 3)
                if pd.notna(row["FG3_PCT"])
                else 0.0,
                "ft_pct": round(float(row["FT_PCT"]), 3)
                if pd.notna(row["FT_PCT"])
                else 0.0,
            }

            if game_id not in existing_game_ids:
                doc["games"].append(new_game)
                existing_game_ids.add(game_id)

            for stat in ["pts", "ast", "reb", "stl", "blk"]:
                peak_key = f"max_{stat}"
                current_peak = doc["season_peaks"].get(peak_key, {"value": 0})
                if new_game[stat] > current_peak.get("value", 0):
                    doc["season_peaks"][peak_key] = {
                        "value": new_game[stat],
                        "date": game_date,
                        "opponent": opponent,
                        "game_id": game_id,
                    }

        if pid in totals_map.index and pid in per_game_map.index:
            p_tot = totals_map.loc[pid]
            p_avg = per_game_map.loc[pid]

            doc["season_totals"] = {
                "games_played": int(p_tot["GP"]),
                "pts": int(p_tot["PTS"]),
                "ast": int(p_tot["AST"]),
                "reb": int(p_tot["REB"]),
                "stl": int(p_tot["STL"]),
                "blk": int(p_tot["BLK"]),
            }
            doc["season_averages"] = {
                "pts": round(float(p_avg["PTS"]), 1),
                "ast": round(float(p_avg["AST"]), 1),
                "reb": round(float(p_avg["REB"]), 1),
                "stl": round(float(p_avg["STL"]), 1),
                "blk": round(float(p_avg["BLK"]), 1),
            }

        games_df = pd.DataFrame(doc["games"])
        if not games_df.empty:
            perf_list = []
            for opp, group in games_df.groupby("opponent"):
                perf_list.append(
                    {
                        "team": opp,
                        "games_played": len(group),
                        "avg_pts": round(float(group["pts"].mean()), 1),
                        "avg_ast": round(float(group["ast"].mean()), 1),
                        "avg_reb": round(float(group["reb"].mean()), 1),
                        "avg_blk": round(float(group["blk"].mean()), 1),
                        "avg_stl": round(float(group["stl"].mean()), 1),
                    }
                )
            doc["performance_vs_teams"] = sorted(perf_list, key=lambda x: x["team"])

        season_bulk_ops.append(
            UpdateOne({"_id": season_id}, {"$set": doc}, upsert=True)
        )

    if season_bulk_ops:
        await db["players_seasons_cron_test"].bulk_write(season_bulk_ops, ordered=False)
        logger.info(
            "Updated %d player_seasons documents in collection '%s'.",
            len(season_bulk_ops),
            "players_seasons",
        )

    elapsed = time.time() - start_time
    logger.info(
        "Sync players and player_seasons finished in %.2f seconds (Players: %d, Seasons: %d).",
        elapsed,
        len(player_bulk_ops),
        len(season_bulk_ops),
    )
    return {
        "players_updated": len(player_bulk_ops),
        "seasons_updated": len(season_bulk_ops),
        "elapsed_seconds": round(elapsed, 2),
    }


async def run_daily_sync(season: str | None = None) -> None:
    target_season = season or DEFAULT_SEASON
    today = datetime.now(ZoneInfo("America/New_York"))
    logger.info(
        "=== Starting Daily NBA Sync Job [%s | Date: %s] ===", target_season, today
    )
    start_total = time.time()

    db = get_db()
    redis = get_redis()

    await sync_teams(db=db, redis=redis, season=target_season)
    time.sleep(1.0)

    await sync_players(db=db, season=target_season)

    total_elapsed = time.time() - start_total
    logger.info(
        "=== Daily NBA Sync Finished Successfully in %.2f seconds ===", total_elapsed
    )


if __name__ == "__main__":
    asyncio.run(run_daily_sync())
