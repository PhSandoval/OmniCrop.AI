import pytest
import pandas as pd
import sys
from pathlib import Path

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.fetch_api import _build_features as build_features
from src.features.build_features import calculate_gdd, calculate_water_balance, compute_agronomic_features


def test_gda_mensal_calculation():
    """Teste agronômico preciso do GDA com base 18°C (Cana-de-Açúcar)."""
    # Temperaturas: [20, 22, 15, 10, 25] -> Esperado GDA diário: [2, 4, 0, 0, 7]
    dates = pd.date_range("2023-01-01", periods=5)
    df_dummy = pd.DataFrame({
        "date": dates,
        "t_mean": [20.0, 22.0, 15.0, 10.0, 25.0],
        "precipitacao_total": [0.0] * 5,
    })

    # Calcular features passando explicitamente crop_id="sugarcane"
    res_df = build_features(df_dummy, crop_id="sugarcane")

    # Os valores diários de gdd
    gda_diario = res_df["gdd"].tolist()
    assert gda_diario == [2.0, 4.0, 0.0, 0.0, 7.0]

    # O GDA Acumulado da janela
    gda_acumulado = res_df.iloc[-1]["GDA_mensal"]
    assert gda_acumulado == 13.0


def test_gda_calculation_soybean_and_corn():
    """Valida o cálculo dinâmico de GDA com temperatura base 10°C para Soja e Milho."""
    # Temperaturas: [20, 22, 15, 10, 25] -> Com base 10°C: [10, 12, 5, 0, 15] -> Soma = 42
    dates = pd.date_range("2023-01-01", periods=5)
    df_dummy = pd.DataFrame({
        "date": dates,
        "t_mean": [20.0, 22.0, 15.0, 10.0, 25.0],
        "precipitacao_total": [0.0] * 5,
    })

    res_soja = build_features(df_dummy, crop_id="soybean")
    assert res_soja["gdd"].tolist() == [10.0, 12.0, 5.0, 0.0, 15.0]
    assert res_soja.iloc[-1]["GDA_mensal"] == 42.0

    res_milho = build_features(df_dummy, crop_id="corn")
    assert res_milho["gdd"].tolist() == [10.0, 12.0, 5.0, 0.0, 15.0]
    assert res_milho.iloc[-1]["GDA_mensal"] == 42.0


def test_gda_calculation_coffee_and_pasture():
    """Valida o cálculo dinâmico de GDA para Café (Tb=10°C) e Pecuária (Tb=15°C)."""
    dates = pd.date_range("2023-01-01", periods=5)
    df_dummy = pd.DataFrame({
        "date": dates,
        "t_mean": [20.0, 22.0, 15.0, 10.0, 25.0],
        "precipitacao_total": [0.0] * 5,
    })

    # Café: Tb = 10.0 -> [10, 12, 5, 0, 15] -> Soma = 42.0
    res_cafe = build_features(df_dummy, crop_id="coffee")
    assert res_cafe["gdd"].tolist() == [10.0, 12.0, 5.0, 0.0, 15.0]
    assert res_cafe.iloc[-1]["GDA_mensal"] == 42.0

    # Pecuária: Tb = 15.0 -> [5, 7, 0, 0, 10] -> Soma = 22.0
    res_pasture = build_features(df_dummy, crop_id="pasture")
    assert res_pasture["gdd"].tolist() == [5.0, 7.0, 0.0, 0.0, 10.0]
    assert res_pasture.iloc[-1]["GDA_mensal"] == 22.0


def test_calculate_gdd_and_water_balance_functions():
    """Valida as funções unitárias de GDD e Balanço Hídrico com Kc por cultura."""
    # GDD
    assert calculate_gdd(25.0, crop_id="sugarcane") == 7.0   # 25 - 18 = 7
    assert calculate_gdd(25.0, crop_id="soybean") == 15.0    # 25 - 10 = 15
    assert calculate_gdd(25.0, crop_id="corn") == 15.0       # 25 - 10 = 15
    assert calculate_gdd(8.0, crop_id="soybean") == 0.0      # Não pode ser negativo

    # Balanço Hídrico Líquido (P - ET0 * Kc)
    # Cana: Kc = 1.05 -> ETc = 30 * 1.05 = 31.5 -> Balanço = 50 - 31.5 = 18.5
    assert calculate_water_balance(precipitation=50.0, et0=30.0, crop_id="sugarcane") == 18.5

    # Soja: Kc = 1.15 -> ETc = 30 * 1.15 = 34.5 -> Balanço = 50 - 34.5 = 15.5
    assert calculate_water_balance(precipitation=50.0, et0=30.0, crop_id="soybean") == 15.5

    # Milho: Kc = 1.20 -> ETc = 30 * 1.20 = 36.0 -> Balanço = 50 - 36.0 = 14.0
    assert calculate_water_balance(precipitation=50.0, et0=30.0, crop_id="corn") == 14.0

    # Café: Kc = 1.05, Tb = 10.0 -> GDD(25) = 15.0, Balanço = 50 - 31.5 = 18.5
    assert calculate_gdd(25.0, crop_id="coffee") == 15.0
    assert calculate_water_balance(precipitation=50.0, et0=30.0, crop_id="coffee") == 18.5

    # Pecuária: Kc = 0.90, Tb = 15.0 -> GDD(25) = 10.0, Balanço = 50 - 27.0 = 23.0
    assert calculate_gdd(25.0, crop_id="pasture") == 10.0
    assert calculate_water_balance(precipitation=50.0, et0=30.0, crop_id="pasture") == 23.0


def test_chuva_acumulada_limits():
    """Teste para garantir que as somas móveis tratam janelas menores no início dos dados (min_periods=1)."""
    dates = pd.date_range("2023-01-01", periods=5)
    df_dummy = pd.DataFrame({
        "date": dates,
        "t_mean": [25.0] * 5,
        "precipitacao_total": [5.0] * 5,
    })
    res_df = build_features(df_dummy, crop_id="sugarcane")

    assert res_df.iloc[0]["chuva_acumulada_30d"] == 5.0
    assert res_df.iloc[4]["chuva_acumulada_30d"] == 25.0


def test_compute_agronomic_features_pipeline():
    """Valida o cálculo enriquecido de features agronômicas no DataFrame via compute_agronomic_features."""
    dates = pd.date_range("2024-01-01", periods=10)
    df = pd.DataFrame({
        "date": dates,
        "t_mean": [26.0] * 10,
        "precipitacao_total": [10.0] * 10,
        "evapotranspiracao_total": [4.0] * 10,
    })
    res_cana = compute_agronomic_features(df, crop_id="sugarcane")
    assert "chuva_acumulada_30d" in res_cana.columns
    assert "GDA_mensal" in res_cana.columns
    assert "balanco_hidrico_30d" in res_cana.columns
    assert res_cana["chuva_acumulada_30d"].iloc[-1] == 100.0
    assert res_cana["gdd"].iloc[0] == 8.0  # 26 - 18
