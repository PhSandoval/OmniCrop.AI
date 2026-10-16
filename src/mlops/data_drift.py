"""
Módulo de Deteção de Degradação de Dados (Data Drift) - MLOps OmniCrop AI.
Compara estatisticamente a nova carga de dados da Camada Prata com um baseline de treino
utilizando o Population Stability Index (PSI) e o teste de Kolmogorov-Smirnov (KS-test).
Dispara alertas operacionais quando a distribuição de features agronômicas sofrer deriva severa.
"""
from __future__ import annotations
import os
import sys
import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

# Adiciona a raiz do projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class FeatureDriftResult:
    """Resultado estatístico da avaliação de drift para uma feature individual."""
    feature_name: str
    ks_statistic: float
    p_value: float
    psi: float
    drift_detected: bool
    severity: str  # "STABLE" | "MODERATE" | "CRITICAL"
    baseline_mean: float
    current_mean: float
    baseline_std: float
    current_std: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_name": self.feature_name,
            "ks_statistic": round(self.ks_statistic, 4),
            "p_value": round(self.p_value, 5),
            "psi": round(self.psi, 4),
            "drift_detected": self.drift_detected,
            "severity": self.severity,
            "baseline_mean": round(self.baseline_mean, 3),
            "current_mean": round(self.current_mean, 3),
            "baseline_std": round(self.baseline_std, 3),
            "current_std": round(self.current_std, 3),
        }


@dataclass
class DataDriftReport:
    """Relatório consolidado de Data Drift do pipeline."""
    timestamp: str
    total_features_evaluated: int
    drifted_features_count: int
    dataset_drift_detected: bool
    metrics: Dict[str, FeatureDriftResult] = field(default_factory=dict)
    alert_dispatched: bool = False
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_features_evaluated": self.total_features_evaluated,
            "drifted_features_count": self.drifted_features_count,
            "dataset_drift_detected": self.dataset_drift_detected,
            "alert_dispatched": self.alert_dispatched,
            "summary": self.summary,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
        }


