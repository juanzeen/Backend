from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playercareerstats,
    playerawards,
    commonplayerinfo,
    alltimeleadersgrids,
    teaminfocommon,
    leaguestandingsv3,
    leaguedashteamstats,
)
import pandas as pd
import time
import csv
import os
import json


def normalize_name(name: str):
    return name.lower().replace("-", "").replace("'", "")


def is_legendary_player(
    points,
    rebs,
    asts,
    mvp_count,
    all_star_participations,
    finals_mvp_count,
    rings,
    min_games,
) -> bool:
    """
    Personal filter to set historical players only based in stats and individual awards. Filter must be improved and include players who
    win at least 1 MVP.
    """
    volume_conditions = (
        points >= 23000 or rebs >= 11500 or asts >= 7500
    ) and min_games >= 460
    peak_conditions = (
        mvp_count > 0
        or all_star_participations > 5
        or finals_mvp_count > 0
        or rings > 2
    )
    return volume_conditions or peak_conditions


def convert_to_cm(fi: str) -> float:
    feet, inch = fi.split("-")
    height_cm = round((int(feet) * 30.48) + (int(inch) * 2.54))
    return height_cm


LEGEND_HEADERS = [
    "Player ID",
    "Full Name",
    "Total Games",
    "Total Points",
    "Total Rebounds",
    "Total Assists",
    "Total Steals",
    "Total Blocks",
    "Championships",
    "MVPs",
    "Finals MVPs",
    "All-Star Appearances",
    "Peak PPG",
    "Peak PPG Season",
    "Peak RPG",
    "Peak RPG Season",
    "Peak APG",
    "Peak APG Season",
    "Peak SPG",
    "Peak SPG Season",
    "Peak BPG",
    "Peak BPG Season",
    "Total Seasons",
    "Career Span",
    "Position",
    "Player Slug",
    "Height",
    "Country",
]


def extract_career_metrics(df_career: pd.DataFrame) -> dict:
    """Extract career totals and single-season peak averages from PlayerCareerStats DataFrame."""
    if df_career.empty:
        return {}

    stat_cols = ["PTS", "REB", "AST", "GP", "STL", "BLK"]
    for col in stat_cols:
        if col not in df_career.columns:
            df_career[col] = 0
        else:
            df_career[col] = df_career[col].fillna(0)

    df_valid = df_career[df_career["GP"] > 0].copy()
    if df_valid.empty:
        return {}

    total_games = int(df_valid["GP"].sum())
    total_points = int(df_valid["PTS"].sum())
    total_rebs = int(df_valid["REB"].sum())
    total_asts = int(df_valid["AST"].sum())
    total_stl = int(df_valid["STL"].sum())
    total_blk = int(df_valid["BLK"].sum())

    total_seasons = int(df_valid["SEASON_ID"].nunique())
    career_span = f"{df_valid['SEASON_ID'].min()} - {df_valid['SEASON_ID'].max()}"

    df_valid["PPG"] = df_valid["PTS"] / df_valid["GP"]
    df_valid["RPG"] = df_valid["REB"] / df_valid["GP"]
    df_valid["APG"] = df_valid["AST"] / df_valid["GP"]
    df_valid["SPG"] = df_valid["STL"] / df_valid["GP"]
    df_valid["BPG"] = df_valid["BLK"] / df_valid["GP"]

    def get_peak_stat(col: str):
        series = df_valid[col].dropna()
        first_season = (
            str(df_valid["SEASON_ID"].iloc[0]) if not df_valid.empty else "N/A"
        )
        if series.empty or (series == 0).all():
            return 0.0, first_season
        idx = series.idxmax()
        val = series.loc[idx]
        season = str(df_valid.loc[idx, "SEASON_ID"])
        return round(float(val), 1), season

    ppg, ppg_season = get_peak_stat("PPG")
    rpg, rpg_season = get_peak_stat("RPG")
    apg, apg_season = get_peak_stat("APG")
    spg, spg_season = get_peak_stat("SPG")
    bpg, bpg_season = get_peak_stat("BPG")

    return {
        "Total Games": total_games,
        "Total Points": total_points,
        "Total Rebounds": total_rebs,
        "Total Assists": total_asts,
        "Total Steals": total_stl,
        "Total Blocks": total_blk,
        "Peak PPG": ppg,
        "Peak PPG Season": ppg_season,
        "Peak RPG": rpg,
        "Peak RPG Season": rpg_season,
        "Peak APG": apg,
        "Peak APG Season": apg_season,
        "Peak SPG": spg,
        "Peak SPG Season": spg_season,
        "Peak BPG": bpg,
        "Peak BPG Season": bpg_season,
        "Total Seasons": total_seasons,
        "Career Span": career_span,
    }


