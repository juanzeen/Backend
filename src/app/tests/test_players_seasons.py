from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock
import pytest
from ..main import app
from ..dependencies import get_db

mock_s1 = {
    "_id": "2544_2021-22",
    "player_id": 2544,
    "season_year": "2021-22",
    "team": {"abbreviation": "LAL", "name": "Los Angeles Lakers"},
    "season_totals": {
        "games_played": 56,
        "pts": 1695,
        "ast": 349,
        "reb": 459,
        "blk": 59,
        "stl": 73,
    },
    "season_averages": {"pts": 30.3, "ast": 6.2, "reb": 8.2, "blk": 1.1, "stl": 1.3},
    "season_peaks": {
        "max_pts": {
            "value": 56,
            "game_id": 22100959,
            "opponent": "GSW",
            "date": "2022-03-05",
        },
        "max_ast": {
            "value": 12,
            "game_id": 22101072,
            "opponent": "CLE",
            "date": "2022-03-21",
        },
        "max_reb": {
            "value": 15,
            "game_id": 22100854,
            "opponent": "GSW",
            "date": "2022-02-12",
        },
        "max_stl": {
            "value": 4,
            "game_id": 22100589,
            "opponent": "ATL",
            "date": "2022-01-07",
        },
        "max_blk": {
            "value": 4,
            "game_id": 22100985,
            "opponent": "HOU",
            "date": "2022-03-09",
        },
    },
    "performance_vs_teams": [
        {
            "team": "ATL",
            "games_played": 1,
            "avg_pts": 32.0,
            "avg_ast": 9.0,
            "avg_reb": 8.0,
            "avg_blk": 3.0,
            "avg_stl": 4.0,
        },
        {
            "team": "BKN",
            "games_played": 2,
            "avg_pts": 36.0,
            "avg_ast": 6.5,
            "avg_reb": 8.0,
            "avg_blk": 1.5,
            "avg_stl": 3.0,
        },
    ],
    "games": [
        {
            "game_id": 22101160,
            "date": "2022-04-01",
            "opponent": "NOP",
            "result": "L",
            "is_home": True,
            "playoffs": False,
            "minutes": "40",
            "pts": 38,
            "ast": 4,
            "reb": 8,
            "stl": 1,
            "blk": 0,
            "fg_pct": 0.565,
            "fg3_pct": 0.375,
            "ft_pct": 0.75,
        },
        {
            "game_id": 22100341,
            "date": "2021-12-03",
            "opponent": "LAC",
            "result": "L",
            "is_home": True,
            "playoffs": False,
            "minutes": "36",
            "pts": 23,
            "ast": 6,
            "reb": 11,
            "stl": 2,
            "blk": 0,
            "fg_pct": 0.391,
            "fg3_pct": 0.25,
            "ft_pct": 0.6,
        },
        {
            "game_id": 22100365,
            "date": "2021-12-07",
            "opponent": "BOS",
            "result": "W",
            "is_home": True,
            "playoffs": False,
            "minutes": "36",
            "pts": 30,
            "ast": 5,
            "reb": 4,
            "stl": 0,
            "blk": 0,
            "fg_pct": 0.684,
            "fg3_pct": 0.4,
            "ft_pct": 1.0,
        },
        {
            "game_id": 22100380,
            "date": "2021-12-09",
            "opponent": "MEM",
            "result": "L",
            "is_home": False,
            "playoffs": False,
            "minutes": "37",
            "pts": 20,
            "ast": 11,
            "reb": 10,
            "stl": 4,
            "blk": 2,
            "fg_pct": 0.467,
            "fg3_pct": 0.167,
            "ft_pct": 1.0,
        },
        {
            "game_id": 22100389,
            "date": "2021-12-10",
            "opponent": "OKC",
            "result": "W",
            "is_home": False,
            "playoffs": False,
            "minutes": "35",
            "pts": 33,
            "ast": 6,
            "reb": 5,
            "stl": 3,
            "blk": 2,
            "fg_pct": 0.65,
            "fg3_pct": 0.667,
            "ft_pct": 0.75,
        },
    ],
}

