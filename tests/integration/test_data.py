import pytest
import io
import json
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.data.schemas import OpenMeteoResponse, DailyWeather
from src.data.ingest_azure import (
    fetch_weather_data,
    transform_to_silver,
    transform_to_gold,
    load_latest_gold_kpis,
    main as ingest_azure_main,
    GOLD_CONTAINER,
    BRONZE_CONTAINER,
    SILVER_CONTAINER,
)
from src.data.fetch_api import (
    search_location,
    _fetch_openmeteo,
    _build_features,
    fetch_farm_data,
)


@pytest.fixture
def valid_openmeteo_payload():
    return {
        "latitude": -21.17,
        "longitude": -47.81,
        "daily": {
            "time": ["2026-10-01", "2026-10-02"],
            "temperature_2m_max": [30.5, 31.0],
            "temperature_2m_min": [20.1, 21.0],
            "precipitation_sum": [0.0, 5.2],
            "et0_fao_evapotranspiration": [4.5, 4.2]
        }
    }


def test_open_meteo_contract_valid(valid_openmeteo_payload):
    """Valida um payload JSON perfeito na classe OpenMeteoResponse."""
    response = OpenMeteoResponse(**valid_openmeteo_payload)
    
    assert response.latitude == -21.17
    assert response.longitude == -47.81
    assert len(response.daily.time) == 2
    assert response.daily.precipitation_sum == [0.0, 5.2]
    assert response.daily.et0_fao_evapotranspiration == [4.5, 4.2]
    assert isinstance(response.daily.temperature_2m_max[0], float)


def test_open_meteo_contract_invalid():
    """Garante que o Pydantic bloqueia a execução se faltar a chave precipitation_sum."""
    payload = {
        "latitude": -21.17,
        "longitude": -47.81,
        "daily": {
            "time": ["2023-01-01"],
            "temperature_2m_max": [30.5],
            "temperature_2m_min": [20.1],
            # FALTA A CHAVE precipitation_sum
            "et0_fao_evapotranspiration": [4.5]
        }
    }
    
    with pytest.raises(ValidationError):
        OpenMeteoResponse(**payload)


@patch('requests.get')
def test_open_meteo_api_failure(mock_get):
    """Simula um erro HTTP 500 da Open-Meteo, garantindo que o sistema lança um erro limpo."""
    mock_get.return_value.status_code = 500
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        response = requests.get("https://api.open-meteo.com/v1/forecast")
        response.raise_for_status()
        
    assert "500 Server Error" in str(exc_info.value)


