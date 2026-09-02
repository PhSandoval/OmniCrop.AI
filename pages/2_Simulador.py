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

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("A sua sessão expirou. Faça login novamente para acessar o sistema.")
    st.page_link("app.py", label="Ir para Login 🔒")
    st.stop()


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
render_page_header("Simulator", "SIMULADOR DE INTERVENÇÕES · ANÁLISE WHAT-IF")

st.markdown(
    "<div style='color:rgba(180,230,180,.55);font-size:13px;margin-bottom:24px;'>"
    f"Baseline: dados reais de hoje ({today['date'].strftime('%d/%m/%Y') if hasattr(today.get('date', ''), 'strftime') else str(today.get('date',''))}) "
    f"em {cfg.get('farm_name','sua fazenda')}. Ajuste os parâmetros para projetar o impacto de uma intervenção."
    "</div>", unsafe_allow_html=True)

cenario = st.radio("Cenário de Intervenção:",
                   ["Planejamento de Plantio", "Irrigação de Salvamento", "Aplicação de Adubação", "Manejo de Colheita / Maturador"],
                   horizontal=True)

st.markdown("<br>", unsafe_allow_html=True)
col_ctrl, col_out = st.columns([1, 1], gap="large")
payload_sim = payload_hoje.copy()

with col_ctrl:
    st.markdown('<div class="sec-header">Parâmetros da Simulação</div>', unsafe_allow_html=True)
    st.caption(f"Chuva 30d: **{today.get('chuva_acumulada_30d', 0):.1f} mm** · "
               f"GDA atual: **{today.get('GDA_mensal', 0):.1f}**")
    st.markdown("<br>", unsafe_allow_html=True)

    if "Plantio" in cenario:
        chuva_plantio = st.slider(f"Previsão de Chuva para a Quinzena (Atual Real: {today.get('chuva_acumulada_30d',0):.1f} mm)", 0, 150, 40, format="%d mm")
        gda_plantio   = st.slider(f"Previsão de GDA (Atual Real: {today.get('GDA_mensal',0):.1f} GDA)", 0, 200, 95, format="%d GDA")
        payload_sim["chuva_acumulada_30d"] = chuva_plantio
        payload_sim["GDA_mensal"] = gda_plantio
        
    elif "Irrigação" in cenario:
        lame    = st.slider("Lâmina de Irrigação Adicional", 0, 100, 40, format="%d mm/dia", help="Milimetros de água aplicados no campo por dia")
        duracao = st.slider("Duração do Programa", 1, 30, 10, format="%d dias")
        vol_total = lame * duracao
        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + vol_total)
        st.caption(f"Chuva 30d projetada: {today.get('chuva_acumulada_30d',0):.0f} → **{payload_sim['chuva_acumulada_30d']:.0f} mm**")
        
        custo_por_mm_ha = 5.00
        custo_total = lame * duracao * custo_por_mm_ha
        st.caption(f'Custo Estimado de Energia/Bombeamento: **R$ {custo_total:,.2f} / hectare**')

    elif "Adubação" in cenario:
        eficiencia = st.selectbox("Qualidade e Tipo do Fertilizante", ["Ureia Comum", "Ureia Protegida (Polimero)", "Nitrato (Alta Absorção)"])
        chuva_prev = st.slider(f"Previsão de Chuva Pós-Aplicação (Atual Real: {today.get('chuva_acumulada_30d',0):.1f} mm)", 0, 150, 15, format="%d mm")
        
        bonus_ndvi = 0
        if "Comum" in eficiencia and chuva_prev > 15:
            bonus_ndvi = 0.05
        elif "Protegida" in eficiencia:
            bonus_ndvi = 0.08
        elif "Nitrato" in eficiencia:
            bonus_ndvi = 0.12
            
        payload_sim["chuva_acumulada_30d"] = chuva_prev
        
    elif "Colheita" in cenario:
        dias_antecip = st.slider("Dias para Antecipação de Corte / Aplicação de Maturador", 0, 45, 15, format="%d dias")
        # O maturador trava o crescimento vegetativo para acumular açucar.
        # Entao o NDVI vai artificialmente "cair" ou estabilizar, e a planta precisa de estresse hidrico.
        chuva_colheita = st.slider(f"Previsão de Chuva Acumulada (Atual Real: {today.get('chuva_acumulada_30d',0):.1f} mm)", 0, 150, 5, format="%d mm")
        payload_sim["chuva_acumulada_30d"] = chuva_colheita
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + (dias_antecip * 4)) # aumenta calor

with col_out:
    st.markdown('<div class="sec-header">Projeção Pós-Intervenção</div>', unsafe_allow_html=True)
    resultado_sim = get_prediction(payload_sim)

    if resultado_sim and resultado_hoje:
        ndvi_base = resultado_hoje["ndvi_previsto"]
        ndvi_proj = resultado_sim["ndvi_previsto"]
        
        bonus_ndvi_val = 0
        if "Adubação" in cenario:
            # We assume bonus_ndvi was defined in the Adubação block
            try:
                bonus_ndvi_val = bonus_ndvi
            except NameError:
                bonus_ndvi_val = 0
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
            st.success(f"Intervenção benéfica — melhora de {abs(delta_pct):.1f}% no vigor.")
        elif delta < 0:
            st.error(f"Cenário crítico — queda de {abs(delta_pct):.1f}% no vigor.")
            
        st.info(f"**Ação Recomendada ({dss['status_title']}):**  \n{dss['mensagem_recomendacao']}")
        
        if "Irrigação" in cenario and payload_sim["chuva_acumulada_30d"] > 250:
            st.error("⚠️ **Risco de Alagamento (Waterlogging)**: Volume excessivo de água pode causar sufocamento radicular e queda brusca de vigor.")
    else:
        st.error("Erro na projeção local.")
