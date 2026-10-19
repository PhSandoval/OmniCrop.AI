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
from src.api.schemas.audit import AuditLogResponse
from src.api.schemas.jobs import (
    BatchKpisRequest,
    BatchReportsRequest,
    BatchRetrainRequest,
    JobSubmissionResponse,
    JobStatusResponse,
    JobListResponse,
    CacheStatsResponse,
    CacheClearResponse,
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
    "AuditLogResponse",
    "BatchKpisRequest",
    "BatchReportsRequest",
    "BatchRetrainRequest",
    "JobSubmissionResponse",
    "JobStatusResponse",
    "JobListResponse",
    "CacheStatsResponse",
    "CacheClearResponse",
]
