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
    assert _resolve_column(df_en, ["col_inexistente_1", "col_inexistente_2"]) is None


def test_data_drift_dataclasses_to_dict(baseline_weather_df, drifted_weather_df):
    """Valida serialização to_dict() de FeatureDriftResult e DataDriftReport."""
    feat_res = evaluate_feature_drift(
        baseline_series=baseline_weather_df["temperature_2m_max"],
        current_series=drifted_weather_df["temperature_2m_max"],
        feature_name="temperature_2m_max",
    )
    d_feat = feat_res.to_dict()
    assert isinstance(d_feat, dict)
    assert d_feat["feature_name"] == "temperature_2m_max"
    assert "ks_statistic" in d_feat
    assert "psi" in d_feat
    assert "severity" in d_feat

    report = detect_data_drift(
        current_df=drifted_weather_df,
        baseline_df=baseline_weather_df,
        auto_alert=False,
    )
    d_rep = report.to_dict()
    assert isinstance(d_rep, dict)
    assert "timestamp" in d_rep
    assert "metrics" in d_rep
    assert d_rep["total_features_evaluated"] > 0
    assert "temperature_max" in d_rep["metrics"]


def test_calculate_psi_edge_cases():
    """Valida casos de borda matemáticos do cálculo de PSI."""
    # 1. Arrays vazios (cobre linha 104)
    assert calculate_psi(np.array([]), np.array([])) == 0.0
    assert calculate_psi(np.array([1.0, 2.0]), np.array([])) == 0.0

    # 2. Amostras com variância zero / valores idênticos (cobre linha 108)
    assert calculate_psi(np.array([5.0] * 10), np.array([5.0] * 10)) == 0.0
    assert calculate_psi(np.array([5.0] * 10), np.array([12.0] * 10)) == 1.0

    # 3. Menos de 2 bins retornados por np.unique (cobre linha 126)
    real_unique = np.unique

    def fake_unique(a, *args, **kwargs):
        if isinstance(a, np.ndarray) and len(a) > 0 and a[0] == -np.inf:
            return np.array([1.0])
        return real_unique(a, *args, **kwargs)

    with patch("numpy.unique", side_effect=fake_unique):
        assert calculate_psi(np.array([1.0, 2.0, 3.0, 4.0]), np.array([1.0, 2.0, 3.0, 4.0])) == 0.0


def test_evaluate_feature_drift_edge_cases_and_moderate():
    """Valida casos excepcionais e classificação de severidade MODERATE."""
    # 1. Séries vazias (cobre linhas 163-175)
    empty_res = evaluate_feature_drift(
        pd.Series([], dtype=float),
        pd.Series([], dtype=float),
        feature_name="empty_feature",
    )
    assert empty_res.drift_detected is False
    assert empty_res.severity == "STABLE"
    assert empty_res.ks_statistic == 0.0
    assert empty_res.p_value == 1.0

    # 2. ks_2samp lançando exceção (cobre linhas 182-184)
    with patch("src.mlops.data_drift.ks_2samp", side_effect=ValueError("Erro KS")):
        res_err = evaluate_feature_drift(
            pd.Series([1.0, 2.0, 3.0]),
            pd.Series([2.0, 3.0, 4.0]),
            feature_name="ks_error_test",
        )
        assert res_err.ks_statistic == 0.0
        assert res_err.p_value == 1.0

    # 3. Severidade MODERATE (cobre linha 197)
    # is_drift == True, mas psi < 0.25 e p_value >= 0.01 (ex: psi=0.15, p=0.03 com thresholds p<0.05, psi>=0.20)
    with patch("src.mlops.data_drift.ks_2samp") as mock_ks, \
         patch("src.mlops.data_drift.calculate_psi", return_value=0.15):
        mock_ks.return_value = MagicMock(statistic=0.25, pvalue=0.03)
        res_mod = evaluate_feature_drift(
            pd.Series([10.0, 20.0, 30.0]),
            pd.Series([12.0, 22.0, 32.0]),
            feature_name="mod_test",
            p_value_threshold=0.05,
            psi_threshold=0.20,
        )
        assert res_mod.drift_detected is True
        assert res_mod.severity == "MODERATE"


