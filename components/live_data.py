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
    """Retorna lista de locais (nome, lat, lon, country) para a busca."""
    try:
        r = requests.get(
            GEOCODING_URL,
            params={"name": query, "count": 8, "language": "pt", "format": "json"},
            timeout=5,
        )
        results = r.json().get("results", [])
        return [
            {
                "label": f"{r.get('name')}, {r.get('admin1', '')}, {r.get('country', '')}",
                "lat": r["latitude"],
                "lon": r["longitude"],
                "elevation": r.get("elevation", 0),
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
        "forecast_days": 1,
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

    # GDD (base 18°C para cana)
    df["gdd"] = (df["t_mean"] - 18.0).clip(lower=0)
    df["gdd_acumulado_30d"] = df["gdd"].rolling(30, min_periods=1).sum()
    df["gdd_acumulado_90d"] = df["gdd"].rolling(90, min_periods=1).sum()

    # Balanço hídrico
    df["chuva_acumulada_30d"]  = df["precipitacao_total"].rolling(30, min_periods=1).sum()
    df["evapo_acumulada_30d"]  = df["evapotranspiracao_total"].rolling(30, min_periods=1).sum()
    df["balanco_hidrico_30d"]  = df["chuva_acumulada_30d"] - df["evapo_acumulada_30d"]

    # Lags
    df["balanco_hidrico_lag_30d"]  = df["balanco_hidrico_30d"].shift(30)
    df["balanco_hidrico_lag_60d"]  = df["balanco_hidrico_30d"].shift(60)
    df["chuva_acumulada_lag_30d"]  = df["chuva_acumulada_30d"].shift(30)

    # Radiação acumulada
    df["radiacao_acumulada_30d"] = df["radiacao_solar_mean"].rolling(30, min_periods=1).sum()

    # Estresse térmico
    df["dias_calor_extremo_30d"] = (df["t_max"] > 35).rolling(30, min_periods=1).sum()
    df["dias_frio_extremo_30d"]  = (df["t_min"] < 10).rolling(30, min_periods=1).sum()

    # Eventos de chuva extrema
    df["eventos_chuva_extrema_30d"] = (df["precipitacao_total"] > 50).rolling(30, min_periods=1).sum()

    # Sazonalidade
    mes = df["date"].dt.month
    df["mes_seno"]    = np.sin(2 * np.pi * mes / 12)
    df["mes_cosseno"] = np.cos(2 * np.pi * mes / 12)

    # NDVI placeholder (não temos real, mas o modelo não usa NDVI como input)
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
    today = df.iloc[-1].to_dict()
    return df, today