mock_s2 = {
    "_id": "2544_2022-23",
    "player_id": 2544,
    "season_year": "2022-23",
    "team": {"abbreviation": "LAL", "name": "Los Angeles Lakers"},
    "season_totals": {
        "games_played": 56,
        "pts": 1695,
        "ast": 349,
        "reb": 459,
        "blk": 59,
        "stl": 73,
    },
    "season_averages": {"pts": 30.3, "ast": 6.2, "reb": 8.2, "blk": 1.1, "stl": 1.3},
    "season_peaks": {
        "max_pts": {
            "value": 56,
            "game_id": 22100959,
            "opponent": "GSW",
            "date": "2022-03-05",
        },
        "max_ast": {
            "value": 12,
            "game_id": 22101072,
            "opponent": "CLE",
            "date": "2022-03-21",
        },
        "max_reb": {
            "value": 15,
            "game_id": 22100854,
            "opponent": "GSW",
            "date": "2022-02-12",
        },
        "max_stl": {
            "value": 4,
            "game_id": 22100589,
            "opponent": "ATL",
            "date": "2022-01-07",
        },
        "max_blk": {
            "value": 4,
            "game_id": 22100985,
            "opponent": "HOU",
            "date": "2022-03-09",
        },
    },
    "performance_vs_teams": [
        {
            "team": "ATL",
            "games_played": 1,
            "avg_pts": 32.0,
            "avg_ast": 9.0,
            "avg_reb": 8.0,
            "avg_blk": 3.0,
            "avg_stl": 4.0,
        },
        {
            "team": "BKN",
            "games_played": 2,
            "avg_pts": 36.0,
            "avg_ast": 6.5,
            "avg_reb": 8.0,
            "avg_blk": 1.5,
            "avg_stl": 3.0,
        },
    ],
    "games": [
        {
            "game_id": 22101160,
            "date": "2022-04-01",
            "opponent": "NOP",
            "result": "L",
            "is_home": True,
            "playoffs": False,
            "minutes": "40",
            "pts": 38,
            "ast": 4,
            "reb": 8,
            "stl": 1,
            "blk": 0,
            "fg_pct": 0.565,
            "fg3_pct": 0.375,
            "ft_pct": 0.75,
        },
        {
            "game_id": 22100341,
            "date": "2021-12-03",
            "opponent": "LAC",
            "result": "L",
            "is_home": True,
            "playoffs": False,
            "minutes": "36",
            "pts": 23,
            "ast": 6,
            "reb": 11,
            "stl": 2,
            "blk": 0,
            "fg_pct": 0.391,
            "fg3_pct": 0.25,
            "ft_pct": 0.6,
        },
        {
            "game_id": 22100365,
            "date": "2021-12-07",
            "opponent": "BOS",
            "result": "W",
            "is_home": True,
            "playoffs": False,
            "minutes": "36",
            "pts": 30,
            "ast": 5,
            "reb": 4,
            "stl": 0,
            "blk": 0,
            "fg_pct": 0.684,
            "fg3_pct": 0.4,
            "ft_pct": 1.0,
        },
        {
            "game_id": 22100380,
            "date": "2021-12-09",
            "opponent": "MEM",
            "result": "L",
            "is_home": False,
            "playoffs": False,
            "minutes": "37",
            "pts": 20,
            "ast": 11,
            "reb": 10,
            "stl": 4,
            "blk": 2,
            "fg_pct": 0.467,
            "fg3_pct": 0.167,
            "ft_pct": 1.0,
        },
        {
            "game_id": 22100389,
            "date": "2021-12-10",
            "opponent": "OKC",
            "result": "W",
            "is_home": False,
            "playoffs": False,
            "minutes": "35",
            "pts": 33,
            "ast": 6,
            "reb": 5,
            "stl": 3,
            "blk": 2,
            "fg_pct": 0.65,
            "fg3_pct": 0.667,
            "ft_pct": 0.75,
        },
    ],
}


@pytest.mark.anyio
async def test_get_player_seasons():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_s1, mock_s2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons")
        data = response.json().get("data", [])
        pagination = response.json().get("pagination", {})
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(data) > 1
    assert message == "Seasons from player with id 2544 successfully retrieved."
    assert pagination.get("page") == 1
    assert pagination.get("limit") == 10
    assert pagination.get("total_items") == 15
    assert pagination.get("total_pages") == 2
    assert pagination.get("has_next") is True
    assert pagination.get("has_previous") is False


@pytest.mark.anyio
async def test_get_player_seasons_custom_pagination():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_s1, mock_s2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons?page=2&limit=5")
        data = response.json().get("data", [])
        pagination_metadata = response.json().get("pagination", None)
        message = response.json().get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Seasons from player with id 2544 successfully retrieved."
    assert pagination_metadata.get("page") == 2
    assert pagination_metadata.get("limit") == 5
    assert pagination_metadata.get("total_items") == 15
    assert pagination_metadata.get("total_pages") == 3
    assert len(data) > 1


@pytest.mark.anyio
async def test_get_player_seasons_pagination_flags_first_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_s1, mock_s2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons?limit=5&page=1")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") is True
    assert pagination_meta.get("has_previous") is False


@pytest.mark.anyio
async def test_get_player_seasons_pagination_flags_last_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_s1, mock_s2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons?limit=5&page=3")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") is False
    assert pagination_meta.get("has_previous") is True


@pytest.mark.anyio
async def test_get_player_seasons_pagination_flags_middle_page():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mock_s1, mock_s2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons?limit=5&page=2")
        pagination_meta = response.json().get("pagination", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert pagination_meta.get("has_next") is True
    assert pagination_meta.get("has_previous") is True


@pytest.mark.anyio
async def test_fail_get_player_seasons_not_found_player_id():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/2544/seasons")
        message = response.json().get("detail").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Seasons from player with id 2544 not found."


@pytest.mark.anyio
async def test_fail_get_player_seasons_empty_list():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=0)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons")
        message = response.json().get("detail").get("message", "")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Seasons from player with id 2544 not found."


@pytest.mark.anyio
async def test_fail_get_player_seasons_limit_zero():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/2544/seasons?limit=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "greater_than"
    assert message == "Input should be greater than 0"


@pytest.mark.anyio
async def test_fail_get_player_seasons_page_limit_too_high():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/2544/seasons?limit=300")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "less_than_equal"
    assert message == "Input should be less than or equal to 100"


@pytest.mark.anyio
async def test_fail_get_player_seasons_page_too_low():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/2544/seasons?page=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert error_type == "greater_than_equal"
    assert message == "Input should be greater than or equal to 1"


@pytest.mark.anyio
async def test_fail_get_player_seasons_page_invalid_type():
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/2544/seasons?page=abcdedfg")
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
async def test_fail_get_player_seasons_invalid_player_id_too_short():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=None)
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
        response = await ac.get("/api/v1/players/9/seasons")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be greater than 10"
    assert error_type == "greater_than"


@pytest.mark.anyio
async def test_fail_get_player_seasons_invalid_player_id_boundary_lower():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=None)
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
        response = await ac.get("/api/v1/players/10/seasons")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be greater than 10"
    assert error_type == "greater_than"


@pytest.mark.anyio
async def test_fail_get_player_seasons_invalid_player_id_too_long():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/9999999999/seasons")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be less than 10000000"
    assert error_type == "less_than"


@pytest.mark.anyio
async def test_fail_get_player_seasons_invalid_player_id_boundary_upper():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/10000000/seasons")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be less than 10000000"
    assert error_type == "less_than"


@pytest.mark.anyio
async def test_fail_get_player_seasons_invalid_player_id_type():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=15)
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
        response = await ac.get("/api/v1/players/lebronjames/seasons")
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
async def test_get_player_season_by_year(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=mock_s2)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons/2022-23")
        message = response.json().get("message")
        data = response.json().get("data")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Season 2022-23 from player with id 2544 successfully retrieved."
    assert data.get("season_year") == "2022-23"
    assert data.get("_id") == "2544_2022-23"
    assert data.get("player_id") == 2544
    assert data.get("team", {}).get("abbreviation") == "LAL"
    assert data.get("season_totals", {}).get("pts") == 1695
    assert data.get("season_averages", {}).get("pts") == 30.3
    assert len(data.get("games")) > 0


@pytest.mark.anyio
async def test_fail_get_player_season_not_found(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons/1998-99")
        message = response.json().get("detail").get("message")
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Season 1998-99 from player with id 2544 not found."


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_season_too_short():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons/1998")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "String should have at least 7 characters"


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_season_too_long():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/2544/seasons/1998-1999")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "String should have at most 7 characters"


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_player_id_too_short():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/9/seasons/2022-23")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be greater than 10"
    assert error_type == "greater_than"


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_player_id_boundary_lower():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/10/seasons/2022-23")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be greater than 10"
    assert error_type == "greater_than"


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_player_id_too_long():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/9999999999/seasons/2022-23")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be less than 10000000"
    assert error_type == "less_than"


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_player_id_boundary_upper():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/10000000/seasons/2022-23")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert message == "Input should be less than 10000000"
    assert error_type == "less_than"


@pytest.mark.anyio
async def test_fail_get_player_season_invalid_player_id_type():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/players/lebronjames/seasons/2022-23")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert (
        message
        == "Input should be a valid integer, unable to parse string as an integer"
    )
    assert error_type == "int_parsing"