def test_detect_data_drift_fallback_baseline_and_custom_features(weather_population):
    """Valida fallback para baseline sintético e seleção customizada de features."""
    sample_df = weather_population.iloc[:50].copy()

    # 1. Baseline None com arquivos candidatos não encontrados (cobre linhas 254-269)
    with patch("pathlib.Path.exists", return_value=False):
        report_fallback = detect_data_drift(current_df=sample_df, baseline_df=None, auto_alert=False)
        assert isinstance(report_fallback, DataDriftReport)
        assert report_fallback.total_features_evaluated > 0

    # 2. Baseline candidate lança exceção ao ler (cobre linhas 259-260)
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pandas.read_csv", side_effect=Exception("CSV corrompido")):
        report_corrupt = detect_data_drift(current_df=sample_df, baseline_df=None, auto_alert=False)
        assert isinstance(report_corrupt, DataDriftReport)

    # 3. features_to_check customizado (cobre linhas 276-277 e 288-290)
    report_custom = detect_data_drift(
        current_df=sample_df,
        baseline_df=weather_population.iloc[50:100],
        features_to_check=["temperature_2m_max", "precipitation_sum"],
        auto_alert=False,
    )
    assert report_custom.total_features_evaluated == 2
    assert "temperature_2m_max" in report_custom.metrics


def test_detect_data_drift_webhook_env_and_exceptions(baseline_weather_df, drifted_weather_df, monkeypatch):
    """Valida resolução da URL do webhook via variável de ambiente e tratamento de falhas HTTP."""
    monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://discord.com/api/webhooks/mock_env")

    # 1. Disparo bem-sucedido via env var (cobre linha 332)
    with patch("src.utils.daily_alerts.send_webhook_alert", return_value=True) as mock_send:
        report = detect_data_drift(
            current_df=drifted_weather_df,
            baseline_df=baseline_weather_df,
            alert_webhook_url=None,
            auto_alert=True,
        )
        assert report.alert_dispatched is True
        mock_send.assert_called_once()

    # 2. Exceção no webhook tratada suavemente (cobre linhas 355-356)
    with patch("src.utils.daily_alerts.send_webhook_alert", side_effect=RuntimeError("Timeout no Webhook")):
        report_err = detect_data_drift(
            current_df=drifted_weather_df,
            baseline_df=baseline_weather_df,
            alert_webhook_url="https://mock.webhook.test",
            auto_alert=True,
        )
        assert report_err.alert_dispatched is False


def test_data_drift_cli_main_and_exit_codes(tmp_path, weather_population):
    """Valida execução via CLI (função main), suporte a Parquet/CSV e códigos de saída."""
    from src.mlops.data_drift import main

    pqt_curr = tmp_path / "silver.parquet"
    weather_population.iloc[350:].to_parquet(pqt_curr)
    pqt_base = tmp_path / "base.parquet"
    weather_population.iloc[:350].to_parquet(pqt_base)

    csv_curr = tmp_path / "silver.csv"
    weather_population.iloc[:50].to_csv(csv_curr, index=False)

    # 1. Execução com Parquet e baseline especificado (cobre linhas 363-409)
    cli_args = [
        "data_drift.py",
        "--current-path", str(pqt_curr),
        "--baseline-path", str(pqt_base),
        "--webhook-url", "https://mock.webhook.test",
        "--farm-name", "Fazenda CLI",
    ]
    with patch("sys.argv", cli_args), patch("src.utils.daily_alerts.send_webhook_alert", return_value=True):
        main()

    # 2. Execução com CSV sem baseline explícito (usa baseline padrão)
    with patch("sys.argv", ["data_drift.py", "--current-path", str(csv_curr)]):
        main()

    # 3. Arquivo de dados inexistente encerra com exit code 1 (cobre linhas 375-376)
    with patch("sys.argv", ["data_drift.py", "--current-path", str(tmp_path / "nao_existe.csv")]), \
         pytest.raises(SystemExit) as exc_missing:
        main()
    assert exc_missing.value.code == 1

    # 4. --fail-on-drift com deriva detectada encerra com exit code 1 (cobre linhas 411-412)
    csv_drift = tmp_path / "drift.csv"
    drifted = weather_population.iloc[350:].copy()
    drifted["temperature_2m_max"] = drifted["temperature_2m_max"] + 25.0
    drifted.to_csv(csv_drift, index=False)

    with patch("sys.argv", ["data_drift.py", "--current-path", str(csv_drift), "--baseline-path", str(pqt_base), "--fail-on-drift"]), \
         pytest.raises(SystemExit) as exc_drift:
        main()
    assert exc_drift.value.code == 1


def test_data_drift_module_as_main(tmp_path, weather_population):
    """Executa o módulo como __main__ para garantir 100% de cobertura do ponto de entrada (linha 416)."""
    import runpy

    csv_curr = tmp_path / "main_test.csv"
    weather_population.iloc[:50].to_csv(csv_curr, index=False)

    with patch("sys.argv", ["data_drift.py", "--current-path", str(csv_curr)]):
        runpy.run_module("src.mlops.data_drift", run_name="__main__")
