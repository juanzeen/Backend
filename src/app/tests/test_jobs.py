from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd
import pytest

from ..jobs.daily_sync import get_tier_by_rank, sync_teams, sync_players
from ..jobs.weekly_sync import sync_rosters


def test_get_tier_by_rank():
    assert get_tier_by_rank(1) == "Championship Contender"
    assert get_tier_by_rank(5) == "Championship Contender"
    assert get_tier_by_rank(6) == "Playoff Contender"
    assert get_tier_by_rank(10) == "Playoff Contender"
    assert get_tier_by_rank(11) == "Play-in Contender"
    assert get_tier_by_rank(18) == "Play-in Contender"
    assert get_tier_by_rank(19) == "Lottery"
    assert get_tier_by_rank(24) == "Lottery"
    assert get_tier_by_rank(25) == "Rebuilding"
    assert get_tier_by_rank(30) == "Rebuilding"


@pytest.mark.anyio
async def test_sync_teams():
    # Mock Standings
    mock_standings_df = pd.DataFrame(
        [
            {"TeamID": 1610612738, "PlayoffRank": 1, "PointsPG": 120.5},
            {"TeamID": 1610612748, "PlayoffRank": 8, "PointsPG": 110.0},
        ]
    )

    # Mock Traditional Team Stats (PerGame)
    mock_stats_df = pd.DataFrame(
        [
            {
                "TEAM_ID": 1610612738,
                "REB": 46.5,
                "DREB": 35.8,
                "OREB": 10.7,
                "AST": 26.9,
                "STL": 6.8,
                "BLK": 6.6,
            },
            {
                "TEAM_ID": 1610612748,
                "REB": 42.3,
                "DREB": 32.8,
                "OREB": 9.5,
                "AST": 25.8,
                "STL": 7.5,
                "BLK": 3.4,
            },
        ]
    )

    # Mock Advanced Stats
    mock_adv_df = pd.DataFrame(
        [
            {
                "TEAM_ID": 1610612738,
                "TEAM_NAME": "Boston Celtics",
                "W": 64,
                "L": 18,
                "W_PCT": 0.78,
                "PACE": 100.5,
                "OFF_RATING": 122.0,
                "DEF_RATING": 110.0,
                "NET_RATING": 12.0,
            },
            {
                "TEAM_ID": 1610612748,
                "TEAM_NAME": "Miami Heat",
                "W": 46,
                "L": 36,
                "W_PCT": 0.56,
                "PACE": 98.0,
                "OFF_RATING": 113.0,
                "DEF_RATING": 112.0,
                "NET_RATING": 1.0,
            },
        ]
    )

    # Mock Opponent Stats
    mock_opp_df = pd.DataFrame(
        [
            {
                "TEAM_ID": 1610612738,
                "OPP_PTS": 109.2,
                "OPP_REB": 42.0,
                "OPP_DREB": 32.5,
                "OPP_OREB": 9.5,
                "OPP_AST": 24.5,
                "OPP_STL": 6.8,
                "OPP_BLK": 4.5,
            },
            {
                "TEAM_ID": 1610612748,
                "OPP_PTS": 108.4,
                "OPP_REB": 41.5,
                "OPP_DREB": 31.0,
                "OPP_OREB": 10.5,
                "OPP_AST": 25.0,
                "OPP_STL": 7.2,
                "OPP_BLK": 4.8,
            },
        ]
    )

    mock_db = MagicMock()
    mock_db_collection = MagicMock()
    mock_db_collection.bulk_write = AsyncMock(
        return_value=MagicMock(matched_count=2, modified_count=2)
    )
    mock_db.__getitem__.return_value = mock_db_collection

    mock_redis = MagicMock()
    mock_redis.set = AsyncMock()

    with (
        patch(
            "nba_api.stats.endpoints.leaguestandingsv3.LeagueStandingsV3"
        ) as mock_standings_ep,
        patch(
            "nba_api.stats.endpoints.leaguedashteamstats.LeagueDashTeamStats"
        ) as mock_team_ep,
        patch("time.sleep", return_value=None),
    ):
        mock_standings_ep.return_value.get_data_frames.return_value = [
            mock_standings_df
        ]
        mock_team_ep.return_value.get_data_frames.side_effect = [
            [mock_stats_df],
            [mock_adv_df],
            [mock_opp_df],
        ]

        result = await sync_teams(db=mock_db, redis=mock_redis)

    assert result["teams_updated"] == 2
    assert "league_averages" in result
    assert result["league_averages"]["pace"] == pytest.approx(99.25, rel=1e-2)

    # Check that bulk_write and redis.set were called
    assert mock_db_collection.bulk_write.called
    assert mock_redis.set.called

    ops = mock_db_collection.bulk_write.call_args[0][0]
    celtics_metrics = ops[0]._doc["$set"]["actual_season.metrics"]
    assert celtics_metrics["stl_per_game"] == 6.8
    assert celtics_metrics["ast_per_game"] == 26.9
    assert celtics_metrics["blk_per_game"] == 6.6
    assert celtics_metrics["reb_per_game"] == 46.5
    assert celtics_metrics["dreb_per_game"] == 35.8
    assert celtics_metrics["oreb_per_game"] == 10.7
    assert celtics_metrics["dreb_allowed_per_game"] == 32.5
    assert celtics_metrics["oreb_allowed_per_game"] == 9.5


