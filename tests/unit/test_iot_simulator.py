"""
Testes Unitários para o Simulador de Telemetria de Sensores IoT no Campo (Fase 3).
Verifica a integridade do payload estruturado, granularidade horária de 24 leituras/dia,
comportamento físico e limites dos sensores (umidade, temperatura e molhamento foliar).
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infra.simulate_iot_sensors import (
    generate_iot_telemetry,
    upload_iot_telemetry_to_azure,
    IoTTelemetryPayload,
    SensorReading,
)


def test_generate_iot_telemetry_one_day():
    """Valida geração de 24 leituras horárias para 1 dia."""
    payload = generate_iot_telemetry(
        device_id="NODE-TEST-01",
        talhao_id="talhao_01",
        crop_id="sugarcane",
        num_days=1,
        random_seed=42,
    )
    assert isinstance(payload, IoTTelemetryPayload)
    assert payload.device_id == "NODE-TEST-01"
    assert payload.talhao_id == "talhao_01"
    assert payload.crop_id == "sugarcane"
    assert payload.total_readings == 24
    assert len(payload.readings) == 24

    # Verifica sequenciamento das horas (0 a 23)
    hours = [r["hour"] for r in payload.readings]
    assert hours == list(range(24))


def test_generate_iot_telemetry_multi_day():
    """Valida geração de múltiplos dias (ex: 3 dias = 72 leituras)."""
    payload = generate_iot_telemetry(
        device_id="NODE-TEST-02",
        num_days=3,
        random_seed=123,
    )
    assert payload.total_readings == 72
    assert len(payload.readings) == 72


def test_iot_sensor_values_physical_bounds():
    """Garante que as leituras sintéticas respeitem limites biofísicos reais."""
    payload = generate_iot_telemetry(num_days=2, random_seed=999)

    for reading in payload.readings:
        # Temperatura do solo: entre 12°C e 42°C
        assert 12.0 <= reading["soil_temperature_celsius"] <= 42.0

        # Umidade superficial (10cm) e profunda (30cm): entre 5% e 95%
        assert 5.0 <= reading["soil_moisture_surface_pct"] <= 95.0
        assert 8.0 <= reading["soil_moisture_deep_pct"] <= 95.0

        # Molhamento foliar: índice entre 0.0 e 1.0
        assert 0.0 <= reading["leaf_wetness_index"] <= 1.0
        assert isinstance(reading["leaf_is_wet"], bool)

        # Telemetria do hardware (Bateria e sinal)
        assert 3.5 <= reading["battery_voltage"] <= 4.3
        assert -115 <= reading["rssi_dbm"] <= -45


def test_leaf_wetness_nocturnal_dynamics():
    """Verifica que o orvalho se concentra na madrugada/início da manhã."""
    payload = generate_iot_telemetry(num_days=1, random_seed=42)

    # Coleta horas de orvalho ativo (leaf_is_wet == True)
    wet_hours = [r["hour"] for r in payload.readings if r["leaf_is_wet"]]
    
    # As horas com molhamento devem estar concentradas no período 01:00 às 07:00
    for h in wet_hours:
        assert 1 <= h <= 8, f"Hora inesperada com orvalho ativo sem chuva: {h}"


def test_upload_iot_telemetry_local_backup(tmp_path: Path):
    """Valida gravação em disco local quando o Azure Blob Storage não está conectado."""
    payload = generate_iot_telemetry(device_id="NODE-BACKUP-TEST", num_days=1, random_seed=42)

    result = upload_iot_telemetry_to_azure(
        payload=payload,
        connection_string=None,
        local_backup_dir=tmp_path,
    )

    assert result["uploaded_to_cloud"] is False
    assert result["device_id"] == "NODE-BACKUP-TEST"
    assert result["total_readings"] == 24

    local_file = Path(result["local_path"])
    assert local_file.exists()

    # Valida formato JSON
    data = json.loads(local_file.read_text(encoding="utf-8"))
    assert data["device_id"] == "NODE-BACKUP-TEST"
    assert len(data["readings"]) == 24


def test_upload_iot_telemetry_azure_mock(tmp_path: Path):
    """Valida upload mockado para o contêiner bronze do Azure Blob Storage."""
    payload = generate_iot_telemetry(device_id="NODE-CLOUD-TEST", num_days=1, random_seed=42)

    mock_blob_service = MagicMock()
    mock_container_client = MagicMock()
    mock_blob_client = MagicMock()

    mock_blob_service.get_container_client.return_value = mock_container_client
    mock_container_client.exists.return_value = True
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string", return_value=mock_blob_service):
        result = upload_iot_telemetry_to_azure(
            payload=payload,
            connection_string="DefaultEndpointsProtocol=https;AccountName=mock;AccountKey=fake;EndpointSuffix=core.windows.net",
            container_name="omnicrop-data-lake-bronze",
            local_backup_dir=tmp_path,
        )

        assert result["uploaded_to_cloud"] is True
        assert "omnicrop-data-lake-bronze" in result["cloud_path"]
        mock_blob_client.upload_blob.assert_called_once()


def test_upload_iot_telemetry_azure_container_creation_and_exception(tmp_path: Path):
    """Valida criação de contêiner se não existir e fallback local em caso de erro na Azure."""
    from infra.simulate_iot_sensors import generate_iot_telemetry, upload_iot_telemetry_to_azure

    payload = generate_iot_telemetry(device_id="NODE-CREATE-CONTAINER", num_days=1, random_seed=42)

    # 1. Contêiner não existe -> cria contêiner
    mock_blob_service = MagicMock()
    mock_container_client = MagicMock()
    mock_container_client.exists.return_value = False
    mock_blob_client = MagicMock()

    mock_blob_service.get_container_client.return_value = mock_container_client
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    with patch("azure.storage.blob.BlobServiceClient.from_connection_string", return_value=mock_blob_service):
        res = upload_iot_telemetry_to_azure(
            payload=payload,
            connection_string="fake_conn_str",
            local_backup_dir=tmp_path,
        )
        assert res["uploaded_to_cloud"] is True
        mock_container_client.create_container.assert_called_once()

    # 2. Exceção de rede na Azure -> fallback para gravação local
    with patch("azure.storage.blob.BlobServiceClient.from_connection_string", side_effect=Exception("Azure timeout")):
        res_fail = upload_iot_telemetry_to_azure(
            payload=payload,
            connection_string="fake_conn_str",
            local_backup_dir=tmp_path,
        )
        assert res_fail["uploaded_to_cloud"] is False
        assert Path(res_fail["local_path"]).exists()


def test_simulate_iot_cli_main_and_run_as_main(tmp_path: Path):
    """Valida execução da função main() do simulador IoT via CLI e como __main__."""
    import runpy
    from infra.simulate_iot_sensors import main

    # 1. Execução da função main() com flag --no-upload
    cli_args = [
        "simulate_iot_sensors.py",
        "--device-id", "CLI-TEST-01",
        "--talhao-id", "talhao_02",
        "--crop-id", "soybean",
        "--days", "1",
        "--no-upload",
    ]
    with patch("sys.argv", cli_args), patch("infra.simulate_iot_sensors.PROJECT_ROOT", tmp_path):
        main()

    # 2. Execução como __main__ via runpy.run_path
    script_path = str(Path(__file__).resolve().parents[2] / "infra" / "simulate_iot_sensors.py")
    with patch("sys.argv", cli_args), patch("infra.simulate_iot_sensors.PROJECT_ROOT", tmp_path):
        runpy.run_path(script_path, run_name="__main__")
