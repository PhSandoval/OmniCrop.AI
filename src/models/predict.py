"""FastAPI client + data loading helpers."""
import requests
import pandas as pd
from pathlib import Path
import streamlit as st

API_URL = "http://localhost:8555/predict_ndvi"

FEATURE_KEYS = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']


def build_payload(row: dict) -> dict:
    return {k: float(row[k]) for k in FEATURE_KEYS}


import joblib
from src.core.crop_config import get_crop_parameters, normalize_crop_id, CROP_REGISTRY

@st.cache_resource
def load_model(crop_id: str = "sugarcane"):
    """
    Carrega dinamicamente o modelo de Machine Learning treinado para a cultura especificada.
    Se a cultura estiver em fase de treino ou não possuir modelo serializado, levanta NotImplementedError explicativo.
    """
    canon_id = normalize_crop_id(crop_id)
    if canon_id not in CROP_REGISTRY:
        raise NotImplementedError(
            f"O modelo preditivo para a cultura '{crop_id}' está em fase de treino e calibração de dados."
        )

    crop_params = CROP_REGISTRY[canon_id]
    clean_id = crop_params.crop_id

    # Monta o caminho do modelo dinamicamente: models/{crop_id}_ndvi.pkl ou fallback ndvi_model.pkl
    models_dir = Path(__file__).resolve().parent
    specific_path = models_dir / f"{clean_id}_ndvi.pkl"
    default_path = models_dir / "ndvi_model.pkl"

    if specific_path.exists():
        model_path = specific_path
    elif clean_id == "sugarcane" and default_path.exists():
        model_path = default_path
    else:
        # Cultura ainda sem modelo treinado em disco
        raise NotImplementedError(
            f"O modelo preditivo para a cultura '{crop_params.name}' ({clean_id}) está em fase de treino e calibração de dados."
        )

    return joblib.load(model_path)