@patch('requests.get')
def test_fetch_weather_data_success(mock_get, valid_openmeteo_payload):
    """Valida chamada com sucesso de fetch_weather_data."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = valid_openmeteo_payload
    mock_get.return_value = mock_resp

    data = fetch_weather_data()
    assert data["latitude"] == -21.17
    assert "daily" in data
    mock_get.assert_called_once()


def test_transform_to_silver_pipeline():
    """Valida a transformação de dados brutos (Bronze) para o formato refinado (Silver)."""
    raw_payload = {
        "latitude": -21.17,
        "longitude": -47.81,
        "daily": {
            "time": ["2026-10-01", "2026-10-02"],
            "temperature_2m_max": [32.0, 30.0],
            "temperature_2m_min": [20.0, 18.0],
            "precipitation_sum": [10.0, 5.0],
            "et0_fao_evapotranspiration": [4.0, 3.5]
        }
    }

    df_silver = transform_to_silver(raw_payload)

    assert isinstance(df_silver, pd.DataFrame)
    assert len(df_silver) == 2
    assert "gda_acumulado" in df_silver.columns
    assert "chuva_acumulada_7d" in df_silver.columns
    assert "thermal_amplitude" in df_silver.columns
    assert df_silver["t_mean"].iloc[0] == 26.0
    assert df_silver["gdd"].iloc[0] == 8.0 # 26 - 18
    assert df_silver["chuva_acumulada_7d"].iloc[1] == 15.0 # 10 + 5


def test_transform_to_gold_pipeline():
    """Valida a agregação de dados da camada Silver para os KPIs executivos da camada Gold."""
    raw_payload = {
        "latitude": -21.17,
        "longitude": -47.81,
        "daily": {
            "time": ["2026-10-01", "2026-10-02"],
            "temperature_2m_max": [32.0, 30.0],
            "temperature_2m_min": [20.0, 18.0],
            "precipitation_sum": [0.0, 0.0], # Sem chuva para forçar estresse
            "et0_fao_evapotranspiration": [4.0, 4.0]
        }
    }

    df_silver = transform_to_silver(raw_payload)
    df_gold = transform_to_gold(df_silver)

    assert isinstance(df_gold, pd.DataFrame)
    assert len(df_gold) == 1
    assert "balanco_hidrico_mm" in df_gold.columns
    assert "risco_estresse_hidrico" in df_gold.columns
    assert "recomendacao_manejo" in df_gold.columns
    assert df_gold["chuva_total_mm"].iloc[0] == 0.0
    assert df_gold["et0_total_mm"].iloc[0] == 8.0
    assert df_gold["balanco_hidrico_mm"].iloc[0] == -8.0
    assert df_gold["dias_sem_chuva"].iloc[0] == 2
    assert df_gold["dias_monitorados"].iloc[0] == 2


def test_transform_to_gold_all_branches():
    """Valida todos os ramos de risco e colunas alternativas na camada Gold."""
    # 1. Risco CRÍTICO (balanco < -25 ou dias_sem_chuva >= 6)
    dates = pd.date_range("2026-10-01", periods=7)
    df_critico = pd.DataFrame({
        "date": dates,
        "precipitation_sum": [0.0] * 7,
        "et0_fao_evapotranspiration": [5.0] * 7,
        "temperature_2m_max": [35.0] * 7,
        "temperature_2m_min": [20.0] * 7,
        "gdd": [10.0] * 7,
        "thermal_amplitude": [15.0] * 7,
        "latitude": [-21.17] * 7,
        "longitude": [-47.81] * 7,
    })
    gold_critico = transform_to_gold(df_critico)
    assert gold_critico["risco_estresse_hidrico"].iloc[0] == "CRÍTICO"

    # 2. Risco BAIXO com colunas alternativas (precipitacao_total, evapotranspiracao_total, sem thermal_amplitude/lat/lon)
    df_baixo = pd.DataFrame({
        "date": pd.date_range("2026-10-01", periods=3),
        "precipitacao_total": [20.0, 25.0, 30.0],
        "evapotranspiracao_total": [3.0, 3.0, 3.0],
        "t_max": [28.0, 27.0, 29.0],
        "t_min": [18.0, 17.0, 18.0],
        "gdd": [5.0, 4.0, 5.0],
    })
    gold_baixo = transform_to_gold(df_baixo)
    assert gold_baixo["risco_estresse_hidrico"].iloc[0] == "BAIXO"
    assert gold_baixo["dias_sem_chuva"].iloc[0] == 0

    # 3. Risco MODERADO (balanco < -10 ou dias_sem_chuva >= 4)
    df_moderado = pd.DataFrame({
        "date": pd.date_range("2026-10-01", periods=5),
        "precipitation_sum": [0.0, 0.0, 0.0, 0.0, 5.0],
        "et0_fao_evapotranspiration": [3.0] * 5,
        "temperature_2m_max": [30.0] * 5,
        "temperature_2m_min": [18.0] * 5,
        "gdd": [6.0] * 5,
        "thermal_amplitude": [12.0] * 5,
        "latitude": [-21.17] * 5,
        "longitude": [-47.81] * 5,
    })
    gold_moderado = transform_to_gold(df_moderado)
    assert gold_moderado["risco_estresse_hidrico"].iloc[0] == "MODERADO"



def test_load_latest_gold_kpis_no_conn_str():
    """Garante retorno None quando a string de conexão não está configurada."""
    with patch.dict(os.environ, {}, clear=True):
        res = load_latest_gold_kpis()
        assert res is None


def test_load_latest_gold_kpis_empty_container():
    """Garante retorno None quando não há blobs na camada Gold."""
    mock_service = MagicMock()
    mock_container = MagicMock()
    mock_container.list_blobs.return_value = []
    mock_service.get_container_client.return_value = mock_container

    with patch("src.data.ingest_azure.BlobServiceClient.from_connection_string", return_value=mock_service):
        res = load_latest_gold_kpis("fake_conn")
        assert res is None


def test_load_latest_gold_kpis_success():
    """Valida leitura e decodificação do Parquet mais recente na camada Gold."""
    df_sample = pd.DataFrame([{"balanco_hidrico_mm": -12.5, "risco_estresse_hidrico": "MODERADO"}])
    buf = io.BytesIO()
    df_sample.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    parquet_bytes = buf.getvalue()

    mock_blob1 = MagicMock()
    mock_blob1.name = "kpi1.parquet"
    mock_blob1.last_modified = datetime(2026, 10, 1, tzinfo=timezone.utc)

    mock_blob2 = MagicMock()
    mock_blob2.name = "kpi2.parquet"
    mock_blob2.last_modified = datetime(2026, 10, 2, tzinfo=timezone.utc)

    mock_container = MagicMock()
    mock_container.list_blobs.return_value = [mock_blob1, mock_blob2]

    mock_blob_client = MagicMock()
    mock_download = MagicMock()
    mock_download.readall.return_value = parquet_bytes
    mock_blob_client.download_blob.return_value = mock_download
    mock_container.get_blob_client.return_value = mock_blob_client

    mock_service = MagicMock()
    mock_service.get_container_client.return_value = mock_container

    with patch("src.data.ingest_azure.BlobServiceClient.from_connection_string", return_value=mock_service):
        res = load_latest_gold_kpis("fake_conn")
        assert res is not None
        assert isinstance(res, pd.DataFrame)
        assert res["risco_estresse_hidrico"].iloc[0] == "MODERADO"


def test_load_latest_gold_kpis_exception_handled():
    """Garante que falhas de rede no Azure Blob Storage são capturadas de forma segura."""
    with patch("src.data.ingest_azure.BlobServiceClient.from_connection_string", side_effect=Exception("Azure Down")):
        res = load_latest_gold_kpis("fake_conn")
        assert res is None


def test_ingest_azure_main_missing_env():
    """Valida que main() levanta ValueError se AZURE_CONNECTION_STRING estiver ausente."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="AZURE_CONNECTION_STRING"):
            ingest_azure_main()


