"""
Schemas Pydantic v2 para Ingestão de Telemetria de Sensores IoT no Campo.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SensorReadingSchema(BaseModel):
    """Leitura pontual de telemetria horária enviada pelo nodo de campo."""
    timestamp: Optional[str] = Field(default=None, description="Timestamp ISO 8601 da leitura")
    hour: Optional[int] = Field(default=None, ge=0, le=23, description="Hora do dia (0 a 23)")
    soil_moisture_surface_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Umidade volumétrica do solo na camada superficial (10 cm) em %",
    )
    soil_moisture_deep_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Umidade volumétrica do solo na camada profunda (30 cm) em %",
    )
    soil_temperature_celsius: float = Field(
        ...,
        description="Temperatura termométrica do solo (°C)",
    )
    leaf_wetness_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Índice biofísico de molhamento foliar (0.0 seco a 1.0 saturado)",
    )
    leaf_is_wet: bool = Field(
        ...,
        description="Indicador booleano de presença de filme d'água na folha para fitossanidade",
    )
    battery_voltage: float = Field(
        default=3.7,
        ge=0.0,
        description="Nível de tensão da bateria do nodo IoT (Volts)",
    )
    rssi_dbm: int = Field(
        default=-75,
        description="Potência do sinal de rádiofrequência LoRaWAN ou celular (dBm)",
    )


class IoTTelemetryIngestRequest(BaseModel):
    """Pacote em lote de telemetria de sensores de campo para a Camada Bronze."""
    device_id: str = Field(..., min_length=2, description="Identificador único de hardware do nodo")
    talhao_id: str = Field(default="talhao_01", description="Código do talhão agrícola associado")
    crop_id: str = Field(default="sugarcane", description="Cultura cultivada no talhão")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude da estação/sensor")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude da estação/sensor")
    firmware_version: str = Field(default="v2.4.1-lmic", description="Versão de firmware embarcado")
    readings: List[SensorReadingSchema] = Field(
        default_factory=list,
        description="Lista de leituras horárias capturadas pelos sensores",
    )


class IoTTelemetryIngestResponse(BaseModel):
    """Confirmação de ingestão do lote de telemetria na Camada Bronze."""
    status: str = Field(..., description="Status da operação ('success' ou 'partial_success')")
    device_id: str
    readings_count: int
    uploaded_to_cloud: bool
    blob_path: str
    backup_local: bool
    message: str
