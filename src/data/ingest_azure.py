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
GOLD_CONTAINER = "omnicrop-data-lake-gold"

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

def transform_to_gold(df_silver: pd.DataFrame) -> pd.DataFrame:
    """
    Camada Gold (Agregada / Decisão / Parquet):
    - Sumariza métricas meteorológicas e agronômicas em nível executivo.
    - Calcula indicadores de estresse hídrico, balanço hídrico acumulado e veranicos.
    - Gera recomendações operacionais automatizadas para a tomada de decisão (DSS).
    """
    precip_col = "precipitation_sum" if "precipitation_sum" in df_silver.columns else "precipitacao_total"
    et0_col = "et0_fao_evapotranspiration" if "et0_fao_evapotranspiration" in df_silver.columns else "evapotranspiracao_total"
    tmax_col = "temperature_2m_max" if "temperature_2m_max" in df_silver.columns else "t_max"
    tmin_col = "temperature_2m_min" if "temperature_2m_min" in df_silver.columns else "t_min"

    total_chuva = float(df_silver[precip_col].sum())
    total_et0 = float(df_silver[et0_col].sum())
    balanco_hidrico = round(total_chuva - total_et0, 2)
    dias_sem_chuva = int((df_silver[precip_col] < 1.0).sum())
    gda_total = round(float(df_silver["gdd"].sum()), 2)
    temp_max_media = round(float(df_silver[tmax_col].mean()), 2)
    temp_min_media = round(float(df_silver[tmin_col].mean()), 2)

    if "thermal_amplitude" in df_silver.columns:
        amplitude_media = round(float(df_silver["thermal_amplitude"].mean()), 2)
    else:
        amplitude_media = round(float((df_silver[tmax_col] - df_silver[tmin_col]).mean()), 2)

    # Classificação agronômica de estresse hídrico
    if balanco_hidrico < -25.0 or dias_sem_chuva >= 6:
        risco_estresse = "CRÍTICO"
        recomendacao = "Alerta de Estresse Hídrico: avaliar irrigação suplementar imediata."
    elif balanco_hidrico < -10.0 or dias_sem_chuva >= 4:
        risco_estresse = "MODERADO"
        recomendacao = "Atenção Operacional: monitorar umidade do solo e previsão climática."
    else:
        risco_estresse = "BAIXO"
        recomendacao = "Condições Hídricas Favoráveis para o desenvolvimento vegetativo."

    lat_val = float(df_silver["latitude"].iloc[0]) if "latitude" in df_silver.columns else LATITUDE
    lon_val = float(df_silver["longitude"].iloc[0]) if "longitude" in df_silver.columns else LONGITUDE

    resumo = {
        "periodo_inicio": str(df_silver["date"].min().date()),
        "periodo_fim": str(df_silver["date"].max().date()),
        "dias_monitorados": len(df_silver),
        "chuva_total_mm": round(total_chuva, 2),
        "et0_total_mm": round(total_et0, 2),
        "balanco_hidrico_mm": balanco_hidrico,
        "dias_sem_chuva": dias_sem_chuva,
        "gda_total_acumulado": gda_total,
        "temp_max_media_c": temp_max_media,
        "temp_min_media_c": temp_min_media,
        "amplitude_termica_media_c": amplitude_media,
        "risco_estresse_hidrico": risco_estresse,
        "recomendacao_manejo": recomendacao,
        "latitude": lat_val,
        "longitude": lon_val,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    return pd.DataFrame([resumo])

def load_latest_gold_kpis(azure_conn_str: str = None) -> pd.DataFrame | None:
    """Carrega os KPIs executivos mais recentes diretamente da Camada Gold do Azure Blob Storage."""
    conn_str = azure_conn_str or os.getenv("AZURE_CONNECTION_STRING")
    if not conn_str:
        return None
    try:
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service_client.get_container_client(GOLD_CONTAINER)
        blobs = list(container_client.list_blobs())
        if not blobs:
            return None
        latest_blob = max(blobs, key=lambda b: b.last_modified)
        blob_client = container_client.get_blob_client(latest_blob.name)
        data = blob_client.download_blob().readall()
        return pd.read_parquet(io.BytesIO(data))
    except Exception as e:
        print(f"Aviso: Não foi possível carregar da Gold na Azure: {e}")
        return None

def main():
    azure_conn_str = os.getenv("AZURE_CONNECTION_STRING")
    if not azure_conn_str:
        raise ValueError("ERRO: Variável de ambiente AZURE_CONNECTION_STRING não encontrada.")

    print("☁️ Iniciando pipeline Medallion no Azure Blob Storage (Bronze, Silver & Gold)...")
    
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
    
    parquet_buffer_silver = io.BytesIO()
    df_silver.to_parquet(parquet_buffer_silver, index=False, engine="pyarrow")
    parquet_buffer_silver.seek(0)

    silver_blob_name = f"weather/year={year}/month={month}/{execution_date}.parquet"
    silver_blob_client = blob_service_client.get_blob_client(container=SILVER_CONTAINER, blob=silver_blob_name)
    silver_blob_client.upload_blob(parquet_buffer_silver.getvalue(), overwrite=True)
    print(f"✅ SILVER salvo: {SILVER_CONTAINER}/{silver_blob_name}")

    # ── CAMADA GOLD (KPIs Executivos Agregados / BI) ────────────────
    print(f"🏆 Processando e gravando na Camada GOLD ({GOLD_CONTAINER})...")
    gold_container_client = blob_service_client.get_container_client(GOLD_CONTAINER)
    if not gold_container_client.exists():
        print(f"📦 Contêiner '{GOLD_CONTAINER}' não existe. Criando agora...")
        gold_container_client.create_container()

    df_gold = transform_to_gold(df_silver)
    
    parquet_buffer_gold = io.BytesIO()
    df_gold.to_parquet(parquet_buffer_gold, index=False, engine="pyarrow")
    parquet_buffer_gold.seek(0)

    gold_blob_name = f"kpis/year={year}/month={month}/resumo_{execution_date}.parquet"
    gold_blob_client = blob_service_client.get_blob_client(container=GOLD_CONTAINER, blob=gold_blob_name)
    gold_blob_client.upload_blob(parquet_buffer_gold.getvalue(), overwrite=True)
    print(f"✅ GOLD salvo: {GOLD_CONTAINER}/{gold_blob_name}")

if __name__ == "__main__":
    main()
