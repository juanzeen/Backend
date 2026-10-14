from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock
import pytest
from ..main import app
from ..dependencies import get_db


@pytest.mark.anyio
async def test_get_historical_records(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find.return_value.to_list = AsyncMock(
        return_value=[
            {
                "value": 43440,
                "record": "ALL_TIME_PTS",
                "leader_id": 2544,
                "leader_full_name": "LeBron James",
                "is_active": True,
                "details": {"season": "", "team": ""},
            },
            {
                "value": 15806,
                "record": "ALL_TIME_AST",
                "leader_id": 304,
                "leader_full_name": "John Stockton",
                "is_active": False,
                "details": {"season": "", "team": ""},
            },
        ]
    )
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://") as ac:
        response = await ac.get("/api/v1/historical-records/")
        print(response)
        data = response.json().get("data", [])
        message = response.json().get("message", None)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(data) > 0
    assert message == "Historical records successfully retrieved."


@pytest.mark.anyio
async def test_fail_get_historical_records(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find.return_value.to_list = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/historical-records/")
        message = response.json().get("detail", None).get("message", None)
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Historical records not found."


@pytest.mark.anyio
async def test_fail_get_historical_records_empty_array(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find.return_value.to_list = AsyncMock(return_value=[])
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/historical-records/")
        message = response.json().get("detail", None).get("message", None)
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Historical records not found."


@pytest.mark.anyio
async def test_get_historical_record_by_category(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(
        return_value={
            "value": 43440,
            "record": "ALL_TIME_PTS",
            "leader_id": 2544,
            "leader_full_name": "LeBron James",
            "is_active": True,
            "details": {"season": "", "team": ""},
        },
    )
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/historical-records/ALL_TIME_PTS")
        data = response.json().get("data", None)
        message = response.json().get("message", [])
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert message == "Historical record ALL_TIME_PTS successfully retrieved."
    assert data is not None


@pytest.mark.anyio
async def test_fail_get_historical_record_by_category_inexistent_category(mock_redis):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/historical-records/AL_TIME_PT")
        message = response.json().get("detail").get("message", [])
    app.dependency_overrides.clear()
    assert response.status_code == 404
    assert message == "Historical record AL_TIME_PT not found."


@pytest.mark.anyio
async def test_fail_get_historical_record_by_category_short_category():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/historical-records/ALL_TIME_POINTS")
        message = response.json().get("detail")[0].get("msg")
        detail = response.json().get("detail")[0].get("type")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert detail == "string_too_long"

    assert message == "String should have at most 13 characters"


@pytest.mark.anyio
async def test_fail_get_historical_record_by_category_long_category():
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_db.__getitem__.return_value = mock_collection
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/historical-records/AA")
        message = response.json().get("detail")[0].get("msg")
        detail = response.json().get("detail")[0].get("type")
    app.dependency_overrides.clear()
    assert response.status_code == 422
    assert detail == "string_too_short"
    assert message == "String should have at least 8 characters"