def extract_player_awards(df_awards: pd.DataFrame) -> dict:
    """Extract championships, MVPs, Finals MVPs, and All-Star selections from PlayerAwards DataFrame."""
    if df_awards.empty or "DESCRIPTION" not in df_awards.columns:
        return {
            "Championships": 0,
            "MVPs": 0,
            "Finals MVPs": 0,
            "All-Star Appearances": 0,
        }

    rings = int((df_awards["DESCRIPTION"] == "NBA Champion").sum())
    mvps = int((df_awards["DESCRIPTION"] == "NBA Most Valuable Player").sum())
    finals_mvps = int(
        (df_awards["DESCRIPTION"] == "NBA Finals Most Valuable Player").sum()
    )
    all_stars = int((df_awards["DESCRIPTION"] == "NBA All-Star").sum())

    return {
        "Championships": rings,
        "MVPs": mvps,
        "Finals MVPs": finals_mvps,
        "All-Star Appearances": all_stars,
    }


def extract_player_bio(df_info: pd.DataFrame, full_name: str) -> dict:
    """Extract player bio (Position, Slug, Height in cm, Country) from CommonPlayerInfo DataFrame."""
    position = ""
    slug = ""
    country = ""
    height = 0

    if not df_info.empty:
        if "POSITION" in df_info.columns and pd.notna(df_info["POSITION"].iloc[0]):
            pos_val = str(df_info["POSITION"].iloc[0]).strip()
            if pos_val:
                position = pos_val
        if "PLAYER_SLUG" in df_info.columns and pd.notna(
            df_info["PLAYER_SLUG"].iloc[0]
        ):
            slug_val = str(df_info["PLAYER_SLUG"].iloc[0]).strip()
            if slug_val:
                slug = slug_val
        if "COUNTRY" in df_info.columns and pd.notna(df_info["COUNTRY"].iloc[0]):
            country = str(df_info["COUNTRY"].iloc[0]).strip()
        if "HEIGHT" in df_info.columns and pd.notna(df_info["HEIGHT"].iloc[0]):
            height = convert_to_cm(df_info["HEIGHT"].iloc[0])

    if not slug:
        slug = "-".join([normalize_name(n) for n in full_name.split()])

    return {
        "Position": position,
        "Player Slug": slug,
        "Height": height,
        "Country": country,
    }


def fetch_legend_player_data(
    player_id: int, full_name: str, delay: float = 1.0
) -> dict | None:
    """
    Fetches stats, awards, and bio for a candidate player.
    Applies is_legendary_player filter. Returns complete player dictionary if legendary, else None.
    """
    try:
        career_endpoint = playercareerstats.PlayerCareerStats(player_id=player_id)
        df_career = career_endpoint.get_data_frames()[0]
        time.sleep(delay)

        awards_endpoint = playerawards.PlayerAwards(player_id=player_id)
        df_awards = awards_endpoint.get_data_frames()[0]
        time.sleep(delay)

        metrics = extract_career_metrics(df_career)
        if not metrics:
            return None

        awards = extract_player_awards(df_awards)

        # Check legendary criteria with the new filters
        is_legend = is_legendary_player(
            points=metrics["Total Points"],
            rebs=metrics["Total Rebounds"],
            asts=metrics["Total Assists"],
            mvp_count=awards["MVPs"],
            all_star_participations=awards["All-Star Appearances"],
            finals_mvp_count=awards["Finals MVPs"],
            rings=awards["Championships"],
            min_games=metrics["Total Games"],
        )

        if not is_legend:
            return None

        # Fetch bio info for the verified legend (with fallback if CommonPlayerInfo is unavailable)
        try:
            info_endpoint = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            df_info = info_endpoint.get_data_frames()[0]
            time.sleep(delay)
            bio = extract_player_bio(df_info, full_name)
        except Exception:
            bio = extract_player_bio(pd.DataFrame(), full_name)

        record = {
            "Player ID": player_id,
            "Full Name": full_name,
            **metrics,
            **awards,
            **bio,
        }

        # Ensure correct column ordering matching LEGEND_HEADERS
        return {col: record.get(col, "") for col in LEGEND_HEADERS}

    except Exception as e:
        print(f"Erro ao processar {full_name} (ID: {player_id}): {e}")
        return None


