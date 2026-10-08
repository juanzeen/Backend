from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ..services.season_predictor import (
    calculate_age_factor,
    calculate_marcel_projection,
    calculate_player_year_prediction,
    calculate_confidence_intervals as calculate_season_confidence_intervals,
)
from ..services.matchup_predictor import (
    extract_player_data,
    extract_team_data,
    calculate_pace_factor,
    calculate_defense_factor,
    calculate_home_modifier,
    calculate_single_stat_projection,
    calculate_confidence_intervals as calculate_matchup_confidence_intervals,
    calculate_matchup_prediction,
)


def test_calculate_age_factor_young():
    factor_20 = calculate_age_factor(20)
    assert factor_20 == pytest.approx(1 + (7 * 0.006), rel=1e-4)

    factor_26 = calculate_age_factor(26)
    assert factor_26 == pytest.approx(1 + (1 * 0.006), rel=1e-4)


def test_calculate_age_factor_peak():
    assert calculate_age_factor(27) == 1.0
    assert calculate_age_factor(28) == 1.0
    assert calculate_age_factor(29) == 1.0


def test_calculate_age_factor_veteran():
    factor_30 = calculate_age_factor(30)
    assert factor_30 == pytest.approx(1 - (1 * 0.005), rel=1e-4)

    factor_35 = calculate_age_factor(35)
    assert factor_35 == pytest.approx(1 - (6 * 0.005), rel=1e-4)


def test_calculate_marcel_projection():
    averages = [
        {
            "points": 25.0 * 5,
            "assists": 5.0 * 5,
            "rebounds": 5.0 * 5,
            "steals": 1.0 * 5,
            "blocks": 1.0 * 5,
        },
        {
            "points": 20.0 * 3,
            "assists": 4.0 * 3,
            "rebounds": 4.0 * 3,
            "steals": 1.0 * 3,
            "blocks": 1.0 * 3,
        },
        {
            "points": 15.0 * 1,
            "assists": 3.0 * 1,
            "rebounds": 3.0 * 1,
            "steals": 1.0 * 1,
            "blocks": 1.0 * 1,
        },
    ]
    projection, age_factor = calculate_marcel_projection(averages, age=28)
    assert age_factor == 1.0
    assert projection["points"] == round(200 / 9 * 1.0, 2)
    assert projection["assists"] == round((25 + 12 + 3) / 9 * 1.0, 2)
    assert projection["rebounds"] == round((25 + 12 + 3) / 9 * 1.0, 2)
    assert projection["steals"] == round((5 + 3 + 1) / 9 * 1.0, 2)
    assert projection["blocks"] == round((5 + 3 + 1) / 9 * 1.0, 2)


@pytest.mark.anyio
async def test_calculate_player_year_prediction():
    mock_db = MagicMock()
    mock_collection = MagicMock()

    season_averages = {
        "points": 20.0,
        "assists": 5.0,
        "rebounds": 6.0,
        "steals": 1.0,
        "blocks": 0.8,
    }
    mock_collection.find_one = AsyncMock(
        return_value={"_id": "1630173_2025-26", "season_averages": season_averages}
    )
    mock_db.__getitem__.return_value = mock_collection

    with patch("app.services.season_predictor.get_db", return_value=mock_db):
        player_info = {"player_id": 1630173, "age": 25}
        projection, age_factor = await calculate_player_year_prediction(
            player=player_info
        )

    assert age_factor == calculate_age_factor(25)
    assert "points" in projection
    assert projection["points"] > 0
    assert mock_collection.find_one.call_count == 3


def test_calculate_season_confidence_intervals():
    expected = {
        "points": 20.0,
        "assists": 5.0,
        "rebounds": 6.0,
        "steals": 1.0,
        "blocks": 0.8,
    }
    ci = calculate_season_confidence_intervals(expected)
    assert "pts_range" in ci
    assert "ast_range" in ci
    assert "reb_range" in ci
    assert "stl_range" in ci
    assert "blk_range" in ci

    # Points margin is 0.10
    assert ci["pts_range"] == [18.0, 22.0]
    # Assists margin is 0.15
    assert ci["ast_range"] == [4.2, 5.8]
    # Lower bound never drops below 0
    assert all(r[0] >= 0.0 for r in ci.values())
    assert all(r[0] <= r[1] for r in ci.values())


def test_extract_player_data_from_season_avg():
    player_data = {
        "_id": 1630173,
        "full_name": "Precious Achiuwa",
        "age": 25,
        "season": {
            "avg": {
                "points": 8.0,
                "assists": 1.1,
                "rebounds": 6.0,
                "steals": 0.6,
                "blocks": 0.7,
            }
        },
        "career": {"avg": {}},
    }
    extracted = extract_player_data(player_data)
    assert extracted["id"] == 1630173
    assert extracted["name"] == "Precious Achiuwa"
    assert extracted["age"] == 25
    assert extracted["pts_avg"] == 8.0
    assert extracted["ast_avg"] == 1.1
    assert extracted["reb_avg"] == 6.0


def test_extract_player_data_fallback_career():
    player_data = {
        "id": 1630173,
        "name": "Precious Achiuwa",
        "age": 25,
        "season": {"avg": {}},
        "career": {
            "avg": {
                "pts": 9.5,
                "ast": 1.5,
                "reb": 7.0,
                "stl": 0.8,
                "blk": 0.9,
            }
        },
    }
    extracted = extract_player_data(player_data)
    assert extracted["pts_avg"] == 9.5
    assert extracted["ast_avg"] == 1.5
    assert extracted["reb_avg"] == 7.0