# ── Cálculo Matemático do Population Stability Index (PSI) ──────────────────
def calculate_psi(
    expected: np.ndarray | pd.Series,
    actual: np.ndarray | pd.Series,
    num_bins: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """
    Calcula o Population Stability Index (PSI) entre duas distribuições contínuas.

    Fórmula:
        PSI = sum((Actual% - Expected%) * ln(Actual% / Expected%))

    Interpretação Padrão de Engenharia de MLOps:
    - PSI < 0.10: Estável, sem mudança de distribuição estatisticamente relevante.
    - 0.10 <= PSI < 0.20: Alerta moderado, leve mudança na população.
    - PSI >= 0.20: Deriva severa (Data Drift Crítico), modelo de ML descalibrado.
    """
    exp = np.asarray(expected, dtype=float)
    act = np.asarray(actual, dtype=float)

    # Remove valores nulos ou infinitos
    exp = exp[np.isfinite(exp)]
    act = act[np.isfinite(act)]

    if len(exp) == 0 or len(act) == 0:
        return 0.0

    # Se todos os valores forem idênticos (variância zero)
    if np.all(exp == exp[0]) and np.all(act == act[0]):
        return 0.0 if exp[0] == act[0] else 1.0

    # Determina o número efetivo de quantis para estabilidade numérica
    # Para lotes pequenos (< 150 registros), reduz o número de bins para evitar ruído Poisson
    min_len = min(len(exp), len(act))
    if min_len < 150:
        effective_bins = min(num_bins, max(4, min_len // 20))
    else:
        effective_bins = num_bins

    # Define os limites de bins usando os quantis do baseline esperado
    quantiles = np.linspace(0, 100, effective_bins + 1)
    bins = np.percentile(exp, quantiles)
    bins[0] = -np.inf
    bins[-1] = np.inf
    bins = np.unique(bins)  # Remove limites duplicados caso haja dados discretizados

    if len(bins) < 2:
        return 0.0

    # Contagens observadas em cada bin
    exp_counts, _ = np.histogram(exp, bins=bins)
    act_counts, _ = np.histogram(act, bins=bins)

    # Converte para proporções com suavização epsilon para evitar divisão por zero
    exp_pct = exp_counts / len(exp)
    act_pct = act_counts / len(act)

    exp_pct = np.where(exp_pct == 0, epsilon, exp_pct)
    act_pct = np.where(act_pct == 0, epsilon, act_pct)

    # Normaliza novamente após a adição do epsilon
    exp_pct = exp_pct / np.sum(exp_pct)
    act_pct = act_pct / np.sum(act_pct)

    # Cálculo da divergência de Kullback-Leibler simetrizada (PSI)
    psi_value = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(np.clip(psi_value, 0.0, 10.0))


# ── Avaliação de Feature Individual ─────────────────────────────────────────
def evaluate_feature_drift(
    baseline_series: pd.Series,
    current_series: pd.Series,
    feature_name: str,
    p_value_threshold: float = 0.05,
    psi_threshold: float = 0.20,
) -> FeatureDriftResult:
    """
    Executa o teste de hipótese Kolmogorov-Smirnov (KS-test) e o cálculo de PSI
    para determinar se a feature atual divergiu do baseline de treinamento.
    """
    base_clean = baseline_series.dropna().to_numpy()
    curr_clean = current_series.dropna().to_numpy()

    if len(base_clean) == 0 or len(curr_clean) == 0:
        return FeatureDriftResult(
            feature_name=feature_name,
            ks_statistic=0.0,
            p_value=1.0,
            psi=0.0,
            drift_detected=False,
            severity="STABLE",
            baseline_mean=0.0,
            current_mean=0.0,
            baseline_std=0.0,
            current_std=0.0,
        )

    # 1. Teste de Kolmogorov-Smirnov (Duas Amostras)
    try:
        ks_res = ks_2samp(base_clean, curr_clean)
        ks_stat = float(ks_res.statistic)
        p_val = float(ks_res.pvalue)
    except Exception:
        ks_stat = 0.0
        p_val = 1.0

    # 2. Population Stability Index (PSI)
    psi_val = calculate_psi(base_clean, curr_clean)

    # 3. Regra de Decisão de Drift
    is_drift = (p_val < p_value_threshold) or (psi_val >= psi_threshold)

    # Severidade
    if is_drift:
        if psi_val >= 0.25 or p_val < 0.01:
            severity = "CRITICAL"
        else:
            severity = "MODERATE"
    else:
        severity = "STABLE"

    return FeatureDriftResult(
        feature_name=feature_name,
        ks_statistic=ks_stat,
        p_value=p_val,
        psi=psi_val,
        drift_detected=is_drift,
        severity=severity,
        baseline_mean=float(np.mean(base_clean)),
        current_mean=float(np.mean(curr_clean)),
        baseline_std=float(np.std(base_clean)),
        current_std=float(np.std(curr_clean)),
    )


# ── Mapeamento Padrão de Nomes de Variáveis Críticas ─────────────────────────
DEFAULT_FEATURE_MAPPINGS = {
    "precipitation": ["precipitation_sum", "precipitacao_total", "precipitation"],
    "temperature_max": ["temperature_2m_max", "t_max", "temperature_max"],
    "temperature_min": ["temperature_2m_min", "t_min", "temperature_min"],
    "et0": ["et0_fao_evapotranspiration", "evapotranspiracao_total", "et0"],
    "gdd": ["gdd", "gda_mensal", "GDA_mensal"],
}


def _resolve_column(df: pd.DataFrame, candidate_names: List[str]) -> str | None:
    for name in candidate_names:
        if name in df.columns:
            return name
    return None


# ── Pipeline Principal de Monitoramento de Data Drift ───────────────────────
def detect_data_drift(
    current_df: pd.DataFrame,
    baseline_df: pd.DataFrame | None = None,
    features_to_check: List[str] | None = None,
    alert_webhook_url: str | None = None,
    farm_name: str = "Fazenda Monitorada",
    auto_alert: bool = True,
    p_value_threshold: float = 0.05,
    psi_threshold: float = 0.20,
) -> DataDriftReport:
    """
    Compara a nova carga de dados da Camada Prata com a base de referência (Baseline).
    Se for detectada deriva estatística em variáveis críticas, dispara um webhook de alerta MLOps.
    """
    # 1. Carrega o Baseline de Referência se não fornecido
    if baseline_df is None:
        baseline_candidates = [
            PROJECT_ROOT / "data" / "processed" / "Dataset_SugarCane_processed.csv",
            PROJECT_ROOT / "data" / "processed" / "dados_features.csv",
            PROJECT_ROOT / "data" / "interim" / "Dataset_SugarCane_interim.csv",
        ]
        for candidate in baseline_candidates:
            if candidate.exists():
                try:
                    baseline_df = pd.read_csv(candidate)
                    break
                except Exception:
                    continue

    if baseline_df is None or baseline_df.empty:
        # Cria um fallback seguro sintético com dados típicos do canavial paulista
        baseline_df = pd.DataFrame({
            "precipitation_sum": [0.0, 5.0, 15.0, 0.0, 0.0, 2.0, 25.0, 0.0, 0.0, 8.0] * 10,
            "temperature_2m_max": [30.0, 31.5, 28.0, 32.0, 33.5, 29.0, 27.5, 31.0, 32.5, 30.0] * 10,
            "temperature_2m_min": [18.0, 19.5, 17.0, 19.0, 20.5, 18.0, 16.5, 18.0, 19.5, 18.0] * 10,
            "gdd": [6.0, 7.5, 4.5, 7.5, 9.0, 5.5, 4.0, 6.5, 8.0, 6.0] * 10,
        })

    # 2. Resolução das Colunas a serem Auditadas
    metrics: Dict[str, FeatureDriftResult] = {}
    evaluated_count = 0
    drift_count = 0

    if features_to_check:
        cols_to_eval = [(f, f) for f in features_to_check if f in current_df.columns and f in baseline_df.columns]
    else:
        cols_to_eval = []
        for canonical_name, candidates in DEFAULT_FEATURE_MAPPINGS.items():
            col_curr = _resolve_column(current_df, candidates)
            col_base = _resolve_column(baseline_df, candidates)
            if col_curr and col_base:
                cols_to_eval.append((canonical_name, col_curr, col_base))

    # 3. Execução das Análises de Deriva
    for item in cols_to_eval:
        if len(item) == 2:
            label, col_name = item
            base_col, curr_col = col_name, col_name
        else:
            label, curr_col, base_col = item

        res = evaluate_feature_drift(
            baseline_series=baseline_df[base_col],
            current_series=current_df[curr_col],
            feature_name=f"{label} ({curr_col})",
            p_value_threshold=p_value_threshold,
            psi_threshold=psi_threshold,
        )
        metrics[label] = res
        evaluated_count += 1
        if res.drift_detected:
            drift_count += 1

    dataset_drift = drift_count > 0

    # 4. Geração do Resumo Executivo MLOps
    if not dataset_drift:
        summary = (
            f"✅ Estabilidade Estatística Confirmada: Nenhuma das {evaluated_count} variáveis monitoradas "
            f"apresentou Data Drift significativo (PSI < {psi_threshold} e KS p-value >= {p_value_threshold})."
        )
    else:
        drifted_names = [f"'{res.feature_name}' (PSI={res.psi:.3f}, p={res.p_value:.4f})" for res in metrics.values() if res.drift_detected]
        summary = (
            f"🚨 Alerta MLOps: Data Drift detectado em {drift_count} de {evaluated_count} variáveis críticas: "
            f"{', '.join(drifted_names)}. Recomenda-se avaliar retreinamento ou checar sensores/APIs."
        )

    report = DataDriftReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_features_evaluated=evaluated_count,
        drifted_features_count=drift_count,
        dataset_drift_detected=dataset_drift,
        metrics=metrics,
        summary=summary,
    )

    # 5. Disparo de Webhook Operacional se Drift for Detectado
    if dataset_drift and auto_alert:
        webhook_target = alert_webhook_url or os.getenv("ALERT_WEBHOOK_URL")
        if webhook_target:
            try:
                from src.utils.daily_alerts import send_webhook_alert

                alert_messages = [
                    f"⚠️ MLOps Data Drift detectado em {drift_count} variáveis da Camada Prata.",
                ]
                for res in metrics.values():
                    if res.drift_detected:
                        alert_messages.append(
                            f"Variável {res.feature_name}: PSI={res.psi:.3f} | KS p-value={res.p_value:.4f} "
                            f"(Média Atual: {res.current_mean:.2f} vs Base: {res.baseline_mean:.2f})"
                        )
                alert_messages.append("Ação: Avaliar retreinamento dos modelos preditivos e inspecionar fontes de dados.")

                ok = send_webhook_alert(
                    webhook_url=webhook_target,
                    farm_name=farm_name,
                    alertas=alert_messages,
                    ndvi=None,
                )
                report.alert_dispatched = ok
            except Exception as e:
                print(f"Aviso: Falha ao despachar webhook de Data Drift: {e}")

    return report


# ── Execução CLI ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="OmniCrop MLOps - Deteção de Data Drift (Camada Prata vs Baseline)")
    parser.add_argument("--current-path", required=True, help="Caminho do arquivo Parquet/CSV da Camada Prata a ser auditado")
    parser.add_argument("--baseline-path", default=None, help="Caminho opcional do arquivo de Baseline de treino")
    parser.add_argument("--webhook-url", default=None, help="URL de Webhook para disparo de alertas de drift")
    parser.add_argument("--farm-name", default="Fazenda Operacional", help="Nome da fazenda auditada")
    parser.add_argument("--fail-on-drift", action="store_true", help="Encerra com exit code 1 se houver drift crítico")

    args = parser.parse_args()

    print("🛡️ Iniciando auditoria de Data Drift (MLOps)...")
    curr_path = Path(args.current_path)
    if not curr_path.exists():
        print(f"❌ Arquivo de dados não encontrado: {curr_path}")
        sys.exit(1)

    if curr_path.suffix == ".parquet":
        current_df = pd.read_parquet(curr_path)
    else:
        current_df = pd.read_csv(curr_path)

    baseline_df = None
    if args.baseline_path:
        base_path = Path(args.baseline_path)
        if base_path.exists():
            baseline_df = pd.read_parquet(base_path) if base_path.suffix == ".parquet" else pd.read_csv(base_path)

    report = detect_data_drift(
        current_df=current_df,
        baseline_df=baseline_df,
        alert_webhook_url=args.webhook_url,
        farm_name=args.farm_name,
    )

    print("\n" + "=" * 70)
    print("📋 RELATÓRIO EXECUTIVO DE DATA DRIFT - MLOPS")
    print("=" * 70)
    print(report.summary)
    print("\nDetalhamento Estatístico:")
    for key, res in report.metrics.items():
        status_icon = "🔴" if res.drift_detected else "🟢"
        print(
            f"  {status_icon} [{res.severity:<8}] {res.feature_name:<30} | "
            f"PSI: {res.psi:.4f} | KS p-val: {res.p_value:.5f} | "
            f"Média Atual: {res.current_mean:6.2f} (Base: {res.baseline_mean:6.2f})"
        )
    print("=" * 70)

    if report.dataset_drift_detected and args.fail_on_drift:
        print("🚨 Pipeline interrompido devido a Data Drift crítico detectado.")
        sys.exit(1)


if __name__ == "__main__":
    main()
