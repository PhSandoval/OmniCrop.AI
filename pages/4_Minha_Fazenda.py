import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.styles import inject_css
from components.header import render_sidebar, render_page_header
from components.db import get_user_farms, update_farm, delete_farm
from components.farm_config import save_config, load_config
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction

st.set_page_config(page_title="Minha Fazenda · OmniCrop AI", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")
inject_css()

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("A sua sessão expirou. Faça login novamente para acessar o sistema.")
    st.page_link("app.py", label="Ir para Login 🔒")
    st.stop()

# Load real data for sidebar
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
render_page_header("Minha Fazenda", "GERENCIAMENTO DE TALHÕES E DADOS AGRONÔMICOS")

user_id = st.session_state['user'].id
farms = get_user_farms(user_id)

if not farms:
    st.info("Você ainda não possui fazendas cadastradas.")
    if st.button("➕ Cadastrar Novo Talhão (Mapa)", use_container_width=True):
        st.session_state['show_onboarding'] = True
        st.switch_page("app.py")
    st.stop()

# Farm Selection for Editing
st.markdown('<div class="sec-header">Selecione um Talhão para Gerenciar</div>', unsafe_allow_html=True)
farm_names = [f["farm_name"] for f in farms]

# Find active index
active_name = cfg.get("farm_name") if cfg else farm_names[0]
if active_name not in farm_names:
    active_name = farm_names[0]
selected_name = st.selectbox("Fazenda", farm_names, index=farm_names.index(active_name))

selected_farm = next(f for f in farms if f["farm_name"] == selected_name)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-header">Informações da Fazenda</div>', unsafe_allow_html=True)
    new_name = st.text_input("Nome do Talhão", value=selected_farm.get("farm_name", ""))
    new_city = st.text_input("Cidade (Apenas para display)", value=selected_farm.get("city", ""))
    
    st.info(f"📍 **Coordenadas de Satélite:** {selected_farm.get('lat', 0):.6f}, {selected_farm.get('lon', 0):.6f}")

with col2:
    st.markdown('<div class="sec-header">Dados Agronômicos</div>', unsafe_allow_html=True)
    new_area = st.number_input("Área (hectares)", value=selected_farm.get("area_ha", 100), min_value=1)
    
    variedades = ["RB867515", "CTC9001", "SP803280", "RB966928"]
    current_var = selected_farm.get("variedade", "RB867515")
    if current_var not in variedades:
        variedades.append(current_var)
    new_var = st.selectbox("Variedade de Cana", variedades, index=variedades.index(current_var))

st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2, _ = st.columns([1.5, 1, 2])

with col_btn1:
    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
        update_data = {
            "farm_name": new_name,
            "city": new_city,
            "area_ha": new_area,
            "variedade": new_var
        }
        update_farm(selected_farm["id"], user_id, update_data)
        
        # If the edited farm is the active one, update the session and local config
        if selected_farm["id"] == cfg.get("id"):
            selected_farm.update(update_data)
            st.session_state['active_farm'] = selected_farm
            save_config(selected_farm)
            
        st.success("Alterações salvas com sucesso!")
        st.rerun()

with col_btn2:
    if st.button("🗑️ Apagar Fazenda", use_container_width=True):
        if len(farms) == 1:
            st.error("Você não pode apagar sua única fazenda.")
        else:
            delete_farm(selected_farm["id"], user_id)
            if selected_farm["id"] == cfg.get("id"):
                st.session_state['active_farm'] = None # Forces to pick another one on reload
            st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)
if st.button("➕ Adicionar Outro Talhão", use_container_width=False):
    st.session_state['show_onboarding'] = True
    st.switch_page("app.py")
