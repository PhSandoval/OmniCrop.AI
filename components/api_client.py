"""FastAPI client + data loading helpers."""
import requests
import pandas as pd
from pathlib import Path
import streamlit as st

API_URL = "http://localhost:8555/predict_ndvi"

FEATURE_KEYS = [
    "t_mean", "precipitacao_total", "radiacao_solar_mean",
    "gdd_acumulado_30d", "gdd_acumulado_90d",
    "balanco_hidrico_30d", "balanco_hidrico_lag_30d", "balanco_hidrico_lag_60d",
    "chuva_acumulada_lag_30d", "radiacao_acumulada_30d",
    "dias_calor_extremo_30d", "dias_frio_extremo_30d",
    "eventos_chuva_extrema_30d", "mes_seno", "mes_cosseno",
]


@st.cache_data
def load_dataset() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "data" / "processed" / "Dataset_SugarCane_processed.csv"
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def build_payload(row: dict) -> dict:
    return {k: float(row[k]) for k in FEATURE_KEYS}


def get_prediction(payload: dict) -> dict | None:
    try:
        r = requests.post(API_URL, json=payload, timeout=4)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def badge_html(status: str) -> str:
    if "Alto" in status:
        cls = "badge-green"
    elif "Médio" in status:
        cls = "badge-yellow"
    else:
        cls = "badge-red"
    return f'<span class="badge {cls}">{status}</span>'


def calcular_dss(mes_atual: int, ndvi_atual: float, ndvi_projetado: float = None) -> dict:
    """
    Matriz de decisão cruzando biologia da planta (fase do ano) com o impacto da simulação.
    Crescimento: Nov a Mar (Meses 11, 12, 1, 2, 3)
    Maturacao/Corte: Abr a Out (Meses 4 a 10)
    """
    # Identificar fase (Crescimento vs Maturacao)
    fase_crescimento = mes_atual in [11, 12, 1, 2, 3]
    fase_maturacao = not fase_crescimento
    
    # Se nao houver projecao, assumimos projecao igual atual (ou seja, delta 0)
    if ndvi_projetado is None:
        ndvi_projetado = ndvi_atual
        
    delta = ndvi_projetado - ndvi_atual
    
    # Regra absoluta (Independente do mes/fase)
    if delta < 0:
        return {
            "status_title": "❌ Alerta Simulacao",
            "mensagem_recomendacao": "A intervencao simulada reduziu ou nao alterou o vigor projetado. Estrategia nao recomendada (desperdicio de recursos)."
        }
        
    # Fase Maturação / Corte (Abr a Out)
    if fase_maturacao:
        if ndvi_atual < 0.4:
            return {
                "status_title": "🟡 Pronto p/ Corte",
                "mensagem_recomendacao": "O vigor atual indica estresse hidrico natural da maturacao ou area ja colhida. Intervencao Rejeitada: Irrigar agora causara desperdicio. Priorizar talhao na fila de colheita."
            }
        elif ndvi_atual >= 0.6:
            return {
                "status_title": "🟠 Alerta",
                "mensagem_recomendacao": "Cana vegetando durante periodo de maturacao. Avaliar aplicacao de maturador quimico para forcar o acumulo de ATR (acucar)."
            }
        else: # Zona cinza de maturacao
            return {
                "status_title": "🟢 Normal p/ Fase",
                "mensagem_recomendacao": "Condicao normal de desenvolvimento na maturacao. Manter monitoramento para a janela de corte ideal."
            }
            
    # Fase Crescimento (Nov a Mar)
    else:
        if ndvi_atual < 0.5 and delta > 0:
            return {
                "status_title": "🔴 Critico",
                "mensagem_recomendacao": "Deficit hidrico severo na fase de crescimento. Aprovar intervencao: Irrigacao de salvamento recomendada para evitar quebra de safra."
            }
        elif ndvi_atual >= 0.6:
            return {
                "status_title": "🟢 Normal",
                "mensagem_recomendacao": "Desenvolvimento vegetativo dentro da normalidade. Manter monitoramento padrao."
            }
        else: # Zona cinza de crescimento
            return {
                "status_title": "🟡 Atencao",
                "mensagem_recomendacao": "Desenvolvimento intermediario. Acompanhar indices nos proximos 15 dias."
            }
