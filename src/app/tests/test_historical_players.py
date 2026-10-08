from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock
import pytest
from ..main import app
from ..dependencies import get_client, get_db

mocked_historical_player = {
    "_id": 200746,
    "career_peaks": {
        "max_ppg": {"value": 23.4, "season": "2014-15"},
        "max_apg": {"value": 2.6, "season": "2020-21"},
        "max_rpg": {"value": 11.1, "season": "2013-14"},
        "max_bpg": {"value": 2.2, "season": "2020-21"},
        "max_spg": {"value": 1, "season": "2010-11"},
    },
    "career_span": "2006-07 - 2021-22",
    "career_totals": {
        "games_played": 1102,
        "pts": 20910,
        "ast": 2125,
        "reb": 8854,
        "blk": 1216,
        "stl": 76,
    },
    "full_name": "LaMarcus Aldridge",
    "slug": "lamarcus-aldridge",
    "height": 211,
    "country": "USA",
    "position": "Center-Forward",
    "is_active": False,
    "honors": {"mvps": 0, "finals_mvps": 0, "all_stars": 7, "championships": 0},
    "seasons": [
        {
            "season_year": "2006-07",
            "team": "POR",
            "games_played": 63,
            "pts_avg": 9,
            "ast_avg": 0.4,
            "reb_avg": 5,
            "blk_avg": 1.2,
            "stl_avg": 0.3,
        },
        {
            "season_year": "2007-08",
            "team": "POR",
            "games_played": 76,
            "pts_avg": 17.8,
            "ast_avg": 1.6,
            "reb_avg": 7.6,
            "blk_avg": 1.2,
            "stl_avg": 0.7,
        },
    ],
}

mocked_historical_player_2 = {
    "_id": 2397,
    "career_peaks": {
        "max_ppg": {"value": 25, "season": "2006-07"},
        "max_apg": {"value": 2.3, "season": "2007-08"},
        "max_rpg": {"value": 10.8, "season": "2007-08"},
        "max_bpg": {"value": 2, "season": "2007-08"},
        "max_spg": {"value": 0.5, "season": "2005-06"},
    },
    "career_span": "2002-03 - 2010-11",
    "career_totals": {
        "games_played": 486,
        "pts": 9247,
        "ast": 769,
        "reb": 4494,
        "blk": 920,
        "stl": 18,
    },
    "full_name": "Yao Ming",
    "slug": "yao-ming",
    "height": 229,
    "country": "China",
    "honors": {"mvps": 0, "finals_mvps": 0, "all_stars": 6, "championships": 0},
    "is_active": False,
    "position": "Center",
    "seasons": [
        {
            "season_year": "2002-03",
            "team": "HOU",
            "games_played": 82,
            "pts_avg": 13.5,
            "ast_avg": 1.7,
            "reb_avg": 8.2,
            "blk_avg": 1.8,
            "stl_avg": 0.4,
        },
        {
            "season_year": "2003-04",
            "team": "HOU",
            "games_played": 82,
            "pts_avg": 17.5,
            "ast_avg": 1.5,
            "reb_avg": 9,
            "blk_avg": 1.9,
            "stl_avg": 0.3,
        },
        {
            "season_year": "2004-05",
            "team": "HOU",
            "games_played": 80,
            "pts_avg": 18.3,
            "ast_avg": 0.8,
            "reb_avg": 8.4,
            "blk_avg": 2,
            "stl_avg": 0.4,
        },
        {
            "season_year": "2005-06",
            "team": "HOU",
            "games_played": 57,
            "pts_avg": 22.3,
            "ast_avg": 1.5,
            "reb_avg": 10.2,
            "blk_avg": 1.6,
            "stl_avg": 0.5,
        },
        {
            "season_year": "2006-07",
            "team": "HOU",
            "games_played": 48,
            "pts_avg": 25,
            "ast_avg": 2,
            "reb_avg": 9.4,
            "blk_avg": 2,
            "stl_avg": 0.4,
        },
        {
            "season_year": "2007-08",
            "team": "HOU",
            "games_played": 55,
            "pts_avg": 22,
            "ast_avg": 2.3,
            "reb_avg": 10.8,
            "blk_avg": 2,
            "stl_avg": 0.5,
        },
        {
            "season_year": "2008-09",
            "team": "HOU",
            "games_played": 77,
            "pts_avg": 19.7,
            "ast_avg": 1.8,
            "reb_avg": 9.9,
            "blk_avg": 1.9,
            "stl_avg": 0.4,
        },
        {
            "season_year": "2010-11",
            "team": "HOU",
            "games_played": 5,
            "pts_avg": 10.2,
            "ast_avg": 0.8,
            "reb_avg": 5.4,
            "blk_avg": 1.6,
            "stl_avg": 0,
        },
    ],
}


