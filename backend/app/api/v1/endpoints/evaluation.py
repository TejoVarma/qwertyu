from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import MonthlyAccuracyMetrics, DailySummaryItem
from app.services.as_of_engine import AsOfEngine
from app.services.metrics_calculator import MetricsCalculator

router = APIRouter()
as_of_engine = AsOfEngine()
metrics_calculator = MetricsCalculator()


@router.get(
    "/monthly",
    response_model=MonthlyAccuracyMetrics,
    summary="January 2026 Monthly Quantitative Accuracy Metrics",
    description="Computes MAE, RMSE, Bias, nMAE, P90/P95 downside risk, diurnal profiles across SP 1-48, and daily roll-ups.",
)
async def get_monthly_evaluation(
    start_date: date = Query(default=date(2026, 1, 1), description="Start date of evaluation window"),
    end_date: date = Query(default=date(2026, 1, 31), description="End date of evaluation window"),
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

    month_label = f"{start_date.strftime('%B %Y')}" if start_date.month == end_date.month else f"{start_date} to {end_date}"
    stats = metrics_calculator.calculate_monthly_metrics(points, month_label=month_label)

    return MonthlyAccuracyMetrics(**stats)


@router.get(
    "/daily-log",
    response_model=list[DailySummaryItem],
    summary="Daily Accuracy Roll-up Log",
    description="Returns day-by-day expected vs actual energy, MAE, RMSE, and bias across the evaluation window.",
)
async def get_daily_log(
    start_date: date = Query(default=date(2026, 1, 1)),
    end_date: date = Query(default=date(2026, 1, 31)),
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
