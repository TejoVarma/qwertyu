from datetime import date, datetime, timezone
import httpx
import pytest
from app.services.elexon_service import ElexonService, ElexonFetchError


def _service(handler) -> ElexonService:
    return ElexonService(base_url="https://elexon.test", transport=httpx.MockTransport(handler))


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


async def test_actuals_keep_only_wind_and_deduplicate():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/datasets/FUELHH/stream"
        return httpx.Response(200, json=[
            {"startTime": "2026-01-15T00:00:00Z", "settlementPeriod": 1, "fuelType": "WIND", "generation": 14602},
            {"startTime": "2026-01-15T00:00:00Z", "settlementPeriod": 1, "fuelType": "WIND", "generation": 14602},
            {"startTime": "2026-01-15T00:00:00Z", "settlementPeriod": 1, "fuelType": "CCGT", "generation": 9000},
        ])

    records = await _service(handler).fetch_actual_wind(date(2026, 1, 15), date(2026, 1, 15))

    assert len(records) == 1
    assert records[0]["generation"] == 14602.0
    assert records[0]["settlement_period"] == 1


async def test_hourly_forecasts_are_held_for_the_following_half_hour():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[
            {"publishTime": "2026-01-14T09:30:00Z", "startTime": "2026-01-15T00:00:00Z", "generation": 15828},
            # Published exactly at the window end: belongs to the next window, must be skipped here
            {"publishTime": "2026-01-15T00:00:00Z", "startTime": "2026-01-15T03:00:00Z", "generation": 1},
        ])

    records = await _service(handler).fetch_forecast_wind(_utc(2026, 1, 14), _utc(2026, 1, 15))

    assert [(r["start_time"], r["settlement_period"], r["generation"]) for r in records] == [
        (_utc(2026, 1, 15, 0, 0), 1, 15828.0),
        (_utc(2026, 1, 15, 0, 30), 2, 15828.0),
    ]
    assert all(r["publish_time"] == _utc(2026, 1, 14, 9, 30) for r in records)


async def test_http_errors_fail_loudly():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    with pytest.raises(ElexonFetchError):
        await _service(handler).fetch_forecast_wind(_utc(2026, 1, 14), _utc(2026, 1, 15))
