import math
import json
import os
import time
import dotenv
import pandas as pd
import numpy as np
from pymongo import MongoClient
from nba_api.stats.endpoints import playercareerstats, playergamelog, commonplayerinfo
from nba_api.stats.static import teams
from datetime import datetime


def convert_to_cm(fi: str) -> float:
    feet, inch = fi.split("-")
    height_cm = round((int(feet) * 30.48) + (int(inch) * 2.54))
    return height_cm


def calculate_age(birthdate: str) -> int:
    birthdate = datetime.fromisoformat(birthdate)
    today = datetime.now().date()
    return (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )


def get_db_collection(collection_name: str):
    """Initialize and return a MongoDB collection using environment variables."""
    dotenv.load_dotenv()
    db_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DATABASE_NAME", "nba_fantastic")
    client = MongoClient(db_url)
    db = client[db_name]
    return db[collection_name]


def clean_float(val, default: float = 0.0, decimals: int = 1) -> float:
    """Safely convert any value to float rounded to specified decimals, handling NaNs/Infs."""
    if val is None or pd.isna(val):
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return round(f, decimals) if decimals is not None else f
    except ValueError, TypeError:
        return default


def clean_int(val, default: int = 0) -> int:
    """Safely convert any value to integer, handling NaNs and floats."""
    if val is None or pd.isna(val):
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return int(f)
    except ValueError, TypeError:
        return default


def clean_str(val, default: str = "") -> str:
    """Safely convert any value to trimmed string, handling NaNs."""
    if val is None or pd.isna(val):
        return default
    s = str(val).strip()
    return default if s.lower() == "nan" else s


def build_season_dict(
    season_year,
    team,
    games_played,
    pts,
    ast,
    reb,
    blk,
    stl,
) -> dict:
    """Format season record into the standard fix_seasons_structure format."""
    return {
        "season_year": clean_str(season_year, default="Unknown"),
        "team": clean_str(team, default="UNK"),
        "games_played": clean_int(games_played, default=0),
        "pts_avg": clean_float(pts, default=0.0, decimals=1),
        "ast_avg": clean_float(ast, default=0.0, decimals=1),
        "reb_avg": clean_float(reb, default=0.0, decimals=1),
        "blk_avg": clean_float(blk, default=0.0, decimals=1),
        "stl_avg": clean_float(stl, default=0.0, decimals=1),
    }


def normalize_season_item(season_item: dict) -> dict:
    """Convert and clean a season entry (legacy nested or flat) into standard format."""
    if not isinstance(season_item, dict):
        return build_season_dict("Unknown", "UNK", 0, 0, 0, 0, 0, 0)

    # Legacy nested format: {"1990-91": {"team": "CHI", "games_played": 82, ...}}
    if len(season_item.keys()) == 1 and "season_year" not in season_item:
        season_year = list(season_item.keys())[0]
        data = season_item[season_year]
        if not isinstance(data, dict):
            data = {}
    else:
        season_year = season_item.get("season_year", "Unknown")
        data = season_item

    team = data.get("team", "UNK")
    games_played = data.get("games_played", 0)

    averages = data.get("averages")
    if isinstance(averages, dict):
        pts = averages.get(
            "pts", averages.get("pts_avg", data.get("pts_avg", data.get("pts", 0)))
        )
        ast = averages.get(
            "ast", averages.get("ast_avg", data.get("ast_avg", data.get("ast", 0)))
        )
        reb = averages.get(
            "reb", averages.get("reb_avg", data.get("reb_avg", data.get("reb", 0)))
        )
        blk = averages.get(
            "blk", averages.get("blk_avg", data.get("blk_avg", data.get("blk", 0)))
        )
        stl = averages.get(
            "stl", averages.get("stl_avg", data.get("stl_avg", data.get("stl", 0)))
        )
    else:
        pts = data.get("pts_avg", data.get("pts", 0))
        ast = data.get("ast_avg", data.get("ast", 0))
        reb = data.get("reb_avg", data.get("reb", 0))
        blk = data.get("blk_avg", data.get("blk", 0))
        stl = data.get("stl_avg", data.get("stl", 0))

    return build_season_dict(
        season_year=season_year,
        team=team,
        games_played=games_played,
        pts=pts,
        ast=ast,
        reb=reb,
        blk=blk,
        stl=stl,
    )


