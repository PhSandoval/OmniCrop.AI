"""Settings — Página 4: Configuração da fazenda com mapa e geocodificação."""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.styles import inject_css
from components.farm_config import load_config, save_config, is_configured
from components.live_data import search_location, fetch_farm_data
from components.api_client import build_payload, get_prediction
from components.header import render_sidebar, render_page_header

st.set_page_config(page_title="Settings · Cropilot AI", layout="wide",
                   initial_sidebar_state="expanded", page_icon="")

inject_css()

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("A sua sessão expirou. Faça login novamente para acessar o sistema.")
    st.page_link("app.py", label="Ir para Login 🔒")
    st.stop()


# Carregar config salva (se existir)
cfg = load_config() or {}

# Sidebar usa dados reais se configurado
_today_cfg = {}
_resultado_cfg = None
if is_configured():
    try:
        _, _today_cfg = fetch_farm_data(cfg["lat"], cfg["lon"])
        _payload = build_payload(_today_cfg)
        _resultado_cfg = get_prediction(_payload)
    except Exception:
        pass

render_sidebar(_today_cfg, _resultado_cfg)
render_page_header("Settings", "CONFIGURAÇÃO DA FAZENDA E LIMIARES DE ALERTA")

col_farm, col_thresholds = st.columns([1, 1], gap="large")

# ─────────────────────────────────────────────────────────────
# COLUNA A — Dados Operacionais
# ─────────────────────────────────────────────────────────────
with col_farm:
    st.markdown('<div class="sec-header">Talhão Ativo</div>', unsafe_allow_html=True)
    
    farm_name = cfg.get("farm_name", "Minha Fazenda")
    city = cfg.get("city", "Cidade")
    lat_input = cfg.get("lat", -21.1767)
    lon_input = cfg.get("lon", -47.8208)
    
    st.info(f"📍 **{farm_name}** ({city})\n\nAs coordenadas de satélite ({lat_input:.4f}, {lon_input:.4f}) são gerenciadas na aba **Minha Conta**.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">Dados Agronômicos</div>', unsafe_allow_html=True)
    area_ha    = st.number_input("Área (hectares)", value=cfg.get("area_ha", 100), min_value=1)
    variedade  = st.selectbox("Variedade de Cana",
                              ["RB867515", "CTC9001", "SP803280", "RB966928"],
                              index=["RB867515", "CTC9001", "SP803280", "RB966928"].index(
                                  cfg.get("variedade", "RB867515")))

# ─────────────────────────────────────────────────────────────
# COLUNA B — Limiares de Alerta
# ─────────────────────────────────────────────────────────────
with col_thresholds:
    st.markdown('<div class="sec-header">Limiares de Alerta</div>', unsafe_allow_html=True)

    ndvi_medio_lim = st.slider(
        "NDVI Atencao (abaixo = alerta amarelo)", 0.0, 0.8,
        cfg.get("ndvi_medio_lim", 0.60), step=0.01)

    ndvi_critico_lim = st.slider(
        "NDVI Critico (abaixo = alerta vermelho)", 0.0, 0.6,
        cfg.get("ndvi_critico_lim", 0.40), step=0.01)

    deficit_lim = st.slider(
        "Chuva Acumulada Critica (mm)", -200, 0,
        cfg.get("deficit_lim", -30),
        help="Balanco hidrico abaixo desse valor dispara alerta de irrigacao.")

    dias_calor_lim = st.slider(
        "GDA Critico (Mensal)", 0, 30,
        cfg.get("dias_calor_lim", 5),
        help="Acima desse numero de dias com T > 35 graus, alerta termico.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">Resumo da Configuracao</div>', unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("NDVI Atencao",   f"{ndvi_medio_lim:.2f}")
    m2.metric("NDVI Critico",   f"{ndvi_critico_lim:.2f}")
    m3.metric("Deficit Limite", f"{deficit_lim} mm")

# ─────────────────────────────────────────────────────────────
# SALVAR E BUSCAR DADOS
# ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_btn, col_status = st.columns([1, 2])

st.markdown("<br>", unsafe_allow_html=True)
receber_alertas = st.toggle("Ativar Relatório Diário por E-mail (CRON)", value=cfg.get("receber_alertas", True), help="Receba um e-mail às 06:00 caso o DSS detecte risco na operação (Ex: Alagamento).")
st.markdown("<br>", unsafe_allow_html=True)

with col_btn:
    if st.button("Salvar e Buscar Dados Reais", use_container_width=True):
        config = {
            "receber_alertas": receber_alertas,
            "lat": lat_input,
            "lon": lon_input,
            "farm_name": farm_name,
            "area_ha": area_ha,
            "variedade": variedade,
            "ndvi_medio_lim": ndvi_medio_lim,
            "ndvi_critico_lim": ndvi_critico_lim,
            "deficit_lim": deficit_lim,
            "dias_calor_lim": dias_calor_lim,
        }
        save_config(config)

        with col_status:
            with st.spinner(f"Buscando 92 dias de dados reais para {lat_input:.4f}, {lon_input:.4f}..."):
                try:
                    # Força o recarregamento limpando o cache
                    fetch_farm_data.clear()
                    df_live, today_live = fetch_farm_data(lat_input, lon_input)
                    st.success(
                        f"Dados reais carregados! "
                        f"{len(df_live)} dias de {df_live['date'].min().strftime('%d/%m/%Y')} "
                        f"ate {df_live['date'].max().strftime('%d/%m/%Y')}. "
                        f"Acesse o Dashboard para ver o diagnostico."
                    )
                    # Exibir preview do dia mais recente
                    t = today_live
                    st.markdown("**Preview — Dados de Hoje:**")
                    p1, p2, p3 = st.columns(3)
                    p1.metric("Temperatura", f"{t['t_mean']:.1f} °C")
                    p2.metric("Precipitacao", f"{t['precipitacao_total']:.1f} mm")
                    p3.metric("Chuva Acum. 30d", f"{t.get('chuva_acumulada_30d',0):.1f} mm")
                except Exception as e:
                    st.error(f"Erro ao buscar dados da API: {e}")
