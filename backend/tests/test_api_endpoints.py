import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Verifies that the /health endpoint confirms database connectivity."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True
    assert data["actuals_count"] > 1400
    assert data["forecasts_count"] > 30000


@pytest.mark.asyncio
async def test_day_ahead_decision_endpoint(client: AsyncClient):
    """Verifies that the /decision/day-ahead endpoint returns all 48 settlement periods."""
    response = await client.get(
        "/decision/day-ahead",
        params={"delivery_date": "2026-01-15", "cutoff_hour": 11},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["delivery_date"] == "2026-01-15"
    assert data["periods_count"] == 48
    assert len(data["settlement_periods"]) == 48
    assert data["day_rmse_mw"] >= data["day_mae_mw"]
    assert data["total_expected_generation_mwh"] > 0.0


@pytest.mark.asyncio
async def test_monthly_evaluation_endpoint(client: AsyncClient):
    """Verifies that the /evaluation/monthly endpoint computes full January 2026 statistics."""
    response = await client.get(
        "/evaluation/monthly",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31", "cutoff_hour": 11},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_periods_evaluated"] == 1488
    assert data["mae_mw"] > 0.0
    assert data["rmse_mw"] >= data["mae_mw"]
    assert data["normalized_mae_pct"] > 0.0
    assert len(data["diurnal_profile"]) == 48
    assert len(data["daily_summary"]) == 31


@pytest.mark.asyncio
async def test_procurement_advisor_endpoint(client: AsyncClient):
    """Verifies that the /procurement/advisor endpoint outputs a 48-period thermal hedging plan."""
    payload = {
        "delivery_date": "2026-01-15",
        "cutoff_hour": 11,
        "risk_tolerance": 1.0,
        "peak_demand_mw": 38000.0,
    }
    response = await client.post("/procurement/advisor", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["delivery_date"] == "2026-01-15"
    assert len(data["schedule"]) == 48
    assert data["total_recommended_thermal_procurement_mwh"] > 0.0
    assert data["total_thermal_safety_reserve_mwh"] > 0.0