def populate_historical_players():
    """Populate base historical player profiles from CSV into MongoDB."""
    file_path = "nba_legends.csv"

    if not os.path.exists(file_path):
        print("CSV file not found!")
        return
    collection = get_db_collection("historical_players")

    df_legends = pd.read_csv(file_path)
    print(
        f"Starting migration of {len(df_legends)} legends to MongoDB ({file_path})..."
    )

    for _, row in df_legends.iterrows():
        player_id = clean_int(row.get("Player ID"))
        if not player_id:
            continue
        full_name = clean_str(row.get("Full Name"))

        try:
            document = {
                "_id": player_id,
                "full_name": full_name,
                "slug": clean_str(row.get("Player Slug")),
                "country": clean_str(row.get("Country")),
                "position": clean_str(row.get("Position"), default="UNK"),
                "height": clean_str(row.get("Height")),
                "is_active": False,
                "career_span": clean_str(row.get("Career Span")),
                "career_totals": {
                    "games_played": clean_int(row.get("Total Games")),
                    "pts": clean_int(row.get("Total Points")),
                    "ast": clean_int(row.get("Total Assists")),
                    "reb": clean_int(row.get("Total Rebounds")),
                    "blk": clean_int(row.get("Total Blocks")),
                    "stl": clean_int(row.get("Total Steals")),
                },
                "career_peaks": {
                    "max_ppg": {
                        "value": clean_float(row.get("Peak PPG")),
                        "season": clean_str(row.get("Peak PPG Season")),
                    },
                    "max_apg": {
                        "value": clean_float(row.get("Peak APG")),
                        "season": clean_str(row.get("Peak APG Season")),
                    },
                    "max_rpg": {
                        "value": clean_float(row.get("Peak RPG")),
                        "season": clean_str(row.get("Peak RPG Season")),
                    },
                    "max_bpg": {
                        "value": clean_float(row.get("Peak BPG")),
                        "season": clean_str(row.get("Peak BPG Season")),
                    },
                    "max_spg": {
                        "value": clean_float(row.get("Peak SPG")),
                        "season": clean_str(row.get("Peak SPG Season")),
                    },
                },
                "honors": {
                    "mvps": clean_int(row.get("MVPs")),
                    "finals_mvps": clean_int(row.get("Finals MVPs")),
                    "all_stars": clean_int(row.get("All-Star Appearances")),
                },
            }

            collection.update_one(
                {"_id": player_id},
                {
                    "$set": document,
                    "$setOnInsert": {"seasons": []},
                },
                upsert=True,
            )

            print(f"Document saved in MongoDB: {full_name} (ID: {player_id})")

        except Exception as e:
            print(f"Error processing {full_name} for MongoDB: {e}")
            continue


