"""
Endpoints para Ingestão e Processamento de Telemetria de Sensores IoT no Campo.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from infra.simulate_iot_sensors import IoTTelemetryPayload, upload_iot_telemetry_to_azure
from src.api.schemas.telemetry import (
    IoTTelemetryIngestRequest,
    IoTTelemetryIngestResponse,
)

router = APIRouter()


@router.post(
    "/telemetry/iot",
    response_model=IoTTelemetryIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingestão de telemetria de sensores de solo e folha (IoT Edge)",
    description=(
        "Recebe leituras horárias de nodos de campo (tensiômetros de solo a 10cm/30cm, "
        "temperatura e molhamento foliar) e persiste o lote particionado na Camada Bronze da Azure Blob Storage."
    ),
)
def ingest_iot_telemetry(req: IoTTelemetryIngestRequest) -> IoTTelemetryIngestResponse:
    if not req.readings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O lote deve conter pelo menos uma leitura de sensor.",
        )

    readings_dicts = [r.model_dump() for r in req.readings]
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    period_start = req.readings[0].timestamp or now_utc
    period_end = req.readings[-1].timestamp or now_utc

    payload = IoTTelemetryPayload(
        device_id=req.device_id,
        talhao_id=req.talhao_id,
        crop_id=req.crop_id,
        latitude=req.latitude,
        longitude=req.longitude,
        firmware_version=req.firmware_version,
        generated_at=now_utc,
        period_start=period_start,
        period_end=period_end,
        total_readings=len(readings_dicts),
        readings=readings_dicts,
    )

    try:
        res = upload_iot_telemetry_to_azure(payload)
        uploaded = bool(res.get("uploaded_to_cloud", False))
        blob_path = str(res.get("cloud_path") or res.get("local_path", ""))
        return IoTTelemetryIngestResponse(
            status="success",
            device_id=payload.device_id,
            readings_count=len(readings_dicts),
            uploaded_to_cloud=uploaded,
            blob_path=blob_path,
            backup_local=True,
            message="Telemetria de campo ingerida na Camada Bronze com sucesso.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao persistir telemetria IoT na Camada Bronze: {e}",
        )
