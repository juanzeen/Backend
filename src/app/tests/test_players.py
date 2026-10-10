from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from ..main import app
from ..dependencies import get_db

mock_p1 = {
    "_id": 1630173,
    "career": {
        "totals": {
            "games": 467,
            "points": 3721,
            "assists": 511,
            "rebounds": 2792,
            "blocks": 327,
            "steals": 29,
        },
        "avg": {
            "points": 8,
            "assists": 1.1,
            "rebounds": 6,
            "blocks": 0.7,
            "steals": 0.6,
        },
    },
    "country": "Nigeria",
    "full_name": "Precious Achiuwa",
    "height": 203,
    "id": 1630173,
    "position": "Forward",
    "age": 20,
    "season": {
        "totals": {
            "games": 0,
            "points": 0,
            "assists": 0,
            "rebounds": 0,
            "blocks": 0,
            "steals": 0,
        },
        "avg": {"points": 0, "assists": 0, "rebounds": 0, "blocks": 0, "steals": 0},
    },
    "team": {"abbreviation": "SAC", "name": "Sacramento Kings"},
    "slug": "precious-achiuwa",
    "career_span": "2020-21 - 2021-21",
}
mock_p2 = {
    "_id": 30212,
    "career": {
        "totals": {
            "games": 467,
            "points": 3721,
            "assists": 511,
            "rebounds": 2792,
            "blocks": 327,
            "steals": 29,
        },
        "avg": {
            "points": 8,
            "assists": 1.1,
            "rebounds": 6,
            "blocks": 0.7,
            "steals": 0.6,
        },
    },
    "country": "Nigeria",
    "full_name": "Precious Achiuwa",
    "height": 203,
    "id": 1630173,
    "age": 21,
    "position": "Forward",
    "season": {
        "totals": {
            "games": 0,
            "points": 0,
            "assists": 0,
            "rebounds": 0,
            "blocks": 0,
            "steals": 0,
        },
        "avg": {"points": 0, "assists": 0, "rebounds": 0, "blocks": 0, "steals": 0},
    },
    "team": {"abbreviation": "SAC", "name": "Sacramento Kings"},
    "slug": "precious-achiuwa",
    "career_span": "2020-21 - 2021-21",
}


@pytest.mark.anyio
async def test_get_players():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/")
        data = response.json().get("data", [])
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(data) > 1
    assert message == "Actual NBA players successfully retrieved."


@pytest.mark.anyio
async def test_get_nba_players_custom_pagination():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?page=2&limit=5")
        players = response.json().get("data", [])
        pagination_metadata = response.json().get("pagination", None)
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Actual NBA players successfully retrieved."
    assert pagination_metadata.get("page") == 2
    assert pagination_metadata.get("limit") == 5
    assert len(players) > 1


@pytest.mark.anyio
async def test_get_nba_players_pagination_flags_first_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?limit=10&page=1")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") == True
    assert pagination_meta.get("has_previous") == False


@pytest.mark.anyio
async def test_get_nba_players_pagination_flags_last_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?limit=10&page=16")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") == False
    assert pagination_meta.get("has_previous") == True


@pytest.mark.anyio
async def test_get_nba_players_pagination_flags_middle_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?limit=10&page=10")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") == True
    assert pagination_meta.get("has_previous") == True


@pytest.mark.anyio
async def test_fail_get_players():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=458)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=None)
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/")
        data = response.json().get("data", [])
        message = response.json().get("detail", "").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert data == []
    assert message == "Actual NBA players not found."


@pytest.mark.anyio
async def test_fail_get_nba_players_limit_zero():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=None)
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?limit=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "greater_than"
    assert message == "Input should be greater than 0"


@pytest.mark.anyio
async def test_fail_get_nba_players_page_invalid_type():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=None)
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?page=abcdedfg")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "int_parsing"
    assert (
        message
        == "Input should be a valid integer, unable to parse string as an integer"
    )


@pytest.mark.anyio
async def test_fail_get_nba_players_page_limit_too_high():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=None)
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?limit=300")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "less_than_equal"
    assert message == "Input should be less than or equal to 100"


@pytest.mark.anyio
async def test_fail_get_nba_players_page_too_low():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=None)
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/?page=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "greater_than_equal"
    assert message == "Input should be greater than or equal to 1"


@pytest.mark.anyio
async def test_get_player(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=mock_p1)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/1630173")
        data = response.json().get("data", None)
        career_games = data.get("career", {}).get("totals", {}).get("games", 0)
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert data.get("_id") == 1630173
    assert data.get("full_name") == "Precious Achiuwa"
    assert career_games > 0
    assert message == "Player successfully retrieved."


@pytest.mark.anyio
async def test_fail_get_player(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/1231")
        message = response.json().get("detail", "").get("message")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Player with id 1231 not found."


@pytest.mark.anyio
async def test_fail_get_player_invalid_id_format():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/alsk{tsaxa}123")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert (
        message
        == "Input should be a valid integer, unable to parse string as an integer"
    )
    assert error_type == "int_parsing"


@pytest.mark.anyio
async def test_fail_get_player_invalid_id_too_low():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/9")
        print(response.json())
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be greater than 10"
    assert error_type == "greater_than"


@pytest.mark.anyio
async def test_fail_get_player_invalid_id_too_large():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/10000000")
        print(response.json())
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be less than 10000000"
    assert error_type == "less_than"


@pytest.mark.anyio
async def test_get_nba_player_by_slug(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=mock_p1)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/search/precious-achiuwa")
        player = response.json().get("data", [])
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Player successfully retrieved."
    assert player.get("_id") == 1630173
    assert player.get("full_name") == "Precious Achiuwa"