def populate_historical_players_seasons():
    """Fetch season-by-season stats from NBA API for each legend and save formatted seasons."""
    file_path = "nba_legends.csv"

    if not os.path.exists(file_path):
        print("CSV file not found!")
        return
    collection = get_db_collection("historical_players")

    df_legends = pd.read_csv(file_path)
    players = df_legends["Player ID"].dropna().unique().tolist()
    print(f"Starting season updates for {len(players)} players...")

    for player_id in players:
        player_id = clean_int(player_id)
        if not player_id:
            continue

        try:
            player_info = playercareerstats.PlayerCareerStats(
                player_id=player_id
            ).get_data_frames()[0]
            seasons = []

            if not player_info.empty:
                for _, row in player_info.iterrows():
                    gp = clean_int(row.get("GP"), default=0)
                    pts = (
                        (row["PTS"] / gp)
                        if gp > 0 and "PTS" in row and pd.notna(row["PTS"])
                        else 0.0
                    )
                    ast = (
                        (row["AST"] / gp)
                        if gp > 0 and "AST" in row and pd.notna(row["AST"])
                        else 0.0
                    )
                    reb = (
                        (row["REB"] / gp)
                        if gp > 0 and "REB" in row and pd.notna(row["REB"])
                        else 0.0
                    )
                    blk = (
                        (row["BLK"] / gp)
                        if gp > 0 and "BLK" in row and pd.notna(row["BLK"])
                        else 0.0
                    )
                    stl = (
                        (row["STL"] / gp)
                        if gp > 0 and "STL" in row and pd.notna(row["STL"])
                        else 0.0
                    )

                    season_data = build_season_dict(
                        season_year=row.get("SEASON_ID"),
                        team=row.get("TEAM_ABBREVIATION"),
                        games_played=gp,
                        pts=pts,
                        ast=ast,
                        reb=reb,
                        blk=blk,
                        stl=stl,
                    )
                    seasons.append(season_data)

            collection.update_one(
                {"_id": player_id},
                {"$set": {"seasons": seasons}},
                upsert=True,
            )
            print(
                f"Seasons for player {player_id} successfully updated in MongoDB ({len(seasons)} seasons)."
            )
            time.sleep(1)

        except Exception as e:
            print(f"Error exporting seasons for player {player_id}: {e}")


def fix_seasons_structure():
    """Correct and clean the seasons array across all historical player records in MongoDB."""
    collection = get_db_collection("historical_players")
    print("Starting correction and cleanup of 'seasons' array...")

    players = collection.find({})
    updated_count = 0

    for player in players:
        player_id = player.get("_id")
        old_seasons = player.get("seasons", [])
        if not isinstance(old_seasons, list):
            old_seasons = []

        new_seasons = [
            normalize_season_item(season_item) for season_item in old_seasons
        ]

        collection.update_one({"_id": player_id}, {"$set": {"seasons": new_seasons}})
        updated_count += 1

    print(
        f"\nSuccess! {updated_count} players had their seasons corrected and cleaned of NaN values."
    )


def populate_historical_records():
    collection = get_db_collection("historical_records")

    csv = "historical_records.csv"
    if not os.path.exists(csv):
        print("CSV not found")
        return
    df_records = pd.read_csv(csv).replace({np.nan: None})

    for _, row in df_records.iterrows():
        category = row.get("category")
        try:
            document = {
                "record": category,
                "value": row.get("value"),
                "leader_id": row.get("leader_id"),
                "leader_full_name": row.get("leader_full_name"),
                "is_active": True if row.get("active") == "Y" else False,
                "details": {
                    "season": row.get("season", None),
                    "team": row.get("team", None),
                },
            }
            collection.update_one({"record": category}, {"$set": document}, upsert=True)
            print(f"Document for the record {category} was successfully inserted")
        except Exception as e:
            print(f"Errow while trying to populate the db {e}")
    return


