from ..dependencies import get_db
from ..schemas.predictions import PlayerInfos
from ..schemas.player_seasons import AvgStats

def calculate_age_factor(age: int):
  age_factor = 1.0
  if age < 27:
    age_factor = 1 + ((27 - age) * 0.006)
  if age > 29:
    age_factor = 1 - ((age - 29) * 0.005)
  return age_factor

def calculate_marcel_projection(averages: list[AvgStats], age: int):
  dict = {}
  age_factor = calculate_age_factor(age)
  for i, _ in enumerate(averages[0].keys()):
      value = (list(averages[0].values())[i] + list(averages[1].values())[i] + list(averages[2].values())[i]) / 9
      dict = dict | {list(averages[0].keys())[i]: round(value * age_factor,2)}
  return dict

async def calculate_player_year_prediction(*, player: PlayerInfos):
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
    projection = calculate_marcel_projection(stats, age)
    return projection
