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

st.set_page_config(page_title="Settings · SugarCane Copilot", layout="wide",
                   initial_sidebar_state="expanded", page_icon="")

inject_css()

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
# COLUNA A — Localização da Fazenda
# ─────────────────────────────────────────────────────────────
with col_farm:
    st.markdown('<div class="sec-header">Localização da Fazenda</div>', unsafe_allow_html=True)

    # Busca por nome de cidade
    query = st.text_input("Buscar por nome de cidade / município",
                          placeholder="Ex: Ribeirão Preto, Piracicaba, Jaboticabal...")

    lat_val = cfg.get("lat", -21.1767)
    lon_val = cfg.get("lon", -47.8208)

    if query and len(query) >= 3:
        with st.spinner("Buscando localização..."):
            results = search_location(query)

        if results:
            labels = [r["label"] for r in results]
            escolha = st.selectbox("Selecione a localidade:", labels)
            idx = labels.index(escolha)
            lat_val = results[idx]["lat"]
            lon_val = results[idx]["lon"]
            st.caption(f"Coordenadas: {lat_val:.4f}, {lon_val:.4f}")
        else:
            st.warning("Nenhuma localidade encontrada. Tente outro nome ou insira as coordenadas manualmente.")

    st.markdown("**Ou insira as coordenadas manualmente:**")
    col_lat, col_lon = st.columns(2)
    lat_input = col_lat.number_input("Latitude", value=lat_val, format="%.4f", step=0.0001)
    lon_input = col_lon.number_input("Longitude", value=lon_val, format="%.4f", step=0.0001)

    # Mapa interativo
    st.markdown("**Localização no Mapa:**")
    map_df = pd.DataFrame({"lat": [lat_input], "lon": [lon_input]})
    st.map(map_df, zoom=9, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">Dados da Fazenda</div>', unsafe_allow_html=True)

    farm_name  = st.text_input("Nome da Fazenda / Talhão",
                               value=cfg.get("farm_name", "Minha Fazenda"))
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
        "Deficit Hidrico Critico (mm)", -200, 0,
        cfg.get("deficit_lim", -30),
        help="Balanco hidrico abaixo desse valor dispara alerta de irrigacao.")

    dias_calor_lim = st.slider(
        "Dias de Calor Extremo (limite/mes)", 0, 30,
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

with col_btn:
    if st.button("Salvar e Buscar Dados Reais", use_container_width=True):
        config = {
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
                    p3.metric("Balanco Hidrico 30d", f"{t['balanco_hidrico_30d']:.1f} mm")
                except Exception as e:
                    st.error(f"Erro ao buscar dados da API: {e}")