def populate_nba_players():
    file_path = "nba_players.csv"
    if not os.path.exists(file_path):
        print("CSV file not found!")
        return
    collection = get_db_collection("players")
    nba_players = pd.read_csv(file_path).replace({np.nan: None})
    print(
        f"Starting migration of {len(nba_players)} players to MongoDB ({file_path})..."
    )

    for _, row in nba_players.iterrows():
        player_id = clean_int(row.get("ID"))
        if not player_id:
            continue
        full_name = clean_str(row.get("Full Name"))
        print(f"Adding player {full_name} with _id: {player_id}")
        p_slug = row.get("Player Slug")
        p_pos = row.get("Position")
        p_country = row.get("Country")
        career_span = clean_str(row.get("Career Span"))
        p_height = row.get("Height")
        team_abb = row.get("Team Abbreviation")
        team_full_name = row.get("Team Full Name")
        total_games = row.get("Total Games")
        total_points = row.get("Total Points")
        total_assists = row.get("Total Assists")
        total_rebounds = row.get("Total Rebounds")
        total_blocks = row.get("Total Blocks")
        total_steals = row.get("Total Steals")
        avg_points = row.get("Avg Points")
        avg_assists = row.get("Avg Assists")
        avg_rebounds = row.get("Avg Rebounds")
        avg_steals = row.get("Avg Steals")
        avg_blocks = row.get("Avg Blocks")
        document = {
            "_id": player_id,
            "full_name": full_name,
            "slug": p_slug,
            "position": p_pos,
            "country": p_country,
            "height": p_height,
            "career_span": career_span,
            "team": {"abbreviation": team_abb, "name": team_full_name},
            "career": {
                "totals": {
                    "games": total_games,
                    "points": total_points,
                    "assists": total_assists,
                    "rebounds": total_rebounds,
                    "blocks": total_blocks,
                    "steals": total_steals,
                },
                "avg": {
                    "points": avg_points,
                    "assists": avg_assists,
                    "rebounds": avg_rebounds,
                    "blocks": avg_blocks,
                    "steals": avg_steals,
                },
            },
            "season": {
                "totals": {
                    "games": None,
                    "points": None,
                    "assists": None,
                    "rebounds": None,
                    "blocks": None,
                    "steals": None,
                },
                "avg": {
                    "points": None,
                    "assists": None,
                    "rebounds": None,
                    "blocks": None,
                    "steals": None,
                },
            },
        }
        collection.update_one({"_id": player_id}, {"$set": document}, upsert=True)


