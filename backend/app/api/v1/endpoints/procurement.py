from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import ProcurementAdvisorRequest, ProcurementAdvisorResponse
from app.services.as_of_engine import AsOfEngine
from app.services.procurement_advisor import ProcurementAdvisor

router = APIRouter()
as_of_engine = AsOfEngine()
procurement_advisor = ProcurementAdvisor()


@router.post(
    "/advisor",
    response_model=ProcurementAdvisorResponse,
    summary="Calculate Thermal Procurement Schedule & Reserve Buffer",
    description="Translates the 48-period Day-Ahead wind forecast and P90 error risk into a recommended thermal hedge.",
)
async def calculate_procurement_advice(
    req: ProcurementAdvisorRequest,
    db: AsyncSession = Depends(get_db),
):
    snapshot = await as_of_engine.get_day_ahead_snapshot(
        session=db, delivery_date=req.delivery_date, cutoff_hour=req.cutoff_hour
    )

    if snapshot["periods_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No settlement data found for delivery date {req.delivery_date}.",
        )

    advice = procurement_advisor.calculate_procurement_schedule(
        settlement_points=snapshot["settlement_periods"],
        risk_tolerance=req.risk_tolerance,
        peak_demand_mw=req.peak_demand_mw,
        custom_demand=req.custom_demand,
    )

    return ProcurementAdvisorResponse(
        delivery_date=snapshot["delivery_date"],
        decision_cutoff_used=snapshot["decision_cutoff_used"],
        risk_tolerance_coefficient=advice["risk_tolerance_coefficient"],
        risk_tolerance_label=advice["risk_tolerance_label"],
        peak_consumer_demand_mw=advice["peak_consumer_demand_mw"],
        total_consumer_demand_mwh=advice["total_consumer_demand_mwh"],
        total_expected_wind_mwh=advice["total_expected_wind_mwh"],
        total_recommended_thermal_procurement_mwh=advice["total_recommended_thermal_procurement_mwh"],
        total_thermal_safety_reserve_mwh=advice["total_thermal_safety_reserve_mwh"],
        average_thermal_buffer_mw=advice["average_thermal_buffer_mw"],
        schedule=advice["schedule"],
    )
