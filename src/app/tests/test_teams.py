from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock
import pytest
from ..main import app
from ..dependencies import get_db

mocked_team_1 = {
    "_id": 1610612737,
    "abbreviation": "ATL",
    "name": "Atlanta Hawks",
    "city": "Atlanta",
    "conference": "East",
    "division": "Southeast",
    "founded_in": 1949,
    "championships": 1,
    "last_season": {
        "rank": 16,
        "record": {
            "wins": 46,
            "losses": 36,
            "win_pct": 0.561,
        },
        "power_ranking": {
            "rank": 13,
            "tier": "Play-in Contender",
            "power_score": 59.1,
            "trend": "+3",
        },
        "metrics": {
            "pace": 102.5,
            "offensive_rating": 115.0,
            "defensive_rating": 112.9,
            "net_rating": 2.2,
            "pts_per_game": 118.2,
            "pts_allowed_per_game": 119.3,
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
            "tier": None,
            "power_score": None,
            "trend": None,
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

mocked_team_2 = {
    "_id": 1610612738,
    "abbreviation": "BOS",
    "name": "Boston Celtics",
    "city": "Boston",
    "conference": "East",
    "division": "Atlantic",
    "founded_in": 1946,
    "championships": 18,
    "last_season": {
        "rank": 1,
        "record": {
            "wins": 64,
            "losses": 18,
            "win_pct": 0.78,
        },
        "power_ranking": {
            "rank": 1,
            "tier": "Championship Contender",
            "power_score": 95.0,
            "trend": "0",
        },
        "metrics": {
            "pace": 98.5,
            "offensive_rating": 122.2,
            "defensive_rating": 110.6,
            "net_rating": 11.6,
            "pts_per_game": 120.6,
            "pts_allowed_per_game": 109.2,
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
            "tier": None,
            "power_score": None,
            "trend": None,
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


@pytest.mark.anyio
async def test_get_teams():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mocked_team_1, mocked_team_2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/")
        data = response.json().get("data", [])
        pagination_meta = response.json().get("pagination", {})
        message = response.json().get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(data) == 2
    assert message == "Teams successfully retrieved."
    assert pagination_meta.get("page") == 1
    assert pagination_meta.get("limit") == 10
    assert pagination_meta.get("total_items") == 30
    assert pagination_meta.get("total_pages") == 3
    assert pagination_meta.get("has_next") is True
    assert pagination_meta.get("has_previous") is False
    assert data[0]["_id"] == 1610612737
    assert data[0]["abbreviation"] == "ATL"
    assert data[0]["name"] == "Atlanta Hawks"
    assert data[1]["_id"] == 1610612738
    assert data[1]["abbreviation"] == "BOS"
    assert data[1]["name"] == "Boston Celtics"


@pytest.mark.anyio
async def test_get_teams_custom_pagination():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mocked_team_1, mocked_team_2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/?page=2&limit=5")
        data = response.json().get("data", [])
        pagination_metadata = response.json().get("pagination", {})
        message = response.json().get("message", "")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert message == "Teams successfully retrieved."
    assert pagination_metadata.get("page") == 2
    assert pagination_metadata.get("limit") == 5
    assert pagination_metadata.get("total_items") == 30
    assert pagination_metadata.get("total_pages") == 6
    assert pagination_metadata.get("has_next") is True
    assert pagination_metadata.get("has_previous") is True
    assert len(data) == 2


@pytest.mark.anyio
async def test_get_teams_pagination_flags_first_page():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mocked_team_1, mocked_team_2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/?limit=10&page=1")
        pagination_meta = response.json().get("pagination", {})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert pagination_meta.get("has_next") is True
    assert pagination_meta.get("has_previous") is False


@pytest.mark.anyio
async def test_get_teams_pagination_flags_last_page():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mocked_team_1, mocked_team_2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/?limit=10&page=3")
        pagination_meta = response.json().get("pagination", {})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert pagination_meta.get("has_next") is False
    assert pagination_meta.get("has_previous") is True


@pytest.mark.anyio
async def test_get_teams_pagination_flags_middle_page():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[mocked_team_1, mocked_team_2])
    mock_collection.find.return_value = mock_cursor
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/?limit=10&page=2")
        pagination_meta = response.json().get("pagination", {})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert pagination_meta.get("has_next") is True
    assert pagination_meta.get("has_previous") is True


@pytest.mark.anyio
async def test_fail_get_teams_not_found_none():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=0)
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
        response = await ac.get("/api/v1/teams/")
        data = response.json().get("data", [])
        message = response.json().get("detail", {}).get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert message == "Teams not found."
    assert len(data) == 0


@pytest.mark.anyio
async def test_fail_get_teams_not_found_empty_array():
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
        response = await ac.get("/api/v1/teams/")
        data = response.json().get("data", [])
        message = response.json().get("detail", {}).get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert message == "Teams not found."
    assert len(data) == 0


@pytest.mark.anyio
async def test_fail_get_teams_page_too_low():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
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
        response = await ac.get("/api/v1/teams/?page=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert error_type == "greater_than_equal"
    assert message == "Input should be greater than or equal to 1"


@pytest.mark.anyio
async def test_fail_get_teams_limit_zero():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
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
        response = await ac.get("/api/v1/teams/?limit=0")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert error_type == "greater_than"
    assert message == "Input should be greater than 0"


@pytest.mark.anyio
async def test_fail_get_teams_page_invalid_type():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
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
        response = await ac.get("/api/v1/teams/?page=abcdedfg")
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
async def test_fail_get_teams_limit_too_high():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    mock_collection.count_documents = AsyncMock(return_value=30)
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
        response = await ac.get("/api/v1/teams/?limit=300")
        error_type = response.json().get("detail")[0].get("type")
        message = response.json().get("detail")[0].get("msg")
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert error_type == "less_than_equal"
    assert message == "Input should be less than or equal to 100"


@pytest.mark.anyio
async def test_get_team_by_id():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=mocked_team_1)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/1610612737")
        data = response.json().get("data", None)
        message = response.json().get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert message == "Team with id 1610612737 successfully retrieved."
    assert data is not None
    assert data["_id"] == 1610612737
    assert data["name"] == "Atlanta Hawks"
    assert data["abbreviation"] == "ATL"
    assert data["last_season"]["rank"] == 16
    assert data["last_season"]["record"]["wins"] == 46


@pytest.mark.anyio
async def test_fail_get_team_by_id_not_found():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/1610612799")
        message = response.json().get("detail", {}).get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert message == "Team with id 1610612799 not found."


@pytest.mark.anyio
async def test_fail_get_team_by_id_below_minimum():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/123")
        detail = response.json().get("detail", [])
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert detail[0]["type"] == "greater_than"


@pytest.mark.anyio
async def test_fail_get_team_by_id_boundary_minimum():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/999999999")
        detail = response.json().get("detail", [])
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert detail[0]["type"] == "greater_than"


@pytest.mark.anyio
async def test_fail_get_team_by_id_not_integer():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/invalid_team_id")
        detail = response.json().get("detail", [])
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert detail[0]["type"] == "int_parsing"


@pytest.mark.anyio
async def test_get_team_by_abbreviation():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=mocked_team_1)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/search/ATL/")
        data = response.json().get("data", None)
        message = response.json().get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert message == "Team ATL successfully retrieved."
    assert data is not None
    assert data["_id"] == 1610612737
    assert data["abbreviation"] == "ATL"
    assert data["name"] == "Atlanta Hawks"


@pytest.mark.anyio
async def test_fail_get_team_by_abbreviation_not_found():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/search/XYZ/")
        message = response.json().get("detail", {}).get("message", None)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert message == "Team XYZ not found."


@pytest.mark.anyio
async def test_fail_get_team_by_abbreviation_too_short():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/search/AT/")
        detail = response.json().get("detail", [])
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert detail[0]["type"] == "string_too_short"


@pytest.mark.anyio
async def test_fail_get_team_by_abbreviation_too_long():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/teams/search/ATLA/")
        detail = response.json().get("detail", [])
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert detail[0]["type"] == "string_too_long"
