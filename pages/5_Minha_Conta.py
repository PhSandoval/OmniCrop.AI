import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.styles import inject_css
from components.header import render_sidebar, render_page_header
from components.db import get_user_farms
from components.farm_config import load_config, save_config
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction

st.set_page_config(page_title="Minha Conta · SugarCane Copilot", layout="wide",
                   initial_sidebar_state="expanded")

inject_css()

# -- LIMPEZA FORCADA --
if not st.session_state.get('cleaned_up_nova_fazenda_forced'):
    try:
        from components.db import delete_farm, get_user_farms
        _farms = get_user_farms(st.session_state['user'].id)
        for _f in _farms:
            if _f.get("farm_name") == "Nova Fazenda":
                delete_farm(_f["id"], st.session_state['user'].id)
                # If the deleted farm is the active one, clear the active state
                if st.session_state.get('active_farm', {}).get('id') == _f['id']:
                    st.session_state['active_farm'] = None
        st.session_state['cleaned_up_nova_fazenda_forced'] = True
        st.rerun()
    except Exception as e:
        print("Erro limpando:", e)
# ---------------------


if 'user' not in st.session_state or not st.session_state['user']:
    st.info("Você precisa estar logado para acessar esta página.")
    st.page_link("app.py", label="Ir para Login")
    st.stop()

# Sidebar config (to show current active farm)
cfg = load_config() or {}
_today_cfg = {}
_resultado_cfg = None
if 'active_farm' in st.session_state and st.session_state['active_farm']:
    try:
        _, _today_cfg = fetch_farm_data(cfg["lat"], cfg["lon"])
        _payload = build_payload(_today_cfg)
        _resultado_cfg = get_prediction(_payload)
    except Exception:
        pass

render_sidebar(_today_cfg, _resultado_cfg)
render_page_header("Minha Conta", "GERENCIAMENTO DE PERFIL E TALHÕES")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-header">Seu Perfil</div>', unsafe_allow_html=True)
    st.write(f"**E-mail Autenticado:** {st.session_state['user'].email}")
    st.write(f"**Sessão:** Ativa e Segura (Supabase Auth)")
    st.write("")
    if st.button("🚪 Sair do Sistema (Logout)", type="primary"):
        st.session_state['user'] = None
        st.session_state['active_farm'] = None
        st.session_state['access_token'] = None
        st.switch_page("app.py")

with col2:
    st.markdown('<div class="sec-header">Seus Talhões / Fazendas</div>', unsafe_allow_html=True)
    
    farms = get_user_farms(st.session_state['user'].id)
    if farms:
        st.write("Selecione um talhão para tornar ativo no painel:")
        for f in farms:
            is_active = (f['farm_name'] == st.session_state.get('farm_name'))
            btn_text = f"✅ {f['farm_name']} ({f['city']})" if is_active else f"🌾 {f['farm_name']} ({f['city']})"
            
            if st.button(btn_text, use_container_width=True, disabled=is_active):
                st.session_state['active_farm'] = True
                st.session_state['farm_name'] = f['farm_name']
                st.session_state['city'] = f['city']
                save_config(f)
                st.rerun()
    else:
        st.info("Você ainda não possui fazendas cadastradas.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.write("Deseja adicionar uma nova área de manejo com o satélite?")
    if st.button("➕ Cadastrar Novo Talhão (Mapa)", use_container_width=True):
        st.session_state['show_onboarding'] = True
        st.switch_page("app.py")

