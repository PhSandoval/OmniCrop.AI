"""
Busca dados reais da Open-Meteo API para qualquer lat/lon
e aplica o mesmo feature engineering do src/features.py.
"""
import requests
import pandas as pd
import numpy as np
import streamlit as st
from datetime import date, timedelta


OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

HOURLY_VARS = [
    "temperature_2m",
    "precipitation",
    "et0_fao_evapotranspiration",
    "soil_moisture_7_to_28cm",
    "shortwave_radiation",
]


# ── Geocodificação ──────────────────────────────────────────────
def search_location(query: str) -> list[dict]:
    """Retorna lista de locais (nome, lat, lon) para a busca via OpenStreetMap Nominatim (suporta Endereço e CEP)."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 8, "addressdetails": 1},
            headers={"User-Agent": "OmniCropAI/1.0"},
            timeout=8,
        )
        results = r.json()
        return [
            {
                "label": r.get("display_name", ""),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
                "elevation": 0, # Nominatim doesn't provide elevation, but it's not strictly needed for the UI dropdown
            }
            for r in results
        ]
    except Exception:
        return []


# ── Open-Meteo fetch ────────────────────────────────────────────
def _fetch_openmeteo(lat: float, lon: float, past_days: int = 92) -> pd.DataFrame:
    """Baixa dados horários da Open-Meteo e retorna DataFrame diário agregado."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "past_days": past_days,
        "forecast_days": 16,
        "timezone": "America/Sao_Paulo",
    }
    r = requests.get(OPENMETEO_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    hourly = data["hourly"]
    df_h = pd.DataFrame({
        "timestamp":        pd.to_datetime(hourly["time"]),
        "temperatura_2m":   hourly["temperature_2m"],
        "precipitacao_mm":  hourly["precipitation"],
        "evapotranspiracao_mm": hourly["et0_fao_evapotranspiration"],
        "umidade_solo":     hourly["soil_moisture_7_to_28cm"],
        "radiacao_solar":   hourly["shortwave_radiation"],
    })

    df_h["date"] = df_h["timestamp"].dt.date

    daily = df_h.groupby("date").agg(
        t_mean=("temperatura_2m", "mean"),
        t_max=("temperatura_2m", "max"),
        t_min=("temperatura_2m", "min"),
        precipitacao_total=("precipitacao_mm", "sum"),
        evapotranspiracao_total=("evapotranspiracao_mm", "sum"),
        umidade_solo_mean=("umidade_solo", "mean"),
        radiacao_solar_mean=("radiacao_solar", "mean"),
    ).reset_index()

    daily["date"] = pd.to_datetime(daily["date"])
    return daily.sort_values("date").reset_index(drop=True)


# ── Feature engineering (replica src/features.py) ──────────────
def _build_features(daily: pd.DataFrame) -> pd.DataFrame:
    df = daily.copy()

    # GDA Mensal (base 18°C para cana)
    df["gdd"] = (df["t_mean"] - 18.0).clip(lower=0)
    df["GDA_mensal"] = df["gdd"].rolling(30, min_periods=1).sum()

    # Chuva acumulada
    df["chuva_acumulada_30d"]  = df["precipitacao_total"].rolling(30, min_periods=1).sum()
    df["chuva_acumulada_60d"]  = df["precipitacao_total"].rolling(60, min_periods=1).sum()
    df["chuva_acumulada_90d"]  = df["precipitacao_total"].rolling(90, min_periods=1).sum()

    # Aplicar Gradient Boosting no Histórico e na Previsão Futura!
    try:
        from src.models.predict import load_model, FEATURE_KEYS
        model = load_model()
        df["ndvi_medio"] = model.predict(df[FEATURE_KEYS].bfill().ffill())
    except Exception as e:
        df["ndvi_medio"] = np.nan

    return df.bfill().ffill()


# ── Ponto de entrada principal ──────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_farm_data(lat: float, lon: float) -> tuple[pd.DataFrame, dict]:
    """
    Busca dados reais da fazenda via Open-Meteo.
    Retorna (DataFrame completo, dict com dados de hoje).
    Resultado cacheado por 1 hora.
    """
    daily = _fetch_openmeteo(lat, lon, past_days=92)
    df    = _build_features(daily)
    # Garante que 'today' é a data atual (hoje) para o dashboard, ignorando a previsão futura
    now = pd.Timestamp.now(tz="America/Sao_Paulo").normalize().tz_localize(None)
    df_past = df[df["date"] <= now]
    if not df_past.empty:
        today = df_past.iloc[-1].to_dict()
    else:
        today = df.iloc[0].to_dict()
    return df, today
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd



def _five_years_ago(reference_date):
    try:
        return reference_date.replace(year=reference_date.year - 5)
    except ValueError:
        return reference_date.replace(month=2, day=28, year=reference_date.year - 5)


def build_dataset_historico(lat: float, lon: float, nome_talhao: str):
    """Camada fria: monta dataset historico para EDA e treino de modelo."""
    print(f"\n=== Coletando dados para {nome_talhao} ===")

    today = datetime.now().date()
    end_date = today - timedelta(days=1)
    start_date = _five_years_ago(end_date)

    meteo_data = fetch_openmeteo_agro_data(
        lat,
        lon,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )
    ndvi_historico = extrair_ndvi_historico(
        lat,
        lon,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
    )

    meteo_hourly = meteo_data.get("hourly", {}) if isinstance(meteo_data, dict) else {}
    ndvi_por_periodo = {
        item["periodo"]: item
        for item in ndvi_historico
        if isinstance(item, dict)
    }
    ndvi_meses_com_valor = sum(1 for item in ndvi_historico if item.get("ndvi_medio") is not None)

    horarios = meteo_hourly.get("time", []) if isinstance(meteo_hourly, dict) else []
    total_registros = len(horarios)

    registros = []
    for indice, horario in enumerate(horarios):
        periodo = horario[:7]
        ndvi_mes = ndvi_por_periodo.get(periodo, {"data_referencia": None, "ndvi_medio": None, "quantidade_imagens": 0})
        registros.append(
            {
                "talhao": nome_talhao,
                "lat": lat,
                "lon": lon,
                "timestamp": horario,
                "openmeteo": {
                    "timezone": meteo_data.get("timezone"),
                    "elevation": meteo_data.get("elevation"),
                    "temperatura_2m": meteo_hourly.get("temperature_2m", [None])[indice],
                    "umidade_relativa_2m": meteo_hourly.get("relative_humidity_2m", [None])[indice],
                    "precipitacao_mm": meteo_hourly.get("precipitation", [None])[indice],
                    "evapotranspiracao_mm": meteo_hourly.get("et0_fao_evapotranspiration", [None])[indice],
                    "temperatura_solo_18cm_c": meteo_hourly.get("soil_temperature_7_to_28cm", [None])[indice],
                    "umidade_solo_9_27cm": meteo_hourly.get("soil_moisture_7_to_28cm", [None])[indice],
                    "radiacao_solar_wm2": meteo_hourly.get("shortwave_radiation", [None])[indice],
                    "vento_velocidade_ms": meteo_hourly.get("wind_speed_10m", [None])[indice],
                    "vento_rajada_ms": meteo_hourly.get("wind_gusts_10m", [None])[indice],
                },
                "ndvi_historico": {
                    "periodo": ndvi_mes.get("periodo"),
                    "data_referencia": ndvi_mes.get("data_referencia"),
                    "ndvi_medio": ndvi_mes.get("ndvi_medio"),
                    "quantidade_imagens": ndvi_mes.get("quantidade_imagens", 0),
                },
            }
        )

    dataset = {
        "talhao": nome_talhao,
        "lat": lat,
        "lon": lon,
        "data_hora_coleta": datetime.now().isoformat(timespec="seconds"),
        "janela_meteo": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_horarios": total_registros,
        },
        "ndvi_historico_resumo": {
            "periodos_encontrados": len(ndvi_historico),
            "periodos_com_ndvi": ndvi_meses_com_valor,
        },
        "registros": registros,
    }

    return dataset