def test_extract_team_data_last_season():
    team_data = {
        "_id": 1610612737,
        "name": "Atlanta Hawks",
        "last_season": {
            "metrics": {
                "pace": 102.5,
                "defensive_rating": 118.0,
                "pts_allowed_per_game": 119.3,
            }
        },
        "actual_season": {"rank": None, "metrics": {}},
    }
    extracted = extract_team_data(team_data)
    assert extracted["id"] == 1610612737
    assert extracted["name"] == "Atlanta Hawks"
    assert extracted["pace"] == 102.5
    assert extracted["defensive_rating"] == 118.0


def test_extract_team_data_actual_season():
    team_data = {
        "id": 1610612737,
        "name": "Atlanta Hawks",
        "last_season": {"metrics": {"pace": 100.0, "defensive_rating": 115.0}},
        "actual_season": {
            "rank": 5,
            "metrics": {"pace": 104.0, "defensive_rating": 112.0},
        },
    }
    extracted = extract_team_data(team_data)
    assert extracted["pace"] == 104.0
    assert extracted["defensive_rating"] == 112.0


def test_calculate_pace_factor():
    assert calculate_pace_factor(99.0) == 1.0
    assert calculate_pace_factor(103.0) == round(103.0 / 99.0, 3)
    assert calculate_pace_factor(None) == 1.0
    assert calculate_pace_factor(0) == 1.0
    assert calculate_pace_factor(-5.0) == 1.0


def test_calculate_defense_factor():
    team_metrics = {
        "defensive_rating": 118.0,
        "pts_allowed_per_game": 119.0,
        "reb_allowed_per_game": 45.0,
        "ast_allowed_per_game": 28.0,
        "stl_allowed_per_game": 8.0,
        "blk_allowed_per_game": 5.5,
    }
    # All stats are divided by the fallback league average
    assert calculate_defense_factor(team_metrics, "pts") == round(118.0 / 114.0, 3)
    assert calculate_defense_factor(team_metrics, "reb") == round(45.0 / 43.5, 3)
    assert calculate_defense_factor(team_metrics, "ast") == round(28.0 / 26.5, 3)
    assert calculate_defense_factor(team_metrics, "stl") == round(8.0 / 7.5, 3)
    assert calculate_defense_factor(team_metrics, "blk") == round(5.5 / 5.0, 3)

    # Missing metrics fallback to 1.0
    assert calculate_defense_factor({}, "pts") == 1.0
    assert calculate_defense_factor({}, "reb") == 1.0


def test_calculate_home_modifier():
    assert calculate_home_modifier("pts", is_home=True) == 1.2
    assert calculate_home_modifier("pts", is_home=False) == -1.2
    assert calculate_home_modifier("reb", is_home=True) == 0.35
    assert calculate_home_modifier("reb", is_home=False) == -0.35


def test_calculate_single_stat_projection():
    # (baseline * pace * defense) + home
    proj = calculate_single_stat_projection(
        baseline=20.0,
        pace_factor=1.0,
        defense_factor=1.0,
        home_mod=1.2,
    )
    assert proj == 21.2

    proj_clamped = calculate_single_stat_projection(
        baseline=0.5,
        pace_factor=0.9,
        defense_factor=0.9,
        home_mod=-1.2,
    )
    assert proj_clamped == 0.0


def test_calculate_matchup_confidence_intervals():
    projected = {"pts": 20.0, "ast": 5.0, "reb": 6.0, "stl": 1.0, "blk": 0.8}
    ci = calculate_matchup_confidence_intervals(projected)
    assert "pts_range" in ci
    assert ci["pts_range"] == [18.0, 22.0]
    assert all(r[0] >= 0.0 for r in ci.values())
    assert all(r[0] <= r[1] for r in ci.values())


def test_calculate_matchup_prediction_full():
    player_mock = {
        "_id": 1630173,
        "full_name": "Precious Achiuwa",
        "age": 25,
        "season": {
            "avg": {
                "points": 8.0,
                "assists": 1.1,
                "rebounds": 6.0,
                "steals": 0.6,
                "blocks": 0.7,
            }
        },
        "career": {"avg": {}},
    }
    team_mock = {
        "_id": 1610612737,
        "name": "Atlanta Hawks",
        "last_season": {
            "metrics": {
                "pace": 102.5,
                "defensive_rating": 118.0,
                "pts_allowed_per_game": 119.3,
                "reb_allowed_per_game": 45.0,
                "ast_allowed_per_game": 28.0,
                "stl_allowed_per_game": 8.0,
                "blk_allowed_per_game": 5.2,
            }
        },
    }

    result = calculate_matchup_prediction(player_mock, team_mock, is_home=True)
    assert result["player_id"] == 1630173
    assert result["full_name"] == "Precious Achiuwa"
    assert result["opponent_id"] == 1610612737
    assert result["opponent_name"] == "Atlanta Hawks"
    assert "projected_averages" in result
    assert result["projected_averages"]["pts"] > 0
    assert "confidence_intervals" in result
    assert "factors" in result
    assert result["factors"]["is_home"] is True
