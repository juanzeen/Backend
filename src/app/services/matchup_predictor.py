from typing import Any
from ..schemas.teams import Team
from ..schemas.players import Player

# League-wide baselines (denominators) from docs/matchup_prediction.md
LEAGUE_AVERAGES: dict[str, float] = {
    "pace": 99.0,
    "defensive_rating": 114.0,
    "pts": 114.0,
    "reb": 43.5,
    "ast": 26.5,
    "stl": 7.5,
    "blk": 5.0,
}

# Additive venue modifiers (Home: positive, Away: negative)
HOME_MODIFIERS: dict[str, float] = {
    "pts": 1.2,
    "reb": 0.35,
    "ast": 0.30,
    "stl": 0.08,
    "blk": 0.08,
}

# Confidence interval relative margins
CONFIDENCE_MARGINS: dict[str, float] = {
    "pts": 0.10,
    "ast": 0.15,
    "reb": 0.12,
    "stl": 0.20,
    "blk": 0.20,
}


def extract_player_data(player: Player | dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize required player attributes and baseline stats."""
    player_id = player.get("_id") or player.get("id")
    name = player.get("full_name") or player.get("name", "")
    age = player.get("age")

    season_avg = (player.get("season") or {}).get("avg") or {}
    career_avg = (player.get("career") or {}).get("avg") or {}

    has_season_data = (
        season_avg.get("points") is not None or season_avg.get("pts") is not None
    )
    metrics = season_avg if has_season_data else career_avg

    return {
        "id": player_id,
        "name": name,
        "age": age,
        "pts_avg": float(metrics.get("points") or metrics.get("pts") or 0.0),
        "ast_avg": float(metrics.get("assists") or metrics.get("ast") or 0.0),
        "reb_avg": float(metrics.get("rebounds") or metrics.get("reb") or 0.0),
        "stl_avg": float(metrics.get("steals") or metrics.get("stl") or 0.0),
        "blk_avg": float(metrics.get("blocks") or metrics.get("blk") or 0.0),
    }


def extract_team_data(team: Team | dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize opponent team defensive metrics."""
    team_id = team.get("_id") or team.get("id")
    name = team.get("name", "")
    actual_season = team.get("actual_season") or {}
    last_season = team.get("last_season") or {}
    team_rank = actual_season.get("rank")

    if team_rank and actual_season.get("metrics"):
        metrics = actual_season.get("metrics") or {}
    else:
        metrics = last_season.get("metrics") or {}

    return {
        "id": team_id,
        "name": name,
    } | metrics


def calculate_pace_factor(opponent_pace: float | None) -> float:
    """Calculate Pace Factor = Opponent Pace / League Average Pace."""
    if not opponent_pace or opponent_pace <= 0:
        return 1.0
    return round(opponent_pace / LEAGUE_AVERAGES["pace"], 3)


def calculate_defense_factor(team_metrics: dict[str, Any], stat: str) -> float:
    """
    Calculate Defense / Matchup Factor for a specific stat category.
    - Points: Opponent Defensive Rating / League Average DRTG
    - Rebounds: Opponent Rebounds Allowed / League Avg Rebounds
    - Assists: Opponent Assists Allowed / League Avg Assists
    - Steals: Opponent Steals Allowed / League Avg Steals
    - Blocks: Opponent Blocks Allowed / League Avg Blocks
    """
    stat_mapping = {
        "pts": team_metrics.get("defensive_rating")
        or team_metrics.get("pts_allowed_per_game"),
        "reb": team_metrics.get("reb_allowed_per_game"),
        "ast": team_metrics.get("ast_allowed_per_game"),
        "stl": team_metrics.get("stl_allowed_per_game"),
        "blk": team_metrics.get("blk_allowed_per_game"),
    }
    league_key = "defensive_rating" if stat == "pts" else stat
    league_avg = LEAGUE_AVERAGES.get(league_key, 1.0)
    stat_val = stat_mapping.get(stat)

    if not stat_val or stat_val <= 0:
        return 1.0
    return round(float(stat_val) / league_avg, 3)


def calculate_home_modifier(stat: str, is_home: bool = True) -> float:
    """Home (+) or Away (-)."""
    multiplier = 1.0 if is_home else -1.0
    return round(HOME_MODIFIERS.get(stat, 0.0) * multiplier, 2)

def calculate_single_stat_projection(
    baseline: float,
    pace_factor: float,
    defense_factor: float,
    home_mod: float,
) -> float:
    """
    Matchup Formula:
    Game Projected Stat = (Baseline * Pace Factor * Defense Factor) + Home Modifier
    """
    projected = (baseline * pace_factor * defense_factor) + home_mod
    return max(0.0, round(projected, 1))


def calculate_confidence_intervals(
    projected_stats: dict[str, float],
) -> dict[str, list[float]]:
    """Compute confidence intervals for each projected stat category."""
    intervals = {}
    for stat, val in projected_stats.items():
        margin = CONFIDENCE_MARGINS.get(stat, 0.15)
        lower = max(0.0, round(val * (1.0 - margin), 1))
        upper = round(val * (1.0 + margin), 1)
        intervals[f"{stat}_range"] = [lower, upper]
    return intervals


def calculate_matchup_prediction(
    player_data: Player | dict[str, Any],
    team_data: Team | dict[str, Any],
    is_home: bool = True
) -> dict[str, Any]:
    """
    Calculate single-game matchup prediction for an NBA player against an opponent team.
    Returns projected averages across PTS, AST, REB, STL, BLK along with factors and intervals.
    """
    player = extract_player_data(player_data)
    team = extract_team_data(team_data)
    print(f"{player} | {team}")

    pace_factor = calculate_pace_factor(team.get("pace"))
    age = player.get("age")

    stats_to_predict = {
        "pts": player.get("pts_avg", 0.0),
        "ast": player.get("ast_avg", 0.0),
        "reb": player.get("reb_avg", 0.0),
        "stl": player.get("stl_avg", 0.0),
        "blk": player.get("blk_avg", 0.0),
    }

    projected_averages = {}
    defense_factors = {}

    for stat, baseline in stats_to_predict.items():
        def_factor = calculate_defense_factor(team, stat)
        defense_factors[stat] = def_factor
        home_mod = calculate_home_modifier(stat, is_home=is_home)

        projected_averages[stat] = calculate_single_stat_projection(
            baseline=baseline,
            pace_factor=pace_factor,
            defense_factor=def_factor,
            home_mod=home_mod,
        )

    confidence_intervals = calculate_confidence_intervals(projected_averages)

    return {
        "player_id": player.get("id"),
        "full_name": player.get("name"),
        "opponent_id": team.get("id"),
        "opponent_name": team.get("name"),
        "projected_averages": projected_averages,
        "confidence_intervals": confidence_intervals,
        "factors": {
            "pace_factor": pace_factor,
            "defense_factors": defense_factors,
            "is_home": is_home,
        },
    }