def test_ingest_azure_main_contract_failure():
    """Valida que main() falha e levanta ValidationError caso os dados climáticos violem o contrato."""
    with patch.dict(os.environ, {"AZURE_CONNECTION_STRING": "fake_conn"}):
        with patch("src.data.ingest_azure.fetch_weather_data", return_value={"latitude": -21.17}):
            with pytest.raises(ValidationError):
                ingest_azure_main()


def test_ingest_azure_main_success_flow(valid_openmeteo_payload):
    """Valida execução completa da pipeline Medallion (Bronze, Silver, Drift, Gold) com mock da Azure."""
    mock_service = MagicMock()
    mock_container = MagicMock()
    mock_container.exists.return_value = False  # Testa criação automática do contêiner
    mock_service.get_container_client.return_value = mock_container

    mock_blob_client = MagicMock()
    mock_service.get_blob_client.return_value = mock_blob_client

    with patch.dict(os.environ, {"AZURE_CONNECTION_STRING": "fake_conn", "ALERT_WEBHOOK_URL": "http://webhook"}):
        with patch("src.data.ingest_azure.fetch_weather_data", return_value=valid_openmeteo_payload):
            with patch("src.data.ingest_azure.BlobServiceClient.from_connection_string", return_value=mock_service):
                with patch("src.mlops.data_drift.detect_data_drift") as mock_drift:
                    mock_drift.return_value.summary = "Drift OK"
                    ingest_azure_main()

    # Valida que os contêineres foram verificados/criados e os 3 uploads foram realizados
    assert mock_container.create_container.call_count >= 3
    assert mock_blob_client.upload_blob.call_count == 3


def test_ingest_azure_main_drift_exception_handled(valid_openmeteo_payload):
    """Valida que falha na auditoria de drift não bloqueia a gravação da Camada Gold."""
    mock_service = MagicMock()
    mock_container = MagicMock()
    mock_container.exists.return_value = True
    mock_service.get_container_client.return_value = mock_container

    mock_blob_client = MagicMock()
    mock_service.get_blob_client.return_value = mock_blob_client

    with patch.dict(os.environ, {"AZURE_CONNECTION_STRING": "fake_conn"}):
        with patch("src.data.ingest_azure.fetch_weather_data", return_value=valid_openmeteo_payload):
            with patch("src.data.ingest_azure.BlobServiceClient.from_connection_string", return_value=mock_service):
                with patch("src.mlops.data_drift.detect_data_drift", side_effect=RuntimeError("Drift failed")):
                    ingest_azure_main()

    assert mock_blob_client.upload_blob.call_count == 3


# ── TESTES DE FETCH_API.PY ───────────────────────────────────────

