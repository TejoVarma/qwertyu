from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.models import MonthlyAccuracyMetrics, DailySummaryItem, HorizonAnalysisResponse, HorizonMetric
from app.services.as_of_engine import AsOfEngine
from app.services.metrics_calculator import MetricsCalculator

router = APIRouter()
as_of_engine = AsOfEngine()
metrics_calculator = MetricsCalculator()


@router.get(
    "/monthly",
    response_model=MonthlyAccuracyMetrics,
    summary="Accuracy of the forecasts available at decision time (January 2026 decisions)",
    description="Computes MAE, RMSE, Bias, MAE relative to mean generation, P90/P95 downside risk, diurnal profiles across SP 1-48, and daily roll-ups.",
)
async def get_monthly_evaluation(
    start_date: date = Query(default=settings.EVALUATION_START_DATE, description="First delivery day (decision taken on the day before)"),
    end_date: date = Query(default=settings.EVALUATION_END_DATE, description="Last delivery day"),
    cutoff_hour: int = Query(default=11, ge=0, le=23, description="Decision cutoff hour on D-1 (UTC)"),
    db: AsyncSession = Depends(get_db),
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    points = await as_of_engine.get_range_snapshot(
        session=db, start_date=start_date, end_date=end_date, cutoff_hour=cutoff_hour
    )

    if not points:
        raise HTTPException(
            status_code=404,
            detail=f"No data found in range {start_date} to {end_date}. Ensure database is ingested.",
        )

    if (start_date, end_date) == (settings.EVALUATION_START_DATE, settings.EVALUATION_END_DATE):
        month_label = "January 2026 decisions (delivery 2 Jan - 1 Feb)"
    else:
        month_label = f"Delivery {start_date} to {end_date}"
    stats = metrics_calculator.calculate_monthly_metrics(points, month_label=month_label)

    return MonthlyAccuracyMetrics(**stats)


@router.get(
    "/daily-log",
    response_model=list[DailySummaryItem],
    summary="Daily Accuracy Roll-up Log",
    description="Returns day-by-day expected vs actual energy, MAE, RMSE, and bias across the evaluation window.",
)
async def get_daily_log(
    start_date: date = Query(default=settings.EVALUATION_START_DATE),
    end_date: date = Query(default=settings.EVALUATION_END_DATE),
    cutoff_hour: int = Query(default=11, ge=0, le=23),
    db: AsyncSession = Depends(get_db),
):
    points = await as_of_engine.get_range_snapshot(
        session=db, start_date=start_date, end_date=end_date, cutoff_hour=cutoff_hour
    )
    if not points:
        return []
    
    stats = metrics_calculator.calculate_monthly_metrics(points)
    return stats["daily_summary"]


@router.get(
    "/horizon",
    response_model=HorizonAnalysisResponse,
    summary="Forecast Error by Forecast Horizon",
    description=(
        "For each horizon h, uses the latest forecast published at least h hours before each delivery "
        "half-hour and reports its error statistics. Shows how much accuracy is lost by deciding earlier."
    ),
)
async def get_horizon_analysis(
    start_date: date = Query(default=settings.EVALUATION_START_DATE),
    end_date: date = Query(default=settings.EVALUATION_END_DATE),
    db: AsyncSession = Depends(get_db),
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    horizons = []
    for h in settings.HORIZON_HOURS:
        pairs = await as_of_engine.get_horizon_pairs(db, start_date, end_date, h)
        horizons.append(HorizonMetric(**metrics_calculator.calculate_horizon_metrics(h, pairs)))

    return HorizonAnalysisResponse(start_date=start_date, end_date=end_date, horizons=horizons)
