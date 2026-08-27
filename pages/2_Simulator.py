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
                   ["Irrigacao de Salvamento", "Onda de Calor / Veranico", "Periodo Chuvoso Intenso"],
                   horizontal=True)

st.markdown("<br>", unsafe_allow_html=True)
col_ctrl, col_out = st.columns([1, 1], gap="large")
payload_sim = payload_hoje.copy()

with col_ctrl:
    st.markdown('<div class="sec-header">Parametros da Simulacao</div>', unsafe_allow_html=True)
    st.caption(f"Balanco hidrico atual: **{today['balanco_hidrico_30d']:.1f} mm** · "
               f"Temperatura atual: **{today['t_mean']:.1f} °C**")
    st.markdown("<br>", unsafe_allow_html=True)

    if "Irrigacao" in cenario:
        lame    = st.slider("Lamina de Irrigacao (mm/dia)", 0, 100, 40)
        duracao = st.slider("Duracao do Programa (dias)", 1, 30, 10)
        payload_sim["precipitacao_total"]      = float(lame)
        payload_sim["balanco_hidrico_30d"]     = float(today["balanco_hidrico_30d"] + lame * duracao * 0.7)
        payload_sim["chuva_acumulada_lag_30d"] = float(today["chuva_acumulada_lag_30d"] + lame * duracao * 0.5)
        st.caption(f"Balanco projetado: {today['balanco_hidrico_30d']:.0f} → **{payload_sim['balanco_hidrico_30d']:.0f} mm**")

    elif "Calor" in cenario:
        dias_calor    = st.slider("Dias adicionais T > 35°C", 0, 20, 8)
        red_chuva_pct = st.slider("Reducao na precipitacao mensal (%)", 0, 100, 60)
        payload_sim["dias_calor_extremo_30d"] = float(today["dias_calor_extremo_30d"] + dias_calor)
        payload_sim["precipitacao_total"]     = float(today["precipitacao_total"] * (1 - red_chuva_pct / 100))
        payload_sim["balanco_hidrico_30d"]    = float(today["balanco_hidrico_30d"] - dias_calor * 4)
        payload_sim["t_mean"]                 = float(today["t_mean"] + 3.5)
        st.caption(f"T. media projetada: {today['t_mean']:.1f} → **{payload_sim['t_mean']:.1f} °C**")

    elif "Chuvoso" in cenario:
        vol_extra     = st.slider("Volume extra de chuva no mes (mm)", 0, 300, 120)
        dias_extremos = st.slider("Eventos de chuva extrema (>50mm/dia)", 0, 10, 3)
        payload_sim["precipitacao_total"]        = float(vol_extra / 30)
        payload_sim["balanco_hidrico_30d"]       = float(today["balanco_hidrico_30d"] + vol_extra * 0.6)
        payload_sim["eventos_chuva_extrema_30d"] = float(today["eventos_chuva_extrema_30d"] + dias_extremos)
        st.caption(f"Eventos extremos projetados: **{payload_sim['eventos_chuva_extrema_30d']:.0f}** no mes")

with col_out:
    st.markdown('<div class="sec-header">Projecao Pos-Intervencao</div>', unsafe_allow_html=True)
    resultado_sim = get_prediction(payload_sim)

    if resultado_sim and resultado_hoje:
        ndvi_base = resultado_hoje["ndvi_previsto"]
        ndvi_proj = resultado_sim["ndvi_previsto"]
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
        dss = calcular_dss(mes_atual, ndvi_base, ndvi_proj)
        
        if delta > 0:
            st.success(f"Intervencao benefica — melhora de {abs(delta_pct):.1f}% no vigor.")
        elif delta < 0:
            st.error(f"Cenario critico — queda de {abs(delta_pct):.1f}% no vigor.")
            
        st.info(f"**Acao Recomendada ({dss['status_title']}):**  \n{dss['mensagem_recomendacao']}")
    else:
        st.error("API offline — rode: uvicorn main:app --port 8555")
