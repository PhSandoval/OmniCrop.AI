"""
Simulador de Telemetria de Sensores IoT no Campo - OmniCrop AI (Fase 3).
Gera telemetria sintética com ruído e comportamento biofísico realista para 3 sensores:
1. Humidade do Solo (% e capacidade de campo a 10cm e 30cm)
2. Temperatura do Solo (°C com inércia térmica e ciclo diurno senoidal)
3. Molhamento Foliar (Índice 0-1 e estado de orvalho/chuva noturno)

Grava o payload estruturado em JSON na Camada Bronze da Azure Blob Storage:
    bronze/iot_telemetry/year={year}/month={month}/telemetry_{execution_date}_{device_id}.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Adiciona a raiz do projeto ao sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class SensorReading:
    """Leitura individual de telemetria horária de um nodo IoT."""
    timestamp: str
    hour: int
    soil_moisture_surface_pct: float  # Profundidade 10 cm (0 - 100%)
    soil_moisture_deep_pct: float     # Profundidade 30 cm (0 - 100%)
    soil_temperature_celsius: float   # Temperatura do solo (°C)
    leaf_wetness_index: float         # 0.0 (seco) a 1.0 (saturado de orvalho/chuva)
    leaf_is_wet: bool                 # Indicador binário para modelos fitossanitários
    battery_voltage: float            # Tensão de bateria do nodo (ex: 3.6V - 4.2V Li-ion)
    rssi_dbm: int                     # Intensidade do sinal LoRa/4G (-115 a -50 dBm)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IoTTelemetryPayload:
    """Payload estruturado do dispositivo IoT para a Camada Bronze."""
    device_id: str
    talhao_id: str
    crop_id: str
    latitude: float
    longitude: float
    firmware_version: str
    generated_at: str
    period_start: str
    period_end: str
    total_readings: int
    readings: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def generate_iot_telemetry(
    device_id: str = "IOT-NODE-TALHAO-01",
    talhao_id: str = "talhao_01",
    crop_id: str = "sugarcane",
    latitude: float = -21.1767,
    longitude: float = -47.8208,
    start_time: Optional[datetime] = None,
    num_days: int = 1,
    random_seed: Optional[int] = 42,
) -> IoTTelemetryPayload:
    """
    Gera uma série temporal de 24 leituras por dia com dinâmicas físicas realistas:
    - Temperatura do solo: Ciclo solar com atraso térmico de 2 a 3 horas e ruído gaussiano.
    - Umidade do solo: Evapotranspiração diurna (queda gradual) e inércia em profundidade.
    - Molhamento foliar: Alta probabilidade de orvalho entre 00:00 e 07:00 da manhã.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    if start_time is None:
        # Padrão: Início do dia atual em UTC
        now = datetime.now(timezone.utc)
        start_time = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

    total_hours = num_days * 24
    readings: List[Dict[str, Any]] = []

    # Estado inicial dos sensores
    base_moisture_surf = float(np.random.uniform(28.0, 36.0))
    base_moisture_deep = base_moisture_surf + float(np.random.uniform(3.0, 6.0))
    base_soil_temp = 24.5

    # Simulação de evento esporádico de chuva em algum dia
    rain_events = {}
    for d in range(num_days):
        if np.random.rand() < 0.35:  # 35% de chance de chuva no dia
            rain_hour = int(np.random.randint(13, 19))
            rain_events[d * 24 + rain_hour] = float(np.random.uniform(8.0, 25.0))

    current_surf = base_moisture_surf
    current_deep = base_moisture_deep

    for step in range(total_hours):
        current_dt = start_time + timedelta(hours=step)
        hour = current_dt.hour

        # 1. TEMPERATURA DO SOLO (°C)
        # Pico diurno às 15:00, mínimo térmico às 06:00
        # Radiação solar modelada como senóide com atraso térmico de 3 horas
        solar_phase = (hour - 9) * (2 * np.pi / 24.0)
        temp_amplitude = 6.0  # amplitude térmica no solo superficial
        soil_temp = base_soil_temp + temp_amplitude * np.sin(solar_phase) + np.random.normal(0, 0.35)
        soil_temp = float(np.clip(soil_temp, 12.0, 42.0))

        # 2. UMIDADE DO SOLO (%)
        # Se houver chuva no passo:
        rain_mm = rain_events.get(step, 0.0)
        if rain_mm > 0.0:
            current_surf = min(85.0, current_surf + rain_mm * 1.8)
            current_deep = min(80.0, current_deep + rain_mm * 0.8)
        else:
            # Perda por evapotranspiração durante as horas de sol (10h às 17h)
            if 10 <= hour <= 17:
                et_loss = 0.35 + 0.15 * np.sin((hour - 10) * np.pi / 7.0)
                current_surf = max(10.0, current_surf - et_loss - np.random.uniform(0, 0.1))
                current_deep = max(14.0, current_deep - (et_loss * 0.4))
            else:
                # Perda mínima noturna
                current_surf = max(10.0, current_surf - 0.04)
                current_deep = max(14.0, current_deep - 0.02)

        # Ruído de leitura de capacitância dielétrica
        sensor_noise_surf = float(np.random.normal(0, 0.2))
        sensor_noise_deep = float(np.random.normal(0, 0.15))

        meas_moist_surf = float(np.clip(current_surf + sensor_noise_surf, 5.0, 95.0))
        meas_moist_deep = float(np.clip(current_deep + sensor_noise_deep, 8.0, 95.0))

        # 3. MOLHAMENTO FOLIAR (0.0 a 1.0)
        # Formação de orvalho durante a madrugada (01:00 às 07:00) ou durante chuva
        if rain_mm > 0.0:
            leaf_index = float(np.clip(0.85 + np.random.uniform(0, 0.15), 0.0, 1.0))
        elif 1 <= hour <= 7:
            # Pico de orvalho antes do amanhecer
            dew_intensity = np.sin((hour - 1) * np.pi / 6.0)
            leaf_index = float(np.clip(0.40 + 0.55 * dew_intensity + np.random.normal(0, 0.05), 0.0, 1.0))
        elif hour == 8:
            # Evaporação rápida do orvalho pelo sol nascente
            leaf_index = float(np.clip(0.15 + np.random.normal(0, 0.04), 0.0, 1.0))
        else:
            # Folha seca durante o dia
            leaf_index = float(np.clip(np.random.exponential(0.01), 0.0, 0.10))

        leaf_is_wet = bool(leaf_index >= 0.25)

        # 4. TELEMETRIA DO DISPOSITIVO (Bateria e Sinal)
        # Bateria decai sutilmente com o tempo
        battery_volt = float(round(4.12 - (step * 0.0008) + np.random.normal(0, 0.01), 2))
        rssi_val = int(np.clip(-75 + np.random.randint(-10, 10), -115, -45))

        reading = SensorReading(
            timestamp=current_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            hour=hour,
            soil_moisture_surface_pct=round(meas_moist_surf, 2),
            soil_moisture_deep_pct=round(meas_moist_deep, 2),
            soil_temperature_celsius=round(soil_temp, 2),
            leaf_wetness_index=round(leaf_index, 3),
            leaf_is_wet=leaf_is_wet,
            battery_voltage=battery_volt,
            rssi_dbm=rssi_val,
        )
        readings.append(reading.to_dict())

    end_time = start_time + timedelta(hours=total_hours - 1)

    payload = IoTTelemetryPayload(
        device_id=device_id,
        talhao_id=talhao_id,
        crop_id=crop_id,
        latitude=latitude,
        longitude=longitude,
        firmware_version="v2.4.1-lmic",
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        period_start=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        period_end=end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        total_readings=len(readings),
        readings=readings,
    )
    return payload