def get_prediction(payload: dict, crop_id: str = "sugarcane") -> dict | None:
    crop_params = get_crop_parameters(crop_id)
    clean_id = crop_params.crop_id
    try:
        model = load_model(crop_id=crop_id)
        # Convert dictionary to DataFrame for sklearn prediction (keeping feature order)
        df_input = pd.DataFrame([payload], columns=FEATURE_KEYS)
        pred = model.predict(df_input)[0]

        # Configurações fenológicas e de alertas biofísicos específicas por cultura
        crop_phenology = {
            "sugarcane": ("Desenvolvimento Vegetativo / Maturação", 30.0, "MAE 0.02"),
            "soybean": ("Enchimento de Grãos (R5-R6) / Maturação", 45.0, "MAE 0.05"),
            "corn": ("Pendoamento / Enchimento de Grãos (VT-R3)", 50.0, "MAE 0.10"),
            "coffee": ("Florada / Granação dos Frutos", 40.0, "MAE 0.025"),
            "pasture": ("Rebrote Estival / Manejo de Pastagem", 25.0, "MAE 0.024"),
        }
        fase_nome, limiar_chuva_30d, mae_hist = crop_phenology.get(
            clean_id, ("Ciclo Vegetativo", 30.0, "MAE 0.03")
        )

        alertas = []
        c30 = payload.get("chuva_acumulada_30d", 0.0)
        if c30 < limiar_chuva_30d:
            alertas.append(f"ALERTA HÍDRICO: Déficit hídrico agudo detectado nos últimos 30 dias ({c30:.1f}mm < {limiar_chuva_30d}mm) para {crop_params.name}.")

        return {
            "ndvi_previsto": round(float(pred), 3),
            "status_vigor": "Vigor Médio/Alto" if pred >= 0.50 else "Vigor Sob Atenção",
            "fatores_de_risco_identificados": alertas,
            "plano_de_acao": "", # O DSS cuida disso
            "confiabilidade_modelo": f"Alta (Margem Histórica {mae_hist})",
            "fase_fenologica": fase_nome,
            "crop_id": clean_id,
            "crop_name": crop_params.name,
        }
    except NotImplementedError as nie:
        # Alerta amigável para culturas em treinamento
        try:
            st.warning(f"ℹ️ {nie}")
        except Exception:
            pass
        return {
            "ndvi_previsto": 0.0,
            "status_vigor": "Em Treinamento",
            "status_geral": f"Modelo {crop_params.name} em Treinamento",
            "fatores_de_risco_identificados": [str(nie)],
            "plano_de_acao": "Aguardando conclusão do pipeline de treino e coleta de satélite.",
            "confiabilidade_modelo": "Em Treinamento",
            "fase_fenologica": "Calibração de Dados",
            "aviso": str(nie),
        }
    except Exception as e:
        try:
            st.error(f"Prediction Error: {e}")
        except Exception:
            pass
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
    
    if "Maturador" in cenario:
        if chuva_projetada > 80:
            return {
                "status_title": "🔴 Desperdício de Produto",
                "mensagem_recomendacao": "A alta previsão de chuvas pode lavar o produto das folhas logo após a aplicação aérea. Além disso, a umidade forçará o crescimento vegetativo da planta contra a ação do maturador."
            }
        elif delta < 0:
            return {
                "status_title": "🟢 Aplicação Ideal",
                "mensagem_recomendacao": "A simulação prevê queda do vigor (secagem da folha). Condição climática favorável para o produto inibir o crescimento e maximizar a conversão em sacarose (ATR)."
            }
        else:
            return {
                "status_title": "🟡 Dose Insuficiente",
                "mensagem_recomendacao": "O clima atual está estimulando muito o crescimento da planta. A dose de maturador testada não foi forte o suficiente para reverter o vigor. Aumente a dose ou aguarde o tempo secar."
            }

    if "Colheita" in cenario:
        if chuva_projetada > 50:
            return {
                "status_title": "🔴 Risco Operacional",
                "mensagem_recomendacao": "Alerta: Previsão de chuva forte (mais de 50mm). Risco altíssimo de atolamento das colhedoras, transbordos e pisoteio de soqueira (destruição da próxima safra). Interromper operações de corte!"
            }
        elif gda_projetado > 100 and chuva_projetada < 20:
            return {
                "status_title": "🟢 Corte Liberado",
                "mensagem_recomendacao": "Cenário ideal. GDA alto para a maturação final e solo completamente seco garantindo excelente trafegabilidade das máquinas."
            }
        else:
            return {
                "status_title": "🟡 Janela Aceitável",
                "mensagem_recomendacao": "Condição razoável. Monitore o mapa de chuvas na véspera para não correr risco de atolar frotas no talhão."
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


FEATURE_LABELS = {
    "chuva_acumulada_30d": "Chuva Recente (30d)",
    "chuva_acumulada_60d": "Chuva Médio Prazo (60d)",
    "chuva_acumulada_90d": "Chuva Longo Prazo (90d)",
    "GDA_mensal": "Soma Térmica (GDA)"
}


def explain_prediction_delta(payload_base: dict, payload_sim: dict, model=None, crop_id: str = "sugarcane") -> dict:
    """
    Explicabilidade de IA (XAI):
    Decompõe a contribuição marginal de cada variável climática e agronômica
    na variação do índice NDVI entre o baseline real e o cenário simulado.
    """
    if model is None:
        try:
            model = load_model(crop_id=crop_id)
        except NotImplementedError as nie:
            return {
                "pred_base": 0.0,
                "pred_sim": 0.0,
                "total_delta": 0.0,
                "contributions": {},
                "top_driver": "Em Treinamento",
                "narrativa": str(nie),
            }

    df_base = pd.DataFrame([payload_base], columns=FEATURE_KEYS)
    df_sim = pd.DataFrame([payload_sim], columns=FEATURE_KEYS)

    pred_base = float(model.predict(df_base)[0])
    pred_sim = float(model.predict(df_sim)[0])
    total_delta = pred_sim - pred_base

    contributions = {}
    for k in FEATURE_KEYS:
        df_temp = df_base.copy()
        df_temp[k] = df_sim[k]
        pred_temp = float(model.predict(df_temp)[0])
        impact = pred_temp - pred_base
        contributions[FEATURE_LABELS.get(k, k)] = round(impact, 4)

    abs_sorted = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
    top_driver, top_val = abs_sorted[0]

    if abs(total_delta) < 0.001:
        narrativa = "Os parâmetros simulados mantiveram o vigor vegetativo estável em relação ao baseline."
    else:
        direcao = "elevação" if total_delta > 0 else "queda"
        impacto_tipo = "positivo" if top_val > 0 else "negativo"
        narrativa = (
            f"A {direcao} no vigor projetado ({total_delta:+.3f} NDVI) foi impulsionada principalmente por "
            f"'{top_driver}', gerando um impacto {impacto_tipo} de {top_val:+.4f}."
        )

    return {
        "pred_base": round(pred_base, 3),
        "pred_sim": round(pred_sim, 3),
        "total_delta": round(total_delta, 4),
        "contributions": contributions,
        "top_driver": top_driver,
        "narrativa": narrativa
    }


def plot_xai_waterfall(explanation: dict):
    """
    Gera gráfico interativo de decomposição (Waterfall) usando Plotly
    para explicar a decisão do algoritmo de forma intuitiva.
    """
    import plotly.graph_objects as go

    contributions = explanation["contributions"]
    x = ["Baseline"] + list(contributions.keys()) + ["Projetado"]
    y = [explanation["pred_base"]] + list(contributions.values()) + [explanation["pred_sim"]]
    measure = ["absolute"] + ["relative"] * len(contributions) + ["total"]

    fig = go.Figure(go.Waterfall(
        name="Impacto XAI",
        orientation="v",
        measure=measure,
        x=x,
        textposition="outside",
        text=[f"{v:+.3f}" if m == "relative" else f"{v:.3f}" for v, m in zip(y, measure)],
        y=y,
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        decreasing={"marker": {"color": "#EF5350"}},
        increasing={"marker": {"color": "#69F0AE"}},
        totals={"marker": {"color": "#4FC3F7"}}
    ))
    fig.update_layout(
        title="Decomposição do Impacto no Vigor (XAI Waterfall)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=320,
        margin=dict(t=30, b=20, l=10, r=10),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    )
    return fig

