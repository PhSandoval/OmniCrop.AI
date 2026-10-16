"""
Módulo de Engenharia de Features Agronômicas do OmniCrop AI.
Calcula Graus-Dia de Desenvolvimento (GDD / GDA) e Balanço Hídrico com Kc dinâmico por cultura.
"""
from __future__ import annotations
import pandas as pd
from src.core.crop_config import get_crop_parameters


def calculate_gdd(t_mean: float, t_base: float | None = None, crop_id: str = "sugarcane") -> float:
    """
    Calcula Graus-Dia de Desenvolvimento (GDD).
    Se t_base não for informado, busca a temperatura base dinamicamente do crop_config.py
    com base no crop_id (ex: Cana=18°C, Soja=10°C, Milho=10°C, Café=10°C, Pastagem=15°C).
    """
    if t_base is None:
        crop_params = get_crop_parameters(crop_id)
        t_base = crop_params.base_temp_celsius
    return max(0.0, float(t_mean) - float(t_base))


def calculate_water_balance(precipitation: float, et0: float, crop_id: str = "sugarcane") -> float:
    """
    Calcula o Balanço Hídrico Líquido ajustado pela evapotranspiração da cultura (ETc = ET0 * Kc).
    Busca o Kc padrão da cultura dinamicamente no crop_config.py.
    """
    crop_params = get_crop_parameters(crop_id)
    etc = float(et0) * crop_params.kc_default
    return round(float(precipitation) - etc, 2)


def compute_agronomic_features(daily_df: pd.DataFrame, crop_id: str = "sugarcane") -> pd.DataFrame:
    """
    Gera features agronômicas acumuladas e enriquecidas para a cultura especificada
    a partir de um DataFrame de dados meteorológicos diários.
    """
    df = daily_df.copy()
    crop_params = get_crop_parameters(crop_id)
    t_base = crop_params.base_temp_celsius

    precip_col = "precipitacao_total" if "precipitacao_total" in df.columns else "precipitation_sum"
    et0_col = "evapotranspiracao_total" if "evapotranspiracao_total" in df.columns else "et0_fao_evapotranspiration"
    t_col = "t_mean" if "t_mean" in df.columns else "temperature_2m_mean"

    # Acúmulos pluviométricos móveis
    df["chuva_acumulada_30d"] = df[precip_col].rolling(window=30, min_periods=1).sum()
    df["chuva_acumulada_60d"] = df[precip_col].rolling(window=60, min_periods=1).sum()
    df["chuva_acumulada_90d"] = df[precip_col].rolling(window=90, min_periods=1).sum()

    # Graus-Dia Acumulados (GDA) dinâmico
    df["gdd"] = df[t_col].apply(lambda x: calculate_gdd(x, t_base=t_base, crop_id=crop_id))
    df["GDA_mensal"] = df["gdd"].rolling(window=30, min_periods=1).sum()

    # Balanço hídrico diário e acumulado
    if et0_col in df.columns:
        df["etc_diaria"] = df[et0_col] * crop_params.kc_default
        df["balanco_hidrico_30d"] = (df[precip_col] - df["etc_diaria"]).rolling(window=30, min_periods=1).sum()

    return df
