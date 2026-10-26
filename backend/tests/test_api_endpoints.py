from httpx import AsyncClient


async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database_connected"] is True
    assert data["actuals_count"] == 3 * 48


async def test_day_ahead_uses_latest_forecast_published_before_cutoff(client: AsyncClient):
    response = await client.get("/decision/day-ahead", params={"delivery_date": "2026-01-15", "cutoff_hour": 11})
    assert response.status_code == 200
    data = response.json()

    assert data["decision_cutoff_used"] == "2026-01-14T11:00:00Z"
    assert data["periods_count"] == 48
    for p in data["settlement_periods"]:
        assert p["selected_publish_time"] == "2026-01-14T09:30:00Z"
        assert p["forecast_mw"] == 11000.0  # never the 99,999 MW forecast published after the cutoff
        assert p["error_mw"] == 1000.0
    assert data["day_mae_mw"] == 1000.0
    assert data["normalized_mae_pct"] == 10.0


async def test_later_cutoff_picks_later_forecast(client: AsyncClient):
    response = await client.get("/decision/day-ahead", params={"delivery_date": "2026-01-15", "cutoff_hour": 12})
    assert response.status_code == 200
    assert response.json()["settlement_periods"][0]["selected_publish_time"] == "2026-01-14T11:30:00Z"


async def test_day_ahead_unknown_day_returns_404(client: AsyncClient):
    response = await client.get("/decision/day-ahead", params={"delivery_date": "2026-01-25"})
    assert response.status_code == 404


async def test_monthly_evaluation(client: AsyncClient):
    response = await client.get("/evaluation/monthly", params={"start_date": "2026-01-13", "end_date": "2026-01-15"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_periods_evaluated"] == 3 * 48
    assert [d["date"] for d in data["daily_summary"]] == ["2026-01-13", "2026-01-14", "2026-01-15"]
    assert [d["mae_mw"] for d in data["daily_summary"]] == [500.0, 5000.0, 1000.0]
    assert len(data["diurnal_profile"]) == 48


async def test_horizon_analysis(client: AsyncClient):
    response = await client.get("/evaluation/horizon", params={"start_date": "2026-01-15", "end_date": "2026-01-15"})
    assert response.status_code == 200
    by_h = {h["horizon_hours"]: h for h in response.json()["horizons"]}

    # 1h ahead, every target can use the D-1 11:30 forecast
    assert by_h[1]["sample_count"] == 48
    assert by_h[1]["mae_mw"] == 89999.0
    # 48h ahead, only targets from 22:30 onwards have a forecast published 48h earlier (D-2 22:30)
    assert by_h[48]["sample_count"] == 3
    assert by_h[48]["mae_mw"] == 2000.0


async def test_procurement_buffer_has_no_look_ahead(client: AsyncClient):
    payload = {"delivery_date": "2026-01-15", "cutoff_hour": 11, "risk_tolerance": 1.0, "peak_demand_mw": 38000.0}
    response = await client.post("/procurement/advisor", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["buffer_history_end"] == "2026-01-13"
    assert len(data["schedule"]) == 48
    for row in data["schedule"]:
        # From D-2's 500 MW shortfall only: not D-1 (5,000 MW) and not D itself (1,000 MW)
        assert row["thermal_safety_buffer_mw"] == 500.0
        assert row["wind_forecast_mw"] == 11000.0