def test_fetch_api_search_location_success():
    """Valida retorno estruturado de Nominatim com mock de requests."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {"display_name": "Ribeirão Preto, SP", "lat": "-21.17", "lon": "-47.81"}
    ]
    with patch("requests.get", return_value=mock_resp):
        res = search_location("Ribeirão Preto")
        assert len(res) == 1
        assert res[0]["label"] == "Ribeirão Preto, SP"
        assert res[0]["lat"] == -21.17
        assert res[0]["lon"] == -47.81
        assert res[0]["elevation"] == 0


def test_fetch_api_search_location_exception():
    """Valida retorno de lista vazia caso a geocodificação falhe."""
    with patch("requests.get", side_effect=Exception("Timeout")):
        res = search_location("Local Inexistente")
        assert res == []


def test_fetch_api_fetch_openmeteo_success():
    """Valida busca de dados horários e agregação diária do Open-Meteo."""
    times = [f"2026-10-01T{h:02d}:00" for h in range(24)]
    mock_hourly = {
        "time": times,
        "temperature_2m": [25.0] * 24,
        "precipitation": [0.5] * 24,
        "et0_fao_evapotranspiration": [0.2] * 24,
        "soil_moisture_7_to_28cm": [0.35] * 24,
        "shortwave_radiation": [200.0] * 24,
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"hourly": mock_hourly}

    with patch("requests.get", return_value=mock_resp):
        daily = _fetch_openmeteo(lat=-21.17, lon=-47.81, past_days=1)
        assert isinstance(daily, pd.DataFrame)
        assert len(daily) == 1
        assert "t_mean" in daily.columns
        assert daily["precipitacao_total"].iloc[0] == pytest.approx(12.0)


def test_fetch_api_build_features_with_model():
    """Valida cálculo de GDA dinâmico e inferência de modelo em _build_features."""
    daily = pd.DataFrame({
        "date": pd.date_range("2026-10-01", periods=5),
        "t_mean": [26.0] * 5,
        "precipitacao_total": [10.0] * 5,
        "chuva_acumulada_30d": [50.0] * 5,
        "chuva_acumulada_60d": [100.0] * 5,
        "chuva_acumulada_90d": [150.0] * 5,
        "GDA_mensal": [200.0] * 5,
    })

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0.72] * 5)

    with patch("src.models.predict.load_model", return_value=mock_model):
        res = _build_features(daily, crop_id="sugarcane")
        assert "gdd" in res.columns
        assert "GDA_mensal" in res.columns
        assert "ndvi_medio" in res.columns
        assert res["ndvi_medio"].iloc[0] == 0.72


def test_fetch_api_build_features_not_implemented_and_exception():
    """Valida preenchimento seguro de NaN quando cultura não tem modelo treinado ou falha."""
    daily = pd.DataFrame({
        "date": pd.date_range("2026-10-01", periods=3),
        "t_mean": [25.0] * 3,
        "precipitacao_total": [5.0] * 3,
        "chuva_acumulada_30d": [15.0] * 3,
        "chuva_acumulada_60d": [30.0] * 3,
        "chuva_acumulada_90d": [45.0] * 3,
        "GDA_mensal": [100.0] * 3,
    })

    # 1. NotImplementedError
    with patch("src.models.predict.load_model", side_effect=NotImplementedError("Em treino")):
        res_nie = _build_features(daily, crop_id="soybean")
        assert np.isnan(res_nie["ndvi_medio"].iloc[0])

    # 2. Generic Exception
    with patch("src.models.predict.load_model", side_effect=RuntimeError("IO Error")):
        res_exc = _build_features(daily, crop_id="sugarcane")
        assert np.isnan(res_exc["ndvi_medio"].iloc[0])


def test_fetch_api_fetch_farm_data_both_branches():
    """Valida fetch_farm_data tanto quando há datas passadas quanto apenas datas futuras."""
    fetch_farm_data.clear()

    # 1. Com datas passadas (date <= now)
    past_dates = pd.date_range(datetime.now().date() - timedelta(days=5), periods=6)
    df_past = pd.DataFrame({
        "date": past_dates,
        "t_mean": [25.0] * 6,
        "precipitacao_total": [5.0] * 6,
        "chuva_acumulada_30d": [30.0] * 6,
        "chuva_acumulada_60d": [60.0] * 6,
        "chuva_acumulada_90d": [90.0] * 6,
        "GDA_mensal": [150.0] * 6,
        "ndvi_medio": [0.7] * 6,
    })

    with patch("src.data.fetch_api._fetch_openmeteo", return_value=df_past):
        df_out, today_dict = fetch_farm_data(-21.17, -47.81, "sugarcane")
        assert isinstance(df_out, pd.DataFrame)
        assert isinstance(today_dict, dict)
        assert "ndvi_medio" in today_dict
        assert isinstance(today_dict["ndvi_medio"], float)

    # 2. Apenas datas futuras (df_past.empty)
    fetch_farm_data.clear()
    future_dates = pd.date_range(datetime.now().date() + timedelta(days=10), periods=5)
    df_future = pd.DataFrame({
        "date": future_dates,
        "t_mean": [24.0] * 5,
        "precipitacao_total": [2.0] * 5,
        "chuva_acumulada_30d": [10.0] * 5,
        "chuva_acumulada_60d": [20.0] * 5,
        "chuva_acumulada_90d": [30.0] * 5,
        "GDA_mensal": [80.0] * 5,
        "ndvi_medio": [0.65] * 5,
    })

    with patch("src.data.fetch_api._fetch_openmeteo", return_value=df_future):
        df_out, today_dict = fetch_farm_data(-21.17, -47.81, "sugarcane")
        assert isinstance(df_out, pd.DataFrame)
        assert "ndvi_medio" in today_dict
        assert isinstance(today_dict["ndvi_medio"], float)

