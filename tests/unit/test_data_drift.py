"""
Testes Unitários para o Módulo de MLOps - Deteção de Data Drift (Fase 3).
Verifica os algoritmos de PSI (Population Stability Index) e KS-Test (Kolmogorov-Smirnov),
garantindo que alertas de degradação estatística só sejam disparados mediante deriva real.
"""
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest

from src.mlops.data_drift import (
    calculate_psi,
    evaluate_feature_drift,
    detect_data_drift,
    _resolve_column,
    FeatureDriftResult,
    DataDriftReport,
)


@pytest.fixture
def weather_population() -> pd.DataFrame:
    """População climática sintética representativa para testes controlados."""
    np.random.seed(42)
    n = 500
    return pd.DataFrame({
        "temperature_2m_max": np.random.normal(loc=30.0, scale=3.0, size=n),
        "temperature_2m_min": np.random.normal(loc=19.0, scale=2.5, size=n),
        "precipitation_sum": np.random.exponential(scale=5.0, size=n),
        "et0_fao_evapotranspiration": np.random.normal(loc=4.5, scale=0.8, size=n),
        "gdd": np.random.normal(loc=6.5, scale=1.5, size=n),
    })


@pytest.fixture
def baseline_weather_df(weather_population) -> pd.DataFrame:
    """Distribuição climática histórica de referência (Baseline de treino, 350 dias)."""
    return weather_population.iloc[:350].copy()


@pytest.fixture
def identical_weather_df(weather_population) -> pd.DataFrame:
    """Distribuição recente estatisticamente aderente ao baseline (150 dias da mesma população)."""
    return weather_population.iloc[350:].copy()


@pytest.fixture
def drifted_weather_df(weather_population) -> pd.DataFrame:
    """Distribuição anômala com severa anomalia térmica e seca extrema (Data Drift Crítico)."""
    df = weather_population.iloc[350:].copy()
    df["temperature_2m_max"] = df["temperature_2m_max"] + 15.0  # Onda de calor extrema (+15°C)
    df["temperature_2m_min"] = df["temperature_2m_min"] + 10.0
    df["precipitation_sum"] = 0.0                               # Seca severa
    df["et0_fao_evapotranspiration"] = df["et0_fao_evapotranspiration"] * 2.2
    df["gdd"] = df["gdd"] + 12.0
    return df


def test_psi_identical_distributions():
    """Testa se o cálculo do PSI entre amostras da mesma população é < 0.10 (estável)."""
    np.random.seed(42)
    dist1 = np.random.normal(loc=25.0, scale=5.0, size=500)
    dist2 = np.random.normal(loc=25.0, scale=5.0, size=300)

    psi_val = calculate_psi(dist1, dist2)
    assert psi_val < 0.10, f"PSI esperado < 0.10 para populações idênticas, obtido: {psi_val}"


def test_psi_drifted_distribution():
    """Testa se o PSI ultrapassa 0.20 quando a média ou variância diverge drasticamente."""
    np.random.seed(42)
    dist_baseline = np.random.normal(loc=20.0, scale=2.0, size=300)
    dist_anomalous = np.random.normal(loc=35.0, scale=4.0, size=100)  # Salto de +15 unidades

    psi_val = calculate_psi(dist_baseline, dist_anomalous)
    assert psi_val > 0.20, f"PSI esperado > 0.20 para população desviada, obtido: {psi_val}"


def test_evaluate_feature_drift_stable(baseline_weather_df, identical_weather_df):
    """Testa avaliação de feature sem drift."""
    res = evaluate_feature_drift(
        baseline_series=baseline_weather_df["temperature_2m_max"],
        current_series=identical_weather_df["temperature_2m_max"],
        feature_name="temperature_2m_max",
    )
    assert isinstance(res, FeatureDriftResult)
    assert res.drift_detected is False
    assert res.severity == "STABLE"
    assert res.p_value >= 0.05
    assert res.psi < 0.20


def test_evaluate_feature_drift_critical(baseline_weather_df, drifted_weather_df):
    """Testa avaliação de feature com anomalia crítica."""
    res = evaluate_feature_drift(
        baseline_series=baseline_weather_df["temperature_2m_max"],
        current_series=drifted_weather_df["temperature_2m_max"],
        feature_name="temperature_2m_max",
    )
    assert isinstance(res, FeatureDriftResult)
    assert res.drift_detected is True
    assert res.severity == "CRITICAL"
    assert res.p_value < 0.01
    assert res.psi > 0.25


def test_detect_data_drift_stable_does_not_alert(baseline_weather_df, identical_weather_df):
    """Garante que dados conformes NÃO disparem alertas para os operadores."""
    with patch("src.utils.daily_alerts.send_webhook_alert") as mock_alert:
        report = detect_data_drift(
            current_df=identical_weather_df,
            baseline_df=baseline_weather_df,
            alert_webhook_url="https://mock.webhook.test",
            auto_alert=True,
        )
        assert isinstance(report, DataDriftReport)
        assert report.dataset_drift_detected is False
        assert report.drifted_features_count == 0
        assert report.alert_dispatched is False
        mock_alert.assert_not_called()


def test_detect_data_drift_anomalous_triggers_alert(baseline_weather_df, drifted_weather_df):
    """Garante que anomalias críticas acionem o envio de webhook com a lista de variáveis corrompidas."""
    with patch("src.utils.daily_alerts.send_webhook_alert", return_value=True) as mock_alert:
        report = detect_data_drift(
            current_df=drifted_weather_df,
            baseline_df=baseline_weather_df,
            alert_webhook_url="https://mock.webhook.test",
            farm_name="Fazenda Piloto Teste",
            auto_alert=True,
        )
        assert isinstance(report, DataDriftReport)
        assert report.dataset_drift_detected is True
        assert report.drifted_features_count >= 1
        assert report.alert_dispatched is True

        # Verifica chamada ao webhook
        mock_alert.assert_called_once()
        call_args = mock_alert.call_args
        assert "Fazenda Piloto Teste" in call_args[0] or "Fazenda Piloto Teste" in str(call_args)


def test_resolve_column_supports_portuguese_and_english():
    """Valida interoperabilidade de nomenclatura de colunas (Open-Meteo vs Dataset de Treino)."""
    df_en = pd.DataFrame({"precipitation_sum": [10.0], "temperature_2m_max": [32.0]})
    df_pt = pd.DataFrame({"precipitacao_total": [10.0], "t_max": [32.0]})

    col_en = _resolve_column(df_en, ["precipitation_sum", "precipitacao_total"])
    col_pt = _resolve_column(df_pt, ["precipitation_sum", "precipitacao_total"])

    assert col_en == "precipitation_sum"
    assert col_pt == "precipitacao_total"
