from fastapi import APIRouter
from app.api.v1.endpoints import health, decision, evaluation, procurement

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(decision.router, prefix="/decision", tags=["Day-Ahead Decision Cockpit"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Accuracy & Risk Lab"])
api_router.include_router(procurement.router, prefix="/procurement", tags=["Thermal Procurement Advisor"])