@pytest.mark.anyio
async def test_fail_get_nba_player_by_slug(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/search/precious-achiuwa")
        message = response.json().get("detail", "").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Player with slug precious-achiuwa not found."


@pytest.mark.anyio
async def test_fail_get_nba_player_by_slug_too_short():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/search/prec")
        message = response.json().get("detail", "")[0].get("msg", "")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "String should have at least 7 characters"


@pytest.mark.anyio
async def test_get_players_by_team_abbreviation(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.find.return_value.to_list = AsyncMock(return_value=[mock_p1, mock_p2])
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/team/mia")
        print(response)
        data = response.json().get("data")
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(data) > 0
    assert data[0].get("full_name") == "Precious Achiuwa"
    assert message == "Players from MIA successfully retrieved."


@pytest.mark.anyio
async def test_fail_get_players_by_team_abbreviation_not_found(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/team/mis")
        print(response)
        message = response.json().get("detail").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Players from MIS not found."


@pytest.mark.anyio
async def test_fail_get_players_by_team_abbreviation_too_short():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find.return_value.to_list = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/team/mi")
        print(response)
        message = response.json().get("detail")[0].get("msg", "")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "String should have at least 3 characters"


@pytest.mark.anyio
async def test_fail_get_players_by_team_abbreviation_too_long():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find.return_value.to_list = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/team/miami")
        print(response)
        message = response.json().get("detail")[0].get("msg", "")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "String should have at most 3 characters"


mock_opponent_team = {
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
    "actual_season": {"rank": None, "metrics": {}},
}


@pytest.mark.anyio
async def test_get_player_season_prediction():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=mock_p1)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_proj = {"pts": 18.0, "ast": 4.0, "reb": 5.0, "stl": 1.0, "blk": 0.5}
    with patch(
        "app.routers.players.calculate_player_year_prediction",
        new=AsyncMock(return_value=(mock_proj, 1.042)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            response = await ac.get(f"/players/{mock_p1['_id']}/predictions/season")
            data = response.json().get("data")
            message = response.json().get("message", "")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert data["player_id"] == mock_p1["_id"]
    assert data["projected_averages"] == mock_proj
    assert "confidence_intervals" in data
    assert message == "Player season prediction successfully calculated."


@pytest.mark.anyio
async def test_fail_get_player_season_prediction_not_found():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/999999/predictions/season")
        message = response.json().get("detail", {}).get("message", "")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert message == "Player with id 999999 not found."


@pytest.mark.anyio
async def test_fail_get_player_season_prediction_invalid_id():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/5/predictions/season")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_player_matchup_prediction_home():
    mock_db = MagicMock()

    def get_collection(name):
        mock_col = MagicMock()
        if name == "players":
            mock_col.find_one = AsyncMock(return_value=mock_p1)
        elif name == "teams":
            mock_col.find_one = AsyncMock(return_value=mock_opponent_team)
        return mock_col

    mock_db.__getitem__.side_effect = get_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(
            f"/players/{mock_p1['_id']}/predictions/matchup/1610612737?is_home=true"
        )
        data = response.json().get("data")
        message = response.json().get("message", "")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert data["player_id"] == mock_p1["_id"]
    assert data["opponent_id"] == 1610612737
    assert data["factors"]["is_home"] is True
    assert "projected_averages" in data
    assert "confidence_intervals" in data
    assert "succesfully retrieved" in message


@pytest.mark.anyio
async def test_get_player_matchup_prediction_away():
    mock_db = MagicMock()

    def get_collection(name):
        mock_col = MagicMock()
        if name == "players":
            mock_col.find_one = AsyncMock(return_value=mock_p1)
        elif name == "teams":
            mock_col.find_one = AsyncMock(return_value=mock_opponent_team)
        return mock_col

    mock_db.__getitem__.side_effect = get_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(
            f"/players/{mock_p1['_id']}/predictions/matchup/1610612737?is_home=false"
        )
        data = response.json().get("data")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert data["factors"]["is_home"] is False


@pytest.mark.anyio
async def test_fail_get_player_matchup_prediction_player_not_found():
    mock_db = MagicMock()

    def get_collection(name):
        mock_col = MagicMock()
        if name == "players":
            mock_col.find_one = AsyncMock(return_value=None)
        elif name == "teams":
            mock_col.find_one = AsyncMock(return_value=mock_opponent_team)
        return mock_col

    mock_db.__getitem__.side_effect = get_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/players/999999/predictions/matchup/1610612737")
        message = response.json().get("detail", {}).get("message", "")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert message == "Player with id 999999 not found."


@pytest.mark.anyio
async def test_fail_get_player_matchup_prediction_team_not_found():
    mock_db = MagicMock()

    def get_collection(name):
        mock_col = MagicMock()
        if name == "players":
            mock_col.find_one = AsyncMock(return_value=mock_p1)
        elif name == "teams":
            mock_col.find_one = AsyncMock(return_value=None)
        return mock_col

    mock_db.__getitem__.side_effect = get_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get(
            f"/players/{mock_p1['_id']}/predictions/matchup/1610612737"
        )
        message = response.json().get("detail", {}).get("message", "")
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "not found" in message


@pytest.mark.anyio
async def test_fail_get_player_matchup_prediction_invalid_ids():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Invalid player id (<= 10)
        res1 = await ac.get("/players/5/predictions/matchup/1610612737")
        assert res1.status_code == 422

        # Invalid opponent team id (<= 999999999)
        res2 = await ac.get(f"/players/{mock_p1['_id']}/predictions/matchup/100")
        assert res2.status_code == 422
