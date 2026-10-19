"""
Schemas Pydantic v2 para requisições e respostas da API RESTful OmniCrop AI.
"""
from src.api.schemas.common import HealthResponse, ErrorResponse
from src.api.schemas.predict import (
    PredictNDVIRequest,
    PredictNDVIResponse,
    XAIWaterfallExplanation,
    DSSDecision,
)
from src.api.schemas.farm import (
    FarmCreate,
    FarmUpdate,
    FarmResponse,
)
from src.api.schemas.telemetry import (
    SensorReadingSchema,
    IoTTelemetryIngestRequest,
    IoTTelemetryIngestResponse,
)
from src.api.schemas.report import (
    ReportGenerateRequest,
    ReportGenerateResponse,
)
from src.api.schemas.mlops import (
    FeatureDriftDetail,
    DataDriftStatusResponse,
)

__all__ = [
    "HealthResponse",
    "ErrorResponse",
    "PredictNDVIRequest",
    "PredictNDVIResponse",
    "XAIWaterfallExplanation",
    "DSSDecision",
    "FarmCreate",
    "FarmUpdate",
    "FarmResponse",
    "SensorReadingSchema",
    "IoTTelemetryIngestRequest",
    "IoTTelemetryIngestResponse",
    "ReportGenerateRequest",
    "ReportGenerateResponse",
    "FeatureDriftDetail",
    "DataDriftStatusResponse",
]