@pytest.mark.anyio
async def test_sync_players():
    mock_players_df = pd.DataFrame(
        [
            {
                "PLAYER_ID": 2544,
                "PLAYER_NAME": "LeBron James",
                "TEAM_ID": 1610612747,
                "GP": 71,
                "MIN": 35.3,
                "PTS": 25.7,
                "REB": 7.3,
                "AST": 8.3,
                "STL": 1.3,
                "BLK": 0.5,
                "FG_PCT": 0.540,
                "FG3_PCT": 0.410,
                "FT_PCT": 0.750,
            }
        ]
    )

    mock_db = MagicMock()
    mock_db_collection = MagicMock()
    mock_db_collection.bulk_write = AsyncMock(
        return_value=MagicMock(matched_count=1, modified_count=1)
    )
    mock_db.__getitem__.return_value = mock_db_collection

    with (
        patch(
            "nba_api.stats.endpoints.leaguedashplayerstats.LeagueDashPlayerStats"
        ) as mock_player_ep,
        patch("nba_api.stats.endpoints.playergamelogs.PlayerGameLogs") as mock_logs_ep,
    ):
        mock_player_ep.return_value.get_data_frames.side_effect = [
            [mock_players_df],
            [mock_players_df],
        ]
        mock_logs_ep.return_value.get_data_frames.return_value = [pd.DataFrame()]

        result = await sync_players(db=mock_db, season="2024-25")

    assert result["players_updated"] == 1
    assert result["seasons_updated"] == 0
    assert mock_db_collection.bulk_write.called


@pytest.mark.anyio
async def test_sync_rosters():
    mock_roster_df = pd.DataFrame(
        [
            {
                "PERSON_ID": 2544,
                "TEAM_ID": 1610612747,
                "TEAM_ABBREVIATION": "LAL",
                "TEAM_NAME": "Los Angeles Lakers",
            }
        ]
    )

    mock_db = MagicMock()
    mock_db_collection = MagicMock()
    mock_db_collection.bulk_write = AsyncMock(
        return_value=MagicMock(matched_count=1, modified_count=1)
    )
    mock_db.__getitem__.return_value = mock_db_collection

    with patch(
        "nba_api.stats.endpoints.commonallplayers.CommonAllPlayers"
    ) as mock_all_ep:
        mock_all_ep.return_value.get_data_frames.return_value = [mock_roster_df]

        updated_count = await sync_rosters(db=mock_db, season="2024-25")

    assert updated_count == 1
    assert mock_db_collection.bulk_write.called