def extract_player_season(
    player_id: int, season_year: str, is_playoffs: bool = False
) -> dict | None:
    """
    Fetch all games for a specific player in a given season using PlayerGameLog,
    and format the data matching the player_seasons collection schema.
    """
    season_type = "Playoffs" if is_playoffs else "Regular Season"

    try:
        print(f"Trying to get logs for player {player_id}")
        log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season_year,
            season_type_all_star=season_type,
            timeout=30,
        )
        df = log.get_data_frames()[0]
    except Exception as e:
        print(f"Error fetching game logs for player {player_id} ({season_year}): {e}")
        return None

    if df.empty:
        print(
            f"No games found for player {player_id} in {season_year} ({season_type})."
        )
        return None

    df["formatted_date"] = pd.to_datetime(
        df["GAME_DATE"], format="%b %d, %Y"
    ).dt.strftime("%Y-%m-%d")
    df["is_home"] = df["MATCHUP"].str.contains("vs.")
    df["opponent"] = df["MATCHUP"].apply(lambda x: x.split()[-1])
    df["team_abbr"] = df["MATCHUP"].apply(lambda x: x.split()[0])

    primary_team_abbr = df["team_abbr"].mode()[0]
    team_data = teams.find_team_by_abbreviation(primary_team_abbr)
    team_dict = {
        "abbreviation": primary_team_abbr,
        "name": team_data["full_name"] if team_data else primary_team_abbr,
    }

    gp = len(df)
    totals = {
        "games_played": gp,
        "pts": int(df["PTS"].sum()),
        "ast": int(df["AST"].sum()),
        "reb": int(df["REB"].sum()),
        "stl": int(df["STL"].sum()),
        "blk": int(df["BLK"].sum()),
    }

    averages = {
        "pts": round(totals["pts"] / gp, 1) if gp > 0 else 0.0,
        "ast": round(totals["ast"] / gp, 1) if gp > 0 else 0.0,
        "reb": round(totals["reb"] / gp, 1) if gp > 0 else 0.0,
        "stl": round(totals["stl"] / gp, 1) if gp > 0 else 0.0,
        "blk": round(totals["blk"] / gp, 1) if gp > 0 else 0.0,
    }

    def get_peak(stat_col):
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

    peaks = {
        "max_pts": get_peak("PTS"),
        "max_ast": get_peak("AST"),
        "max_reb": get_peak("REB"),
        "max_stl": get_peak("STL"),
        "max_blk": get_peak("BLK"),
    }

    perf_vs_teams = []
    for opp, group in df.groupby("opponent"):
        perf_vs_teams.append(
            {
                "team": opp,
                "games_played": len(group),
                "avg_pts": round(float(group["PTS"].mean()), 1),
                "avg_ast": round(float(group["AST"].mean()), 1),
                "avg_reb": round(float(group["REB"].mean()), 1),
                "avg_blk": round(float(group["BLK"].mean()), 1),
                "avg_stl": round(float(group["STL"].mean()), 1),
            }
        )
    perf_vs_teams.sort(key=lambda x: x["team"])

    games = []
    df_sorted = df.sort_values(by="GAME_DATE", ascending=True)
    for _, row in df_sorted.iterrows():
        games.append(
            {
                "game_id": int(row["Game_ID"]),
                "date": row["formatted_date"],
                "opponent": row["opponent"],
                "result": str(row["WL"]),
                "is_home": bool(row["is_home"]),
                "playoffs": is_playoffs,
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
        )

    return {
        "player_id": player_id,
        "season_year": season_year,
        "team": team_dict,
        "season_totals": totals,
        "season_averages": averages,
        "season_peaks": peaks,
        "performance_vs_teams": perf_vs_teams,
        "games": games,
    }


def upload_player_season(doc: dict, db):
    """Upsert a player season document into the player_seasons collection."""
    collection = db["player_seasons"]
    collection.update_one(
        {"_id": doc["_id"]},
        {"$set": doc},
        upsert=True,
    )
    print(
        f"Saved: {doc['_id']} ({doc['team']['abbreviation']}, {doc['season_totals']['games_played']} games)"
    )


def sync_player_seasons(pid: int, seasons: list[str], is_playoffs: bool = False):
    """Extract and upload seasons for multiple players with polite request pacing."""
    collection = get_db_collection("players_seasons")
    for season in seasons:
        print(f"\nProcessing Player {pid} for season {season}...")
        doc = extract_player_season(
            player_id=pid, season_year=season, is_playoffs=is_playoffs
        )
        if doc:
            collection.update_one(
                {"_id": f"{pid}_{season}"},
                {
                    "$set": doc,
                },
                upsert=True,
            )

        time.sleep(1.5)


def increment_season(a: str, b: str) -> str:
    na = int(a) + 1
    nb = int(b) + 1
    return f"{na}-{nb}"


def career_span_to_seasons_list(span: str) -> list[str]:
    start_season = span[:7]
    last_season = span[-7:]
    seasons = []
    current_season = start_season
    while current_season != last_season:
        seasons.append(current_season)
        a, b = current_season.split("-")
        current_season = increment_season(a, b)
    seasons.append(last_season)
    return seasons


def populate_player_seasons():
    df = pd.read_csv("nba_players.csv")
    pids = df["ID"].tolist()
    for pid in pids:
        player_matches = df[df["ID"].astype(str) == str(pid)]
        if player_matches.empty:
            continue
        idx = player_matches.index[0]
        career_span = df.at[idx, "Career Span"]
        seasons = career_span_to_seasons_list(career_span)
        sync_player_seasons(pid, seasons)


def populate_players_age():
    df = pd.read_csv("nba_players.csv")
    collection = get_db_collection("players")
    pids = df["ID"].tolist()
    for pid in pids:
        p_birthday = commonplayerinfo.CommonPlayerInfo(player_id=pid).get_data_frames()[
            0
        ]["BIRTHDATE"][0]
        age = calculate_age(p_birthday)
        collection.update_one(
            {"_id": pid},
            {
                "$set": {"age": age},
            },
            upsert=True,
        )
        print(f"Added age for player {pid} | {age} years old")
        time.sleep(0.5)


def populate_teams():
    col = get_db_collection("teams")
    with open("full_data_teams_v2.json", "r") as f:
        teams = json.load(f)
        col.insert_many(teams)
        f.close()


# populate_historical_records()
# populate_historical_players()
# populate_historical_players_seasons()
# populate_nba_players()
# populate_player_seasons()
# populate_players_age()
populate_teams()
