from ..dependencies import get_db
from ..schemas.predictions import PlayerInfos
from ..schemas.player_seasons import AvgStats


def calculate_age_factor(age: int):
    """Calculate the age factor for marcel projection"""
    age_factor = 1.0
    if age < 27:
        age_factor = 1 + ((27 - age) * 0.006)
    if age > 29:
        age_factor = 1 - ((age - 29) * 0.005)
    return age_factor


def calculate_marcel_projection(averages: list[AvgStats], age: int):
    """Uses the marcel projection, with a sum of weighted averages from the past 3 seasons multiplied with the age factor"""
    dict = {}
    age_factor = calculate_age_factor(age)
    for i, _ in enumerate(averages[0].keys()):
        value = (
            list(averages[0].values())[i]
            + list(averages[1].values())[i]
            + list(averages[2].values())[i]
        ) / 9
        dict = dict | {list(averages[0].keys())[i]: round(value * age_factor, 2)}
    return dict, age_factor


async def calculate_player_year_prediction(*, player: PlayerInfos):
    """Calculate the season prediction for a specific player"""
    player_id = player.get("player_id")
    age = player.get("age")
    db = get_db()
    sc = db["players_seasons"]
    recent_years = ["2025-26", "2024-25", "2023-24"]
    multipliers = [5, 3, 1]
    stats: list[AvgStats] = []
    for i, y in enumerate(recent_years):
        season_stats = await sc.find_one({"_id": f"{player_id}_{y}"})
        averages = season_stats["season_averages"]
        weighted_averages = {k: v * multipliers[i] for k, v in averages.items()}
        stats.append(weighted_averages)
    projection, age_factor = calculate_marcel_projection(stats, age)
    return projection, age_factor


def calculate_confidence_intervals(expected: dict[str, float]):
    """Calculates confidence intervals for a year prediction, with specific multipliers for each stat"""
    print(expected)
    margin_list = [0.1, 0.15, 0.12, 0.2, 0.2]
    label_list = ["pts_range", "ast_range", "reb_range", "stl_range", "blk_range"]
    values_list = list(expected.values())
    data = {}
    for i, margin in enumerate(margin_list):
        lower = max(0.0, round(values_list[i] * (1 - margin), 1))
        upper = round(values_list[i] * (1 + margin), 1)
        data = data | {label_list[i]: [lower, upper]}
    return data