def upload_iot_telemetry_to_azure(
    payload: IoTTelemetryPayload,
    connection_string: Optional[str] = None,
    container_name: str = "omnicrop-data-lake-bronze",
    local_backup_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Faz o upload do payload estruturado em JSON para a Camada Bronze da Azure:
        bronze/iot_telemetry/year={year}/month={month}/telemetry_{execution_date}_{device_id}.json
    Em caso de ausência da chave ou modo offline, grava o payload localmente em disco.
    """
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    month = now.strftime("%m")
    execution_date = now.strftime("%Y%m%d_%H%M%S")
    clean_device = payload.device_id.replace(" ", "_").lower()

    blob_path = f"bronze/iot_telemetry/year={year}/month={month}/telemetry_{execution_date}_{clean_device}.json"
    json_bytes = payload.to_json(indent=2).encode("utf-8")

    azure_conn_str = connection_string or os.getenv("AZURE_CONNECTION_STRING")
    uploaded_to_cloud = False
    cloud_url = None

    if azure_conn_str:
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)
            container_client = blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()

            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)
            blob_client.upload_blob(json_bytes, overwrite=True)
            cloud_url = f"{container_name}/{blob_path}"
            uploaded_to_cloud = True
            print(f"✅ Telemetria IoT enviada com sucesso para o Azure: {cloud_url}")
        except Exception as e:
            print(f"⚠️ Falha no upload para o Azure Blob Storage ({e}). Prosseguindo com backup local.")

    # Gravação local de segurança
    if local_backup_dir is None:
        local_backup_dir = PROJECT_ROOT / "data" / "bronze" / "iot_telemetry" / f"year={year}" / f"month={month}"
    
    local_backup_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_backup_dir / f"telemetry_{execution_date}_{clean_device}.json"
    local_file.write_bytes(json_bytes)
    print(f"📁 Payload salvo localmente: {local_file}")

    return {
        "uploaded_to_cloud": uploaded_to_cloud,
        "cloud_path": cloud_url,
        "local_path": str(local_file),
        "total_readings": payload.total_readings,
        "device_id": payload.device_id,
        "talhao_id": payload.talhao_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Simulador de Telemetria de Sensores IoT no Campo - OmniCrop AI")
    parser.add_argument("--device-id", default="IOT-NODE-TALHAO-01", help="ID do hardware IoT")
    parser.add_argument("--talhao-id", default="talhao_01", help="Identificador do talhão da fazenda")
    parser.add_argument("--crop-id", default="sugarcane", choices=["sugarcane", "soybean", "corn"], help="Cultura plantada")
    parser.add_argument("--days", type=int, default=1, help="Quantidade de dias a simular (24h/dia)")
    parser.add_argument("--seed", type=int, default=42, help="Semente para reprodutibilidade estocástica")
    parser.add_argument("--no-upload", action="store_true", help="Apenas gera o arquivo local sem tentar Azure")

    args = parser.parse_args()

    print("📡 Simulando telemetria de sensores IoT de campo (Umidade, Temperatura do Solo, Molhamento Foliar)...")
    payload = generate_iot_telemetry(
        device_id=args.device_id,
        talhao_id=args.talhao_id,
        crop_id=args.crop_id,
        num_days=args.days,
        random_seed=args.seed,
    )

    print(f"✨ Geradas {payload.total_readings} leituras horárias para o dispositivo {payload.device_id} ({args.days} dia(s)).")

    conn_str = None if args.no_upload else os.getenv("AZURE_CONNECTION_STRING")
    result = upload_iot_telemetry_to_azure(payload, connection_string=conn_str)

    print("\nResumo da Operação IoT:")
    print(f"  - Dispositivo: {result['device_id']}")
    print(f"  - Leituras: {result['total_readings']}")
    print(f"  - Azure Cloud: {result['cloud_path'] if result['uploaded_to_cloud'] else 'Não conectado (local-only)'}")
    print(f"  - Backup Local: {result['local_path']}")


if __name__ == "__main__":
    main()
