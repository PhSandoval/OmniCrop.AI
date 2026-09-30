import pytest
import pandas as pd
import sys
from pathlib import Path

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.fetch_api import _build_features as build_features

def test_gda_mensal_calculation():
    """Teste agronômico preciso do GDA com base 18°C (sem valores negativos)."""
    # Temperaturas: [20, 22, 15, 10, 25] -> Esperado GDA diário: [2, 4, 0, 0, 7]
    dates = pd.date_range("2023-01-01", periods=5)
    df_dummy = pd.DataFrame({
        "date": dates,
        "t_mean": [20.0, 22.0, 15.0, 10.0, 25.0],
        "precipitacao_total": [0.0] * 5,
    })
    
    # Calcular features
    res_df = build_features(df_dummy)
    
    # Os valores diários de gdd
    gda_diario = res_df["gdd"].tolist()
    assert gda_diario == [2.0, 4.0, 0.0, 0.0, 7.0]
    
    # O GDA Acumulado da janela
    gda_acumulado = res_df.iloc[-1]["GDA_mensal"]
    assert gda_acumulado == 13.0

def test_chuva_acumulada_limits():
    """Teste para garantir que as somas móveis tratam janelas menores no início dos dados (min_periods=1)."""
    dates = pd.date_range("2023-01-01", periods=5)
    df_dummy = pd.DataFrame({
        "date": dates,
        "t_mean": [25.0] * 5,
        "precipitacao_total": [5.0] * 5,
    })
    res_df = build_features(df_dummy)
    
    assert res_df.iloc[0]["chuva_acumulada_30d"] == 5.0
    assert res_df.iloc[4]["chuva_acumulada_30d"] == 25.0
