from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models import WindActual, WindForecast, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System Health & Database Verification")
async def get_health(db: AsyncSession = Depends(get_db)):
    """
    Verifies API status and database connectivity, returning record counts
    for both physical actuals (FUELHH) and published forecasts (WINDFOR).
    """
    db_connected = False
    actuals_count = 0
    forecasts_count = 0

    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        db_connected = True

        # Query counts
        actuals_count = (await db.execute(select(func.count(WindActual.id)))).scalar_one()
        forecasts_count = (await db.execute(select(func.count(WindForecast.id)))).scalar_one()
    except Exception:
        db_connected = False

    return HealthResponse(
        status="ok" if db_connected else "degraded",
        database_connected=db_connected,
        actuals_count=actuals_count,
        forecasts_count=forecasts_count,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )
