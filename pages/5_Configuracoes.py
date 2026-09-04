import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.styles import inject_css
from components.header import render_sidebar, render_page_header
from components.farm_config import save_config, load_config
from components.db import update_farm
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction

st.set_page_config(page_title="Configurações · OmniCrop AI", page_icon="assets/logo.jpg", layout="wide", initial_sidebar_state="expanded")
inject_css()

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("Você precisa estar logado para acessar esta página.")
    st.page_link("app.py", label="Ir para Login")
    st.stop()

# Sidebar config (to show current active farm)
cfg = load_config() or {}
_today_cfg = {}
_resultado_cfg = None
if cfg:
    try:
        _, _today_cfg = fetch_farm_data(cfg["lat"], cfg["lon"])
        _payload = build_payload(_today_cfg)
        _resultado_cfg = get_prediction(_payload)
    except Exception:
        pass

render_sidebar(_today_cfg, _resultado_cfg)
render_page_header("Configurações", "PREFERÊNCIAS DO SISTEMA E MINHA CONTA")

col_pref, col_conta = st.columns([1.5, 1], gap="large")

with col_pref:
    st.markdown('<div class="sec-header">Preferências de Alertas (Sistema)</div>', unsafe_allow_html=True)
    st.write("Ajuste a sensibilidade dos alertas gerados pela Inteligência Artificial para a sua conta.")
    
    ndvi_medio_lim = st.slider("NDVI Atenção (abaixo = alerta amarelo)", 0.0, 0.8, cfg.get("alert_amarelo", 0.60), step=0.01)
    ndvi_critico_lim = st.slider("NDVI Crítico (abaixo = alerta vermelho)", 0.0, 0.6, cfg.get("alert_vermelho", 0.40), step=0.01)
    deficit_lim = st.slider("Chuva Acumulada Crítica (mm)", -200, 0, cfg.get("chuva_critica", -30))
    dias_calor_lim = st.slider("GDA Crítico (Mensal)", 0, 30, cfg.get("gda_critico", 150))
    
    st.markdown("<br>", unsafe_allow_html=True)
    receber_alertas = st.toggle("📧 Ativar Relatório Diário por E-mail (CRON)", value=cfg.get("receber_alertas", True), help="Receba um e-mail às 06:00 caso o DSS detecte risco.")
    
    if st.button("💾 Salvar Preferências", type="primary"):
        if cfg:
            update_data = {
                "alert_amarelo": ndvi_medio_lim,
                "alert_vermelho": ndvi_critico_lim,
                "chuva_critica": deficit_lim,
                "gda_critico": dias_calor_lim,
                "receber_alertas": receber_alertas
            }
            update_farm(cfg["id"], st.session_state['user'].id, update_data)
            
            cfg.update(update_data)
            st.session_state['active_farm'] = cfg
            save_config(cfg)
            st.success("Configurações de sistema salvas com sucesso!")

with col_conta:
    st.markdown('<div class="sec-header">Seu Perfil</div>', unsafe_allow_html=True)
    st.write(f"**E-mail Autenticado:**")
    st.code(st.session_state['user'].email)
    st.write(f"**Sessão:** Ativa e Segura (Supabase Auth)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sair do Sistema (Logout)", type="primary"):
        st.session_state['user'] = None
        st.session_state['active_farm'] = None
        st.session_state['access_token'] = None
        st.switch_page("app.py")
