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
    fase_crescimento = mes_atual in [11, 12, 1, 2, 3]
    fase_maturacao = not fase_crescimento
    
    if ndvi_projetado is None:
        ndvi_projetado = ndvi_atual
        
    delta = ndvi_projetado - ndvi_atual
    
    if "Colheita" in cenario:
        msg_delta = " O Maturador químico agiu com sucesso derrubando o vigor vegetativo." if delta < 0 else ""
        if chuva_projetada > 50:
            return {
                "status_title": "🔴 Risco Operacional",
                "mensagem_recomendacao": f"Alerta: Previsao de chuva forte. Risco altíssimo de atolamento de máquinas e pisoteio de soqueira. Interromper operacoes de corte.{msg_delta}"
            }
        elif gda_projetado > 100 and chuva_projetada < 20:
            return {
                "status_title": "🟢 Corte Liberado",
                "mensagem_recomendacao": f"Cenario ideal. GDA alto para maturação e solo seco para trafegabilidade. Liberado para Corte Mecanizado.{msg_delta}"
            }
        else:
            return {
                "status_title": "🟡 Janela Sub-ótima",
                "mensagem_recomendacao": f"Condicao aceitavel, porem avaliar maturador para acelerar acumulo de ATR antes de eventuais chuvas.{msg_delta}"
            }
            
    if "Plantio" in cenario:
        if ndvi_atual < 0.25:
            base_msg = "Solo limpo/preparado detectado. "
        else:
            base_msg = "Atenção: NDVI alto indica presença de soqueira velha ou mato. Recomenda-se dessecação antes do plantio. "
            
        if chuva_projetada < 20:
            return {
                "status_title": "🔴 Risco de Falha",
                "mensagem_recomendacao": base_msg + "Chuva projetada muito baixa. Risco de falha na brotação por seca."
            }
        elif chuva_projetada > 150:
            return {
                "status_title": "🔴 Risco de Podridão",
                "mensagem_recomendacao": base_msg + "Volume excessivo de água (Chuva + Irrigação). Risco crítico de alagamento do sulco, sufocamento radicular e podridão dos toletes. Cancele a irrigação!"
            }
        elif gda_projetado > 80 and chuva_projetada >= 40:
            return {
                "status_title": "🟢 Plantio Liberado",
                "mensagem_recomendacao": base_msg + "Condição termohidrica excelente para brotação rápida e uniforme."
            }
        else:
            return {
                "status_title": "🟡 Plantio com Restrições",
                "mensagem_recomendacao": base_msg + "Condição razoável, mas exigirá monitoramento."
            }
            
    if "Adubação" in cenario or "Adubacao" in cenario:
        is_comum = "Comum" in cenario
        is_protegida = "Protegida" in cenario
        is_nitrato = "Nitrato" in cenario
        
        if chuva_projetada < 15:
            if is_comum:
                return {
                    "status_title": "🔴 Volatilização Severa",
                    "mensagem_recomendacao": "A chuva projetada é muito baixa para incorporar a Ureia Comum. Haverá severa perda de nitrogênio para a atmosfera (gás amônia). Aguarde chuvas ou troque para Ureia Protegida."
                }
            elif is_nitrato:
                return {
                    "status_title": "🟡 Absorção Lenta",
                    "mensagem_recomendacao": "O Nitrato não volatiliza, mas a falta de umidade no solo limitará a absorção pelas raízes. A resposta vegetativa será lenta."
                }
            else:
                return {
                    "status_title": "🟢 Ureia Protegida Segura",
                    "mensagem_recomendacao": "A Ureia Protegida (com inibidor de urease) resiste ao sol e não volatiliza. Pode aplicar agora com segurança e aguardar a próxima chuva para incorporação."
                }
        elif chuva_projetada > 100:
            if is_nitrato:
                return {
                    "status_title": "🔴 Risco Crítico de Lixiviação",
                    "mensagem_recomendacao": "Chuva excessiva! O Nitrato possui altíssima solubilidade e será lavado (lixiviado) para o lençol freático antes da planta absorver. Prejuízo financeiro alto."
                }
            elif is_comum:
                return {
                    "status_title": "🟡 Risco Moderado",
                    "mensagem_recomendacao": "Volume alto de chuvas. Há risco de lixiviação parcial do nitrogênio. Considere fracionar a dose da adubação para não perder produto."
                }
            else:
                return {
                    "status_title": "🟢 Ureia Protegida Segura",
                    "mensagem_recomendacao": "Os polímeros da Ureia Protegida garantem liberação gradual, suportando bem o volume alto de chuvas sem lixiviar rapidamente."
                }
        else:
            return {
                "status_title": "🟢 Janela Ideal",
                "mensagem_recomendacao": "Condições termohídricas perfeitas para adubação de cobertura. Umidade suficiente para incorporação rápida no solo sem lixiviação grave."
            }

    if "Irrigação" in cenario:
        if chuva_projetada > 150:
             return {
                "status_title": "🔴 Risco de Alagamento",
                "mensagem_recomendacao": "Volume de água excessivo. Cancele o programa de irrigação para não sufocar o sistema radicular."
             }
        if delta < 0:
            return {
                "status_title": "❌ Alerta Simulacao",
                "mensagem_recomendacao": "A irrigação simulada não reverteu a queda de vigor. Estratégia não recomendada (desperdício de recursos e energia)."
            }

    # Fallback / Analise da Fase Fenológica Padrão
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
        else:
            return {
                "status_title": "🟢 Normal p/ Fase",
                "mensagem_recomendacao": "Condicao normal de desenvolvimento na maturacao. Manter monitoramento para a janela de corte ideal."
            }
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
        else:
            return {
                "status_title": "🟡 Atenção",
                "mensagem_recomendacao": "Desenvolvimento intermediario. Acompanhar indices nos próximos 15 dias."
            }