@pytest.mark.anyio
async def test_get_historical_players():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(
        return_value=[mocked_historical_player, mocked_historical_player_2]
    )
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/")
        players = response.json().get("data", [])
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Historical players successfully retrieved."
    assert len(players) > 1


@pytest.mark.anyio
async def test_get_historical_players_custom_pagination():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(
        return_value=[mocked_historical_player, mocked_historical_player_2]
    )
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/?page=2&limit=5")
        players = response.json().get("data", [])
        pagination_metadata = response.json().get("pagination", None)
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Historical players successfully retrieved."
    assert pagination_metadata.get("page") == 2
    assert pagination_metadata.get("limit") == 5
    assert len(players) > 1


@pytest.mark.anyio
async def test_get_historical_players_pagination_flags_first_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(
        return_value=[mocked_historical_player, mocked_historical_player_2]
    )
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/?limit=10&page=1")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") == True
    assert pagination_meta.get("has_previous") == False


@pytest.mark.anyio
async def test_get_historical_players_pagination_flags_last_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(
        return_value=[mocked_historical_player, mocked_historical_player_2]
    )
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/?limit=10&page=16")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") == False
    assert pagination_meta.get("has_previous") == True


@pytest.mark.anyio
async def test_get_historical_players_pagination_flags_middle_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=160)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(
        return_value=[mocked_historical_player, mocked_historical_player_2]
    )
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/?limit=10&page=10")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") == True
    assert pagination_meta.get("has_previous") == True


@pytest.mark.anyio
async def test_fail_get_historical_players():
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
        response = await ac.get("/historical-players/")
        players = response.json().get("data", [])
        message = response.json().get("detail", "").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Historical players not found."
    assert len(players) == 0


@pytest.mark.anyio
async def test_fail_get_historical_players_page_too_low():
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
        response = await ac.get("/historical-players/?page=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "greater_than_equal"
    assert message == "Input should be greater than or equal to 1"


@pytest.mark.anyio
async def test_fail_get_historical_players_limit_zero():
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
        response = await ac.get("/historical-players/?limit=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "greater_than"
    assert message == "Input should be greater than 0"


@pytest.mark.anyio
async def test_fail_get_historical_players_page_invalid_type():
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
        response = await ac.get("/historical-players/?page=abcdedfg")
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
async def test_fail_get_historical_players_page_limit_too_high():
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
        response = await ac.get("/historical-players/?limit=300")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "less_than_equal"
    assert message == "Input should be less than or equal to 100"


@pytest.mark.anyio
async def test_get_historical_player_by_id(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=mocked_historical_player)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/200746")
        player = response.json().get("data", [])
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Player successfully retrieved."
    assert player.get("_id") == 200746
    assert player.get("full_name") == "LaMarcus Aldridge"


@pytest.mark.anyio
async def test_fail_get_historical_player_by_id(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/123123")
        message = response.json().get("detail", "").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Player with id 123123 not found."


@pytest.mark.anyio
async def test_fail_get_historical_player_by_id_small_id():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/1")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be greater than or equal to 10"


@pytest.mark.anyio
async def test_fail_get_historical_player_by_id_big_id():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/123321987")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be less than 1000000"


@pytest.mark.anyio
async def test_get_historical_player_by_slug(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=mocked_historical_player)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/search/lamarcus-aldridge")
        player = response.json().get("data", [])
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Player successfully retrieved."
    assert player.get("_id") == 200746
    assert player.get("full_name") == "LaMarcus Aldridge"


@pytest.mark.anyio
async def test_fail_get_historical_player_by_slug(mock_redis):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/search/lamarcuz-aldridg")
        message = response.json().get("detail", "").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Player with slug lamarcuz-aldridg not found."


@pytest.mark.anyio
async def test_fail_get_historical_player_by_id_too_short():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/historical-players/search/leb")
        message = response.json().get("detail", "")[0].get("msg", "")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "String should have at least 8 characters"
