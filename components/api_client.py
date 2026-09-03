"""FastAPI client + data loading helpers."""
import requests
import pandas as pd
from pathlib import Path
import streamlit as st

API_URL = "http://localhost:8555/predict_ndvi"

FEATURE_KEYS = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']


@st.cache_data
def load_dataset() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "data" / "processed" / "Dataset_SugarCane_processed.csv"
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def build_payload(row: dict) -> dict:
    return {k: float(row[k]) for k in FEATURE_KEYS}


import joblib

@st.cache_resource
def load_model():
    path = Path(__file__).resolve().parents[1] / "models" / "ndvi_xgb_model.pkl"
    return joblib.load(path)

def get_prediction(payload: dict) -> dict | None:
    try:
        model = load_model()
        # Convert dictionary to DataFrame for sklearn prediction (keeping feature order)
        df_input = pd.DataFrame([payload], columns=FEATURE_KEYS)
        pred = model.predict(df_input)[0]
        
        # Simulando os alertas do DSS que a API costumava retornar
        alertas = []
        if payload.get("chuva_acumulada_30d", 0) < 30:
            alertas.append("ALERTA HÍDRICO: Déficit hídrico agudo detectado nos últimos 30 dias.")
        
        return {
            "ndvi_previsto": round(float(pred), 3),
            "status_vigor": "", # Não usado diretamente mais
            "fatores_de_risco_identificados": alertas,
            "plano_de_acao": "", # O DSS cuida disso
            "confiabilidade_modelo": "Alta (Margem de Erro Histórica de MAE 0.02)"
        }
    except Exception as e:
        st.error(f"Prediction Error: {e}")
        return None


def badge_html(status: str) -> str:
    if "Alto" in status:
        cls = "badge-green"
    elif "Médio" in status:
        cls = "badge-yellow"
    else:
        cls = "badge-red"
    return f'<span class="badge {cls}">{status}</span>'


def calcular_dss(mes_atual: int, ndvi_atual: float, ndvi_projetado: float = None, cenario: str = "", chuva_projetada: float = 0, gda_projetado: float = 0) -> dict:
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
    
    # Regras especificas de novos cenarios (ignoram fase do ano)
    if "Colheita" in cenario:
        if chuva_projetada > 50:
            return {
                "status_title": "🔴 Risco Operacional",
                "mensagem_recomendacao": "Alerta: Previsao de chuva forte. Risco altíssimo de atolamento de máquinas e pisoteio de soqueira. Interromper operacoes de corte."
            }
        elif gda_projetado > 100 and chuva_projetada < 20:
            return {
                "status_title": "🟢 Corte Liberado",
                "mensagem_recomendacao": "Cenario ideal. GDA alto para maturação e solo seco para trafegabilidade. Liberado para Corte Mecanizado."
            }
        else:
            return {
                "status_title": "🟡 Janela Sub-ótima",
                "mensagem_recomendacao": "Condicao aceitavel, porem avaliar maturador para acelerar acumulo de ATR antes de eventuais chuvas."
            }
            
    if "Plantio" in cenario:
        if chuva_projetada < 20:
            return {
                "status_title": "🔴 Risco de Falha",
                "mensagem_recomendacao": "Chuva projetada muito baixa. O plantio agora apresenta altissimo risco de falha na brotação dos toletes."
            }
        elif gda_projetado > 90 and chuva_projetada >= 40:
            return {
                "status_title": "🟢 Plantio Liberado",
                "mensagem_recomendacao": "Condicao termohidrica excelente (GDA e Umidade) para brotação rapida e uniforme dos toletes."
            }
            
    if "Adubacao" in cenario:
        if chuva_projetada < 10:
            return {
                "status_title": "🔴 Desperdicio",
                "mensagem_recomendacao": "Não aplicar ureia/nitrogenio. Solo seco nao incorporara o fertilizante, causando perda volatil. Aguardar chuva."
            }
        elif chuva_projetada > 100:
            return {
                "status_title": "🟡 Lixiviação",
                "mensagem_recomendacao": "Chuva excessiva projetada. Risco de lixiviação de nutrientes. Fracionar a dose recomendada."
            }

    # Fase Maturação / Corte (Abr a Out)
    if fase_maturacao:
        if ndvi_atual < 0.4:
            return {
                "status_title": "🟡 Pronto p/ Corte",
                "mensagem_recomendacao": "O vigor atual indica estresse hídrico natural da maturacao ou area ja colhida. Intervencao Rejeitada: Irrigar agora causara desperdício. Priorizar talhao na fila de colheita."
            }
        elif ndvi_atual >= 0.6:
            return {
                "status_title": "🟠 Alerta",
                "mensagem_recomendacao": "Cana vegetando durante periodo de maturacao. Avaliar aplicacao de maturador químico para forcar o acumulo de ATR (acucar)."
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
                "mensagem_recomendacao": "Déficit hídrico severo na fase de crescimento. Aprovar intervencao: Irrigacao de salvamento recomendada para evitar quebra de safra."
            }
        elif ndvi_atual >= 0.6:
            return {
                "status_title": "🟢 Normal",
                "mensagem_recomendacao": "Desenvolvimento vegetativo dentro da normalidade. Manter monitoramento padrao."
            }
        else: # Zona cinza de crescimento
            return {
                "status_title": "🟡 Atenção",
                "mensagem_recomendacao": "Desenvolvimento intermediario. Acompanhar indices nos próximos 15 dias."
            }
