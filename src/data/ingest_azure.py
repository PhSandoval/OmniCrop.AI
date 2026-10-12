import os
import io
import json
import requests
import pandas as pd
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
from tenacity import retry, stop_after_attempt, wait_exponential
from src.data.schemas import OpenMeteoResponse

# Configurações da Fazenda Boa Vista (Ribeirão Preto)
LATITUDE = -21.1704
LONGITUDE = -47.8103
BRONZE_CONTAINER = "omnicrop-data-lake-bronze"
SILVER_CONTAINER = "omnicrop-data-lake-silver"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_weather_data() -> dict:
    print("📥 Baixando dados climáticos...")
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration"
        f"&timezone=America/Sao_Paulo&past_days=7"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

def transform_to_silver(raw_data: dict) -> pd.DataFrame:
    """
    Camada Silver (Refinada / Parquet):
    - Converte o payload JSON para DataFrame estruturado.
    - Limpa dados e padroniza tipos.
    - Calcula features agronômicas enriquecidas (Graus-Dia / GDA e balanço hídrico).
    """
    daily = raw_data.get("daily", {})
    df = pd.DataFrame(daily)

    # Padronização temporal
    df["date"] = pd.to_datetime(df["time"])
    df = df.drop(columns=["time"], errors="ignore")

    # Feature Engineering Agronômico
    df["t_mean"] = (df["temperature_2m_max"] + df["temperature_2m_min"]) / 2.0
    df["thermal_amplitude"] = df["temperature_2m_max"] - df["temperature_2m_min"]

    # Graus-Dia Acumulados (base 18°C para cana)
    df["gdd"] = (df["t_mean"] - 18.0).clip(lower=0.0)
    df["gda_acumulado"] = df["gdd"].cumsum()

    # Acúmulo de precipitação na janela
    df["chuva_acumulada_7d"] = df["precipitation_sum"].rolling(7, min_periods=1).sum()

    # Metadados de Linhagem e Rastreabilidade (Data Lineage)
    df["latitude"] = raw_data.get("latitude", LATITUDE)
    df["longitude"] = raw_data.get("longitude", LONGITUDE)
    df["processed_at"] = datetime.now(timezone.utc).isoformat()

    return df

def main():
    # A Connection String é injetada com segurança pelo GitHub Secrets
    azure_conn_str = os.getenv("AZURE_CONNECTION_STRING")
    if not azure_conn_str:
        raise ValueError("ERRO: Variável de ambiente AZURE_CONNECTION_STRING não encontrada.")

    print("☁️ Iniciando pipeline Medallion no Azure Blob Storage (Bronze & Silver)...")
    
    # 1. Extração (API Open-Meteo) com retentativas automáticas
    data = fetch_weather_data()
    
    # 2. Validação de Contrato (Data Quality Assurance)
    print("🔍 Validando qualidade dos dados (Data Contract)...")
    try:
        _ = OpenMeteoResponse(**data)
        print("✅ Dados passaram na validação do Pydantic!")
    except Exception as e:
        print(f"🚨 ERRO DE CONTRATO: O JSON recebido não possui a estrutura esperada.\n{e}")
        raise

    execution_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    year, month, _ = execution_date.split('-')

    # Metadados de auditoria no JSON cru
    data['_metadata'] = {
        'ingestion_timestamp': datetime.now(timezone.utc).isoformat(),
        'source': 'open-meteo',
        'pipeline': 'github-actions-azure'
    }

    # 3. Conexão com o Azure Blob Storage
    print("🔗 Conectando à conta da Azure...")
    blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)

    # ── CAMADA BRONZE (JSON Cru Particionado) ───────────────────────
    print(f"📦 Gravando na Camada BRONZE ({BRONZE_CONTAINER})...")
    bronze_container_client = blob_service_client.get_container_client(BRONZE_CONTAINER)
    if not bronze_container_client.exists():
        print(f"📦 Contêiner '{BRONZE_CONTAINER}' não existe. Criando agora...")
        bronze_container_client.create_container()

    bronze_blob_name = f"weather/year={year}/month={month}/{execution_date}.json"
    bronze_blob_client = blob_service_client.get_blob_client(container=BRONZE_CONTAINER, blob=bronze_blob_name)
    bronze_blob_client.upload_blob(json.dumps(data, indent=2), overwrite=True)
    print(f"✅ BRONZE salvo: {BRONZE_CONTAINER}/{bronze_blob_name}")

    # ── CAMADA SILVER (Parquet Enriquecido e Compactado) ────────────
    print(f"⚙️ Processando e gravando na Camada SILVER ({SILVER_CONTAINER})...")
    silver_container_client = blob_service_client.get_container_client(SILVER_CONTAINER)
    if not silver_container_client.exists():
        print(f"📦 Contêiner '{SILVER_CONTAINER}' não existe. Criando agora...")
        silver_container_client.create_container()

    df_silver = transform_to_silver(data)
    
    # Serialização colunar Parquet em buffer de memória
    parquet_buffer = io.BytesIO()
    df_silver.to_parquet(parquet_buffer, index=False, engine="pyarrow")
    parquet_buffer.seek(0)

    silver_blob_name = f"weather/year={year}/month={month}/{execution_date}.parquet"
    silver_blob_client = blob_service_client.get_blob_client(container=SILVER_CONTAINER, blob=silver_blob_name)
    silver_blob_client.upload_blob(parquet_buffer.getvalue(), overwrite=True)
    print(f"✅ SILVER salvo: {SILVER_CONTAINER}/{silver_blob_name}")

if __name__ == "__main__":
    main()