def extract_legendary_players(
    output_file: str = "nba_legends_2.csv",
    player_source=None,
    delay: float = 1.0,
):
    """
    Extracts legendary NBA players based on historical stats and awards.
    Outputs to nba_legends_2.csv with complete career stats, season peaks, bio, and championships.

    :param output_file: Target CSV filename (default: 'nba_legends_2.csv').
    :param player_source: None (all retired NBA players), path to existing CSV, or list of player dicts.
    :param delay: Throttle delay between API requests in seconds.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(output_file):
        if os.path.basename(os.getcwd()) != "seed" and os.path.isdir(
            os.path.join(os.getcwd(), "seed")
        ):
            target_path = os.path.join(os.getcwd(), "seed", output_file)
        else:
            target_path = os.path.join(base_dir, output_file)
    else:
        target_path = output_file

    print(f"Arquivo de saída: {target_path}")

    # Resolve candidate players
    if player_source is None:
        all_players_data = players.get_players()
        candidate_players = [
            {"id": p["id"], "full_name": p["full_name"]}
            for p in all_players_data
            if not p.get("is_active", False)
        ]
    elif isinstance(player_source, str) and os.path.isfile(player_source):
        df_src = pd.read_csv(player_source)
        candidate_players = [
            {"id": int(row["Player ID"]), "full_name": str(row["Full Name"])}
            for _, row in df_src.iterrows()
        ]
    elif isinstance(player_source, list):
        candidate_players = player_source
    else:
        raise ValueError(f"Fonte de jogadores inválida: {player_source}")

    # Resume capability: track already processed IDs in output file
    processed_ids = set()
    file_exists = os.path.isfile(target_path)
    if file_exists:
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "Player ID" in row and row["Player ID"]:
                        processed_ids.add(str(row["Player ID"]))
        except Exception as e:
            print(f"Aviso ao ler IDs existentes: {e}")

    print(
        f"Jogadores já gravados em '{os.path.basename(target_path)}': {len(processed_ids)}"
    )
    print(f"Total de candidatos a processar: {len(candidate_players)}")

    added_count = 0
    with open(target_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEGEND_HEADERS)
        if not file_exists or os.path.getsize(target_path) == 0:
            writer.writeheader()
            file_exists = True

        for p in candidate_players:
            player_id = str(p["id"])
            full_name = p["full_name"]

            if player_id in processed_ids:
                continue

            print(f"Processando: {full_name} (ID: {player_id})...")
            record = fetch_legend_player_data(int(player_id), full_name, delay=delay)

            if record:
                writer.writerow(record)
                f.flush()
                processed_ids.add(player_id)
                added_count += 1
                print(
                    f"⭐ Lenda adicionada: {full_name} | "
                    f"Jogos: {record['Total Games']}, Pontos: {record['Total Points']}, "
                    f"Títulos: {record['Championships']}, MVPs: {record['MVPs']}, "
                    f"All-Stars: {record['All-Star Appearances']}"
                )
            else:
                print(f"  Não atende aos critérios: {full_name}")

    print(
        f"\nExtração concluída! {added_count} novas lendas adicionadas em '{target_path}'."
    )


def get_all_time_leaders():
    endpoints = [
        alltimeleadersgrids.AllTimeLeadersGrids().ast_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().blk_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().fg3_m_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().fgm_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().g_p_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().pts_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().reb_leaders,
        alltimeleadersgrids.AllTimeLeadersGrids().stl_leaders,
    ]
    leaders = []
    for f in endpoints:
        try:
            current_leaders = f.get_dict()
            record_obj = {
                "category": current_leaders.get("headers")[2],
                "value": current_leaders.get("data")[0][2],
                "leader_id": current_leaders.get("data")[0][0],
                "leader_full_name": current_leaders.get("data")[0][1],
                "active": current_leaders.get("data")[0][4],
            }
            print(record_obj)
            leaders.append(record_obj)
        except Exception as e:
            print(e)
    pd.DataFrame(leaders).to_csv("all_time_leaders.csv", index=False)


def extract_current_nba_players():
    all_players_data = players.get_players()
    active_players = [p for p in all_players_data if p["is_active"]]  # 530 players
    file_name = "nba_players.csv"
    headers = [
        "ID",
        "Full Name",
        "Country",
        "Weight",
        "Height",
        "Position",
        "Team Abbreviation",
        "Team Full Name",
        "Total Games",
        "Total Points",
        "Total Assists",
        "Total Rebounds",
        "Total Blocks",
        "Total Steals",
        "Avg Points",
        "Avg Rebounds",
        "Avg Assists",
        "Avg Blocks",
        "Avg Steals",
        "Season Games",
        "Season Points",
        "Season Assists",
        "Season Rebounds",
        "Season Blocks",
        "Season Steals",
        "Season Avg Points",
        "Season Avg Rebounds",
        "Season Avg Assists",
        "Season Avg Blocks",
        "Season Avg Steals",
        "Player Slug",
        "Career Span",
    ]
    with open(file_name, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not os.path.isfile(file_name):
            writer.writeheader()
        for p in active_players:
            print(p)
            id = p.get("id")
            full_name = p.get("full_name")
            try:
                common_df = commonplayerinfo.CommonPlayerInfo(
                    player_id=p.get("id")
                ).get_data_frames()[0]
                is_nba_active = (
                    True if common_df["ROSTERSTATUS"].iloc[0] == "Active" else False
                )
                if is_nba_active:
                    print(f"Extracting {full_name} with ID: {id}")
                    p_pos = common_df["POSITION"].iloc[0]
                    p_country = common_df["COUNTRY"].iloc[0]
                    p_height = convert_to_cm(common_df["HEIGHT"].iloc[0])
                    p_weight = round(int(common_df["WEIGHT"].iloc[0]) / 2.205, 2)
                    team_abb = common_df["TEAM_ABBREVIATION"].iloc[0]
                    team_full_name = f"{common_df['TEAM_CITY'].iloc[0]} {common_df['TEAM_NAME'].iloc[0]}"
                    career_df = playercareerstats.PlayerCareerStats(
                        player_id=p.get("id")
                    ).get_data_frames()[0]
                    total_games = int(career_df["GP"].sum())
                    total_points = int(career_df["PTS"].sum())
                    total_assists = int(career_df["AST"].sum())
                    total_rebounds = int(career_df["REB"].sum())
                    total_steals = int(career_df["STL"].sum())
                    total_blocks = int(career_df["BLK"].sum())
                    avg_points = round(total_points / total_games, 1)
                    avg_assists = round(total_assists / total_games, 1)
                    avg_rebounds = round(total_rebounds / total_games, 1)
                    avg_steals = round(total_steals / total_games, 1)
                    avg_blocks = round(total_blocks / total_games, 1)
                    row = {
                        "ID": id,
                        "Full Name": full_name,
                        "Position": p_pos,
                        "Country": p_country,
                        "Weight": p_weight,
                        "Height": p_height,
                        "Team Abbreviation": team_abb,
                        "Team Full Name": team_full_name,
                        "Total Games": total_games,
                        "Total Points": total_points,
                        "Total Assists": total_assists,
                        "Total Rebounds": total_rebounds,
                        "Total Blocks": total_blocks,
                        "Total Steals": total_steals,
                        "Avg Points": avg_points,
                        "Avg Assists": avg_assists,
                        "Avg Rebounds": avg_rebounds,
                        "Avg Blocks": avg_blocks,
                        "Avg Steals": avg_steals,
                        "Season Games": None,
                        "Season Points": None,
                        "Season Assists": None,
                        "Season Rebounds": None,
                        "Season Blocks": None,
                        "Season Avg Points": None,
                        "Season Avg Assists": None,
                        "Season Avg Rebounds": None,
                        "Season Avg Blocks": None,
                        "Season Avg Steals": None,
                    }
                    writer.writerow(row)
                time.sleep(1.5)

            except Exception as e:
                print(e)


def append_player_slug_actual_players():
    df = pd.read_csv("nba_players.csv")
    ids = df["ID"].tolist()
    for id in ids:
        player_matches = df[df["ID"].astype(str) == str(id)]
        if player_matches.empty:
            continue
        idx = player_matches.index[0]
        full_name = df.at[idx, "Full Name"]
        array = full_name.split(" ")
        normalized = [normalize_name(n) for n in array]
        slug = "-".join(normalized)
        print(f"Adding slug for {full_name} | {slug} ")
        df.at[idx, "Player Slug"] = slug
    df.to_csv("nba_players.csv", index=False)


def append_player_career_span_actual_players():
    df = pd.read_csv("nba_players.csv")
    ids = df["ID"].tolist()
    for id in ids:
        player_matches = df[df["ID"].astype(str) == str(id)]
        if player_matches.empty:
            continue
        df_career = playercareerstats.PlayerCareerStats(player_id=id).get_data_frames()[
            0
        ]
        idx = player_matches.index[0]
        full_name = df.at[idx, "Full Name"]
        career_span = f"{df_career['SEASON_ID'].min()} - {df_career['SEASON_ID'].max()}"
        print(f"Adding career for {full_name} | {career_span} ")
        df.at[idx, "Career Span"] = career_span
        time.sleep(1.5)
    df.to_csv("nba_players.csv", index=False)


def get_team_data():
    nt = teams.teams
    docs = []
    for team in nt:
        team_id = team[0]
        advancedStats = leaguedashteamstats.LeagueDashTeamStats(
            team_id_nullable=team_id, measure_type_detailed_defense="Advanced"
        ).get_data_frames()[0]
        leagueStats = leaguestandingsv3.LeagueStandingsV3(
            season="2024-25"
        ).get_data_frames()[0]
        commonInfo = teaminfocommon.TeamInfoCommon(team_id=team_id).get_data_frames()[0]
        leagueStats["Rank"] = (
            leagueStats["WinPCT"].rank(ascending=False, method="min").astype(int)
        )
        team_row = leagueStats[leagueStats["TeamID"] == team_id].iloc[0]
        print(f"rank: {team_row['Rank']}")
        doc = {
            "_id": team_id,
            "abbreviation": commonInfo["TEAM_ABBREVIATION"][0],
            "name": team[5],
            "city": commonInfo["TEAM_CITY"][0],
            "conference": team_row["Conference"],
            "division": team_row["Division"],
            "founded_in": team[3],
            "championships": len(team[7]),
            "last_season": {
                "rank": int(team_row["Rank"]),
                "record": {
                    "wins": int(advancedStats["W"][0]),
                    "losses": int(advancedStats["L"][0]),
                    "win_pct": float(advancedStats["W_PCT"][0]),
                    "home": team_row["HOME"],
                    "road": team_row["ROAD"],
                },
                "power_ranking": {
                    "rank": None,
                    "tier": None,
                    "power_score": None,
                    "trend": None,
                },
                "metrics": {
                    "pace": float(advancedStats["PACE"][0]),
                    "offensive_rating": float(advancedStats["OFF_RATING"][0]),
                    "defensive_rating": float(advancedStats["DEF_RATING"][0]),
                    "net_rating": float(advancedStats["NET_RATING"][0]),
                    "pts_per_game": float(team_row["PointsPG"]),
                    "pts_allowed_per_game": float(team_row["OppPointsPG"]),
                },
            },
            "actual_season": {
                "rank": None,
                "record": {
                    "wins": None,
                    "losses": None,
                    "win_pct": None,
                },
                "power_ranking": {
                    "rank": None,
                },
                "metrics": {
                    "pace": None,
                    "offensive_rating": None,
                    "defensive_rating": None,
                    "net_rating": None,
                    "pts_per_game": None,
                    "pts_allowed_per_game": None,
                },
            },
        }
        time.sleep(1.0)
        print(doc)
        docs.append(doc)
    with open("teams_metrics.json", "w") as f:
        json.dump(docs, f)
        f.close()


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


def calculate_power_score():
    with open("teams_metrics.json", "r") as f:
        raw = json.load(f)
        net_ratings = [t["last_season"]["metrics"]["net_rating"] for t in raw]
        min_net = min(net_ratings)
        max_net = max(net_ratings)
        net_range = max_net - min_net if max_net != min_net else 1.0

        for t in raw:
            net_rating = t.get("last_season").get("metrics").get("net_rating")
            win_pct = t.get("last_season").get("record").get("win_pct")
            normalized_net = (net_rating - min_net) / net_range
            power_score = round((win_pct * 0.4 + normalized_net * 0.6) * 100, 1)
            t["last_season"]["power_ranking"]["power_score"] = power_score

        teams = [
            team
            for team in raw
            if t["last_season"]["power_ranking"]["power_score"] is not None
        ]
        teams.sort(
            key=lambda x: x["last_season"]["power_ranking"]["power_score"], reverse=True
        )

        for power_rank, t in enumerate(teams, start=1):
            pr = t["last_season"]["power_ranking"]
            pr["rank"] = power_rank
            pr["tier"] = get_tier_by_rank(power_rank)
            season_rank = t["last_season"]["rank"]
            if season_rank is not None:
                diff = season_rank - power_rank
                pr["trend"] = f"+{diff}" if diff > 0 else str(diff)
            else:
                pr["trend"] = 0
        with open("normalized_teams_data.json", "w") as out:
            json.dump(raw, out, indent=2)


if __name__ == "__main__":
    extract_current_nba_players()
