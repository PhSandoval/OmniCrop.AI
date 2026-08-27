"""Dashboard — Página principal com dados REAIS da Open-Meteo."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from components.styles import inject_css
from components.farm_config import load_config, is_configured
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction, badge_html, calcular_dss
from components.charts import ndvi_gauge, ndvi_line, rain_bars, temp_lines
from components.header import render_sidebar, render_page_header

st.set_page_config(page_title="Dashboard · SugarCane Copilot", layout="wide",
                   initial_sidebar_state="expanded", page_icon="")

inject_css()

# ── Verificar se a fazenda está configurada ───────────────────
if not is_configured():
    render_sidebar({}, None)
    st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            min-height:60vh;text-align:center;gap:16px;">
    <div style="font-size:48px;">🌾</div>
    <div style="font-size:24px;font-weight:800;color:#fff;">Bem-vindo ao SugarCane Copilot</div>
    <div style="font-size:14px;color:rgba(180,230,180,.60);max-width:440px;line-height:1.6;">
        Configure a localizacao da sua fazenda para comecar a receber
        diagnosticos em tempo real baseados em dados climaticos reais.
    </div>
    <div style="margin-top:8px;font-size:13px;color:#69F0AE;font-weight:600;">
        Acesse Settings na barra lateral para comecar.
    </div>
</div>
""", unsafe_allow_html=True)
    st.stop()

# ── Carregar config e buscar dados reais ─────────────────────
cfg = load_config()

with st.spinner("Buscando dados reais da sua fazenda via satelite..."):
    try:
        df, today = fetch_farm_data(cfg["lat"], cfg["lon"])
    except Exception as e:
        st.warning("⚠️ Ops! A API meteorológica não está respondendo. Verifique sua conexão com a internet ou tente novamente mais tarde.")
        st.stop()

payload   = build_payload(today)
resultado = get_prediction(payload)

render_sidebar(today, resultado)
render_page_header(
    cfg.get("farm_name", "Dashboard"),
    f"MONITORAMENTO OPERACIONAL · {cfg['lat']:.4f}, {cfg['lon']:.4f} · DADOS REAIS OPEN-METEO"
)

with st.expander("🤔 O que é este sistema?"):
    st.markdown('''
    O **SugarCane Copilot** atua como um **satélite virtual**. 
    Ele utiliza o histórico climático dos últimos 90 dias (via Open-Meteo API) e um modelo de Machine Learning (XGBoost) para 
    prever o vigor vegetativo (NDVI) da sua lavoura de cana-de-açúcar, permitindo tomada de decisão até mesmo em dias nublados.
    ''')


# ── KPIs ──────────────────────────────────────────────────────
st.markdown('<div class="sec-header">Condicoes do Talhao Hoje</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Temperatura Media",   f"{today['t_mean']:.1f} °C",
          f"Max {today['t_max']:.0f} / Min {today['t_min']:.0f} °C")
k2.metric("Precipitacao",        f"{today['precipitacao_total']:.1f} mm")
k3.metric("Balanco Hidrico 30d", f"{today['balanco_hidrico_30d']:.1f} mm",
          "Deficit" if today["balanco_hidrico_30d"] < 0 else "Superavit")
k4.metric("Umidade do Solo",     f"{today['umidade_solo_mean']:.2f}")
k5.metric("Radiacao Solar",      f"{today['radiacao_solar_mean']:.0f} W/m²")

st.markdown("<br>", unsafe_allow_html=True)

# ── Gauge + DSS ───────────────────────────────────────────────
st.markdown('<div class="sec-header">Satellite Virtual · Diagnostico IA</div>', unsafe_allow_html=True)

col_g, col_d = st.columns([1, 2], gap="large")
with col_g:
    if resultado:
        st.plotly_chart(ndvi_gauge(resultado["ndvi_previsto"]),
                        use_container_width=True, config={"displayModeBar": False})
        st.markdown(badge_html(resultado["status_vigor"]), unsafe_allow_html=True)
        st.caption(f"Variedade: {cfg.get('variedade','—')} · Area: {cfg.get('area_ha','—')} ha")
    else:
        st.error("API offline — rode: uvicorn main:app --port 8555")

with col_d:
    if resultado:
        mes_atual = today["date"].month if hasattr(today.get("date", ""), "month") else 8
        dss = calcular_dss(mes_atual, resultado["ndvi_previsto"], resultado["ndvi_previsto"])
        
        for alerta in resultado["fatores_de_risco_identificados"]:
            st.warning(f"⚠️ {alerta}")
            
        st.info(f"**Plano de Acao ({dss['status_title']}):**  \n{dss['mensagem_recomendacao']}")
        
        st.markdown("**Ações Sugeridas (Checklist):**")
        st.checkbox("Enviar drone para inspecionar falhas")
        if dss['status_title'] == "🔴 Critico":
            st.checkbox("Solicitar orçamento de irrigação de salvamento")
        if dss['status_title'] in ["🟠 Alerta", "🟡 Pronto p/ Corte"]:
            st.checkbox("Avaliar compra de maturador químico")
            st.checkbox("Agendar equipe de colheita")

        st.caption("Inteligência Agronômica baseada na Matriz de Fases de Safra")

st.markdown("<br>", unsafe_allow_html=True)

# ── Histórico 90 dias (dados reais) ───────────────────────────
st.markdown('<div class="sec-header">Historico Real · Ultimos 90 Dias (Open-Meteo)</div>',
            unsafe_allow_html=True)

hist = df.iloc[-90:]
h1, h2, h3 = st.columns(3)
with h1:
    st.markdown("**Temperatura (°C)**")
    st.plotly_chart(temp_lines(hist), use_container_width=True, config={"displayModeBar": False})
with h2:
    st.markdown("**Precipitacao Diaria (mm)**")
    st.plotly_chart(rain_bars(hist), use_container_width=True, config={"displayModeBar": False})
with h3:
    st.markdown("**Balanco Hidrico 30d (mm)**")
    import plotly.express as px
    fig_bh = px.line(hist, x="date", y="balanco_hidrico_30d",
                     color_discrete_sequence=["#64B5F6"])
    fig_bh.add_hline(y=0, line=dict(color="rgba(255,255,255,.3)", dash="dash", width=1))
    fig_bh.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10),
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="rgba(180,230,180,.80)",
                         xaxis=dict(showgrid=False, tickfont=dict(size=9)),
                         yaxis=dict(showgrid=True, gridcolor="rgba(100,200,100,.10)",
                                    tickfont=dict(size=9)),
                         showlegend=False)
    st.plotly_chart(fig_bh, use_container_width=True, config={"displayModeBar": False})
