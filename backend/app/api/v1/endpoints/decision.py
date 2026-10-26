from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import DayAheadDecisionResponse
from app.services.as_of_engine import AsOfEngine
from app.services.metrics_calculator import MetricsCalculator

router = APIRouter()
as_of_engine = AsOfEngine()
metrics_calculator = MetricsCalculator()


@router.get(
    "/day-ahead",
    response_model=DayAheadDecisionResponse,
    summary="Day-Ahead Decision View (48 Settlement Periods)",
    description="Returns the 48-period curve matching physical actuals against the latest forecast published before Gate Closure on D-1.",
)
async def get_day_ahead_decision(
    delivery_date: date = Query(
        default=date(2026, 1, 15),
        description="Delivery date, 2026-01-02 to 2026-02-01 (e.g. 2026-01-15)",
    ),
    cutoff_hour: int = Query(
        default=11,
        ge=0,
        le=23,
        description="Day-Ahead Gate Closure hour on D-1 in UTC (default: 11)",
    ),
    db: AsyncSession = Depends(get_db),
):
    snapshot = await as_of_engine.get_day_ahead_snapshot(
        session=db, delivery_date=delivery_date, cutoff_hour=cutoff_hour
    )

    if snapshot["periods_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No settlement data found for delivery date {delivery_date}. Run scripts/ingest_data.py to load Elexon data.",
        )

    kpis = metrics_calculator.calculate_daily_summary(snapshot["settlement_periods"])

    return DayAheadDecisionResponse(
        delivery_date=snapshot["delivery_date"],
        decision_cutoff_used=snapshot["decision_cutoff_used"],
        periods_count=snapshot["periods_count"],
        total_expected_generation_mwh=kpis["total_expected_generation_mwh"],
        total_actual_generation_mwh=kpis["total_actual_generation_mwh"],
        volume_imbalance_mwh=kpis["volume_imbalance_mwh"],
        day_mae_mw=kpis["day_mae_mw"],
        day_rmse_mw=kpis["day_rmse_mw"],
        day_bias_mw=kpis["day_bias_mw"],
        normalized_mae_pct=kpis["normalized_mae_pct"],
        peak_shortfall_mw=kpis["peak_shortfall_mw"],
        p90_shortfall_mw=kpis["p90_shortfall_mw"],
        settlement_periods=snapshot["settlement_periods"],
    )
