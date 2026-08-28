"""Simulator — Página 2: Simulador de Intervenções com dados reais."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.styles import inject_css
from components.farm_config import load_config, is_configured
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction, badge_html, calcular_dss
from components.charts import ndvi_gauge
from components.header import render_sidebar, render_page_header

st.set_page_config(page_title="Simulator · SugarCane Copilot", layout="wide",
                   initial_sidebar_state="expanded", page_icon="")

inject_css()

if not is_configured():
    render_sidebar({}, None)
    st.info("Configure a localizacao da sua fazenda em Settings para usar o Simulator.")
    st.stop()

cfg = load_config()
with st.spinner("Carregando dados reais..."):
    df, today = fetch_farm_data(cfg["lat"], cfg["lon"])

payload_hoje = build_payload(today)
resultado_hoje = get_prediction(payload_hoje)

render_sidebar(today, resultado_hoje)
render_page_header("Simulator", "SIMULADOR DE INTERVENCOES · ANALISE WHAT-IF")

st.markdown(
    "<div style='color:rgba(180,230,180,.55);font-size:13px;margin-bottom:24px;'>"
    f"Baseline: dados reais de hoje ({today['date'].strftime('%d/%m/%Y') if hasattr(today.get('date', ''), 'strftime') else str(today.get('date',''))}) "
    f"em {cfg.get('farm_name','sua fazenda')}. Ajuste os parametros para projetar o impacto de uma intervencao."
    "</div>", unsafe_allow_html=True)

cenario = st.radio("Cenario de Intervencao:",
                   ["🌱 Planejamento de Plantio", "💧 Irrigacao de Salvamento", "🧪 Aplicacao de Adubacao", "🌾 Manejo de Colheita / Maturador"],
                   horizontal=True)

st.markdown("<br>", unsafe_allow_html=True)
col_ctrl, col_out = st.columns([1, 1], gap="large")
payload_sim = payload_hoje.copy()

with col_ctrl:
    st.markdown('<div class="sec-header">Parametros da Simulacao</div>', unsafe_allow_html=True)
    st.caption(f"Chuva 30d: **{today.get('chuva_acumulada_30d', 0):.1f} mm** · "
               f"GDA atual: **{today.get('GDA_mensal', 0):.1f}**")
    st.markdown("<br>", unsafe_allow_html=True)

    if "Plantio" in cenario:
        chuva_plantio = st.slider("Previsao de Chuva para a Quinzena (mm)", 0, 150, 40)
        gda_plantio   = st.slider("Previsao de GDA (Termometro de Brotacao)", 0, 200, 95)
        payload_sim["chuva_acumulada_30d"] = chuva_plantio
        payload_sim["GDA_mensal"] = gda_plantio
        
    elif "Irrigacao" in cenario:
        lame    = st.slider("Lamina de Irrigacao (mm/dia)", 0, 100, 40, help="Milimetros aplicados por dia")
        duracao = st.slider("Duracao do Programa (dias)", 1, 30, 10)
        vol_total = lame * duracao
        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + vol_total)
        st.caption(f"Chuva 30d projetada: {today.get('chuva_acumulada_30d',0):.0f} → **{payload_sim['chuva_acumulada_30d']:.0f} mm**")

    elif "Adubacao" in cenario:
        eficiencia = st.selectbox("Qualidade e Tipo do Fertilizante", ["Ureia Comum", "Ureia Protegida (Polimero)", "Nitrato (Alta Absorcao)"])
        chuva_prev = st.slider("Previsao de Chuva pos-aplicacao (mm)", 0, 150, 15)
        
        bonus_ndvi = 0
        if "Comum" in eficiencia and chuva_prev > 15:
            bonus_ndvi = 0.05
        elif "Protegida" in eficiencia:
            bonus_ndvi = 0.08
        elif "Nitrato" in eficiencia:
            bonus_ndvi = 0.12
            
        payload_sim["chuva_acumulada_30d"] = chuva_prev
        
    elif "Colheita" in cenario:
        dias_antecip = st.slider("Dias para Antecipacao de Corte / Aplicacao de Maturador", 0, 45, 15)
        # O maturador trava o crescimento vegetativo para acumular açucar.
        # Entao o NDVI vai artificialmente "cair" ou estabilizar, e a planta precisa de estresse hidrico.
        chuva_colheita = st.slider("Previsao de Chuva (Atrapalha colheita)", 0, 150, 5)
        payload_sim["chuva_acumulada_30d"] = chuva_colheita
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + (dias_antecip * 4)) # aumenta calor

with col_out:
    st.markdown('<div class="sec-header">Projecao Pos-Intervencao</div>', unsafe_allow_html=True)
    resultado_sim = get_prediction(payload_sim)

    if resultado_sim and resultado_hoje:
        ndvi_base = resultado_hoje["ndvi_previsto"]
        bonus_ndvi_val = bonus_ndvi if "Adubacao" in cenario else 0
    ndvi_proj = resultado_sim["ndvi_previsto"]
    if "Adubacao" in cenario:
        ndvi_proj = min(0.95, ndvi_proj + bonus_ndvi_val)
        delta     = ndvi_proj - ndvi_base
        delta_pct = (delta / ndvi_base * 100) if ndvi_base else 0

        gc1, gc2 = st.columns(2)
        with gc1:
            st.plotly_chart(ndvi_gauge(ndvi_base, "NDVI Atual"),
                            use_container_width=True, config={"displayModeBar": False})
            st.markdown("<div style='text-align:center;font-size:10px;color:rgba(180,230,180,.45);'>BASELINE REAL</div>",
                        unsafe_allow_html=True)
        with gc2:
            st.plotly_chart(ndvi_gauge(ndvi_proj, "NDVI Projetado"),
                            use_container_width=True, config={"displayModeBar": False})
            arrow = "▲" if delta > 0 else "▼"
            color = "#69F0AE" if delta > 0 else "#EF5350"
            st.markdown(
                f"<div style='text-align:center;color:{color};font-size:20px;font-weight:700;'>"
                f"{arrow} {abs(delta):.3f} ({abs(delta_pct):.1f}%)</div>",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        mes_atual = today["date"].month if hasattr(today.get("date", ""), "month") else 8
        dss = calcular_dss(mes_atual, ndvi_base, ndvi_proj, cenario=cenario, chuva_projetada=payload_sim["chuva_acumulada_30d"], gda_projetado=payload_sim["GDA_mensal"])
        
        if delta > 0:
            st.success(f"Intervencao benefica — melhora de {abs(delta_pct):.1f}% no vigor.")
        elif delta < 0:
            st.error(f"Cenario critico — queda de {abs(delta_pct):.1f}% no vigor.")
            
        st.info(f"**Acao Recomendada ({dss['status_title']}):**  \n{dss['mensagem_recomendacao']}")
    else:
        st.error("Erro na projecao local.")
