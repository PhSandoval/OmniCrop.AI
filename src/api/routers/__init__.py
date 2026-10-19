"""
Roteadores da API RESTful OmniCrop AI.
"""
from src.api.routers.health import router as health_router
from src.api.routers.predict import router as predict_router
from src.api.routers.farms import router as farms_router
from src.api.routers.telemetry import router as telemetry_router
from src.api.routers.reports import router as reports_router
from src.api.routers.mlops import router as mlops_router

__all__ = [
    "health_router",
    "predict_router",
    "farms_router",
    "telemetry_router",
    "reports_router",
    "mlops_router",
]
