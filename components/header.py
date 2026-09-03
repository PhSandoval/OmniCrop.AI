"""Shared sidebar + page header renderer."""
import streamlit as st
import pandas as pd
from datetime import datetime
from components.farm_config import load_config


def render_sidebar(today: dict, resultado: dict | None) -> None:
    with st.sidebar:
        # Logo / Brand
        st.markdown("""
<div style="padding:8px 4px 20px;">
    <div style="font-size:20px;font-weight:800;color:#fff;letter-spacing:-.02em;">
        OmniCrop AI
    </div>
    <div style="font-size:10px;color:rgba(180,230,180,.5);letter-spacing:.10em;text-transform:uppercase;margin-top:2px;">
        DSS · Satellite Virtual
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")

        # Navegação links (Streamlit renders page links natively, 
        # but we add a label for context)
        st.markdown("""
<div style="font-size:10px;font-weight:700;color:rgba(105,240,174,.7);
            text-transform:uppercase;letter-spacing:.12em;margin-bottom:12px;">
    Navegação
</div>
""", unsafe_allow_html=True)

        st.page_link("app.py",                    label="Painel Geral")
        st.page_link("pages/2_Simulador.py",      label="Simulador")
        st.page_link("pages/3_Analise.py",        label="Análise")
        st.page_link("pages/4_Minha_Fazenda.py",       label="Minha Fazenda")
        st.page_link("pages/5_Configuracoes.py",         label="Configurações")
        st.page_link("pages/6_Assistente_de_Manejo.py", label="Assistente de Manejo")

        st.markdown("---")

        # Farm Switcher (Multi-Tenant)
        if 'user_farms' in st.session_state and isinstance(st.session_state['user_farms'], list) and len(st.session_state['user_farms']) > 1:
            farm_names = [f.get("farm_name", f"Fazenda {i}") for i, f in enumerate(st.session_state['user_farms'])]
            
            # Find active index
            active_idx = 0
            if 'active_farm' in st.session_state and st.session_state['active_farm']:
                active_id = st.session_state['active_farm'].get("id")
                active_idx = next((i for i, f in enumerate(st.session_state['user_farms']) if f.get("id") == active_id), 0)
                
            selected_name = st.selectbox("Mudar Fazenda", farm_names, index=active_idx)
            
            # If changed, update active farm and rerun
            if 'active_farm' in st.session_state and st.session_state['active_farm'].get("farm_name") != selected_name:
                selected_farm = next(f for f in st.session_state['user_farms'] if f.get("farm_name") == selected_name)
                st.session_state['active_farm'] = selected_farm
                st.rerun()

        # Farm status panel
        date_str = pd.to_datetime(today.get("date", "")).strftime("%d/%m/%Y") if today and today.get("date") else "—"
        ndvi_val = resultado["ndvi_previsto"] if resultado else None
        status_txt = resultado["status_vigor"] if resultado else "API Offline"

        if ndvi_val is not None:
            if ndvi_val >= 0.6:
                color, dot = "#69F0AE", "#69F0AE"
            elif ndvi_val >= 0.4:
                color, dot = "#FFD600", "#FFD600"
            else:
                color, dot = "#EF5350", "#EF5350"
        else:
            color, dot = "#888", "#888"

        cfg = load_config() or {}
        
        farm_name = cfg.get("farm_name", "Minha Fazenda")
        city_name = cfg.get("city", "Localização Desconhecida")
        status_label = status_txt.split("(")[0].strip() if (resultado and status_txt) else "Online" if resultado else "API Offline"
        
        html_str = f'''<div style="background:rgba(8,35,10,.55);border:1px solid rgba(100,220,100,.20);border-radius:12px;padding:16px;">
<div style="font-size:10px;color:rgba(180,230,180,.55);text-transform:uppercase;letter-spacing:.10em;margin-bottom:10px;">Talhão Ativo</div>
<div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:4px;">{farm_name}</div>
<div style="font-size:11px;color:rgba(180,230,180,.60);margin-bottom:12px;">{city_name}</div>
<div style="font-size:10px;color:rgba(180,230,180,.45);margin-bottom:4px;">Última leitura</div>
<div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:12px;">{date_str}</div>
<div style="display:flex;align-items:center;gap:8px;">
<div style="width:8px;height:8px;border-radius:50%;background:{dot};box-shadow:0 0 6px {dot};"></div>
<div style="font-size:11px;color:{color};font-weight:600;">{status_label}</div>
</div>
</div>'''
        st.markdown(html_str, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"v1.0 · {datetime.now().strftime('%H:%M')}")


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(f"""
<div style="display:flex;align-items:baseline;justify-content:space-between;
            margin-bottom:24px;padding-bottom:14px;
            border-bottom:1px solid rgba(105,240,174,.18);">
    <div>
        <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-.02em;">
            {title}
        </div>
        <div style="font-size:12px;color:rgba(180,230,180,.55);margin-top:3px;
                    letter-spacing:.05em;">
            {subtitle}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