def salvar_dataset_historico(dataset: dict, nome_talhao: str):
    """Salva o dataset historico em CSV dentro de data/Raw."""
    project_root = Path(__file__).resolve().parents[2]
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)


    filename = "Dataset_SugarCane_historico.csv"
    path = raw_dir / filename

    registros_flat = []
    for registro in dataset["registros"]:
        registros_flat.append(
            {
                "talhao": registro["talhao"],
                "lat": registro["lat"],
                "lon": registro["lon"],
                "timestamp": registro["timestamp"],
                "timezone": registro["openmeteo"]["timezone"],
                "elevation": registro["openmeteo"]["elevation"],
                "temperatura_2m": registro["openmeteo"]["temperatura_2m"],
                "umidade_relativa_2m": registro["openmeteo"]["umidade_relativa_2m"],
                "precipitacao_mm": registro["openmeteo"]["precipitacao_mm"],
                "evapotranspiracao_mm": registro["openmeteo"]["evapotranspiracao_mm"],
                "temperatura_solo_18cm_c": registro["openmeteo"]["temperatura_solo_18cm_c"],
                "umidade_solo_9_27cm": registro["openmeteo"]["umidade_solo_9_27cm"],
                "radiacao_solar_wm2": registro["openmeteo"]["radiacao_solar_wm2"],
                "vento_velocidade_ms": registro["openmeteo"]["vento_velocidade_ms"],
                "vento_rajada_ms": registro["openmeteo"]["vento_rajada_ms"],
                "ndvi_periodo": registro["ndvi_historico"]["periodo"],
                "ndvi_data_referencia": registro["ndvi_historico"]["data_referencia"],
                "ndvi_medio": registro["ndvi_historico"]["ndvi_medio"],
                "ndvi_quantidade_imagens": registro["ndvi_historico"]["quantidade_imagens"],
            }
        )

    pd.DataFrame(registros_flat).to_csv(path, index=False, encoding="utf-8")

    print(f"\n✅ Dataset salvo em: {path}")
    return path


if __name__ == "__main__":
    dataset = build_dataset_historico(
        lat=-21.1775,
        lon=-47.8103,
        nome_talhao="RP_Talhao_Central",
    )
    print(f"Total de registros gerados: {len(dataset['registros'])}")
    print(f"Intervalo: {dataset['janela_meteo']['start_date']} até {dataset['janela_meteo']['end_date']}")
    print(f"NDVI com valor em {dataset['ndvi_historico_resumo']['periodos_com_ndvi']} de {dataset['ndvi_historico_resumo']['periodos_encontrados']} periodos")
    salvar_dataset_historico(dataset, "RP_Talhao_Central")
