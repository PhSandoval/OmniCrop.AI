"""Dashboard — Página principal com dados REAIS da Open-Meteo."""
import streamlit as st
import sys
import folium
from streamlit_folium import st_folium
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from components.styles import inject_css
from components.farm_config import load_config, is_configured, save_config
from components.live_data import fetch_farm_data, search_location
from components.api_client import build_payload, get_prediction, badge_html, calcular_dss
from components.charts import ndvi_gauge, ndvi_line, rain_bars, temp_lines
from components.header import render_sidebar, render_page_header

st.set_page_config(page_title="Dashboard · SugarCane Copilot", layout="wide",
                   initial_sidebar_state="expanded", page_icon="")

inject_css()

# 1. Controle de Estado
if 'user' not in st.session_state:
    st.session_state['user'] = None

if 'active_farm' not in st.session_state:
    st.session_state['active_farm'] = None

if 'show_onboarding' not in st.session_state:
    st.session_state['show_onboarding'] = False

if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [-21.17, -47.81]

if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 7

if 'last_busca' not in st.session_state:
    st.session_state['last_busca'] = ""

from components.auth import render_auth_page
from components.db import get_user_farms, insert_farm


# 2. Função de Onboarding

def render_farm_selector():
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Suas Fazendas</h2>", unsafe_allow_html=True)
    
    farms = get_user_farms(st.session_state['user'].id)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if farms:
            st.write("Selecione um talhão para monitorar:")
            for f in farms:
                if st.button(f"🌾 {f['farm_name']} ({f['city']})", use_container_width=True):
                    # Set active farm and override the local config
                    cfg = f.copy()
                    st.session_state['active_farm'] = True
                    st.session_state['farm_name'] = cfg['farm_name']
                    st.session_state['city'] = cfg['city']
                    
                    from components.farm_config import save_config
                    save_config(cfg) # Sync with local config so pages can read it
                    st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)
            
        st.write("Ou adicione uma nova área de manejo:")
        if st.button("➕ Cadastrar Novo Talhão", type="primary", use_container_width=True):
            st.session_state['show_onboarding'] = True
            st.rerun()
        
        st.write("")
        if st.button("🚪 Sair (Logout)", use_container_width=True):
            st.session_state['user'] = None
            st.session_state['active_farm'] = None
            st.rerun()

def render_onboarding():
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
        </style>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🌱 Mapear Novo Talhão</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(180,230,180,.8); font-size: 16px; margin-bottom: 20px;'>"
                    "Busque sua cidade e clique no mapa para marcar a localização exata da lavoura.</p>", unsafe_allow_html=True)
        
        # Smart Search
        busca = st.text_input("📍 Buscar Cidade ou Município:", placeholder="Ex: Ribeirão Preto, SP")
        if busca and busca != st.session_state.get('last_busca'):
            st.session_state['last_busca'] = busca
            from components.live_data import search_location
            pts = search_location(busca)
            if pts:
                st.session_state['map_center'] = [pts[0]['lat'], pts[0]['lon']]
                st.session_state['map_zoom'] = 12
                st.rerun()
            else:
                st.warning("Localidade não encontrada.")
                
        import folium
        from streamlit_folium import st_folium
        
        m = folium.Map(location=st.session_state['map_center'], zoom_start=st.session_state['map_zoom'])
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Botão de GPS nativo do Folium para voar para a localização do usuário
        from folium.plugins import LocateControl
        LocateControl(auto_start=False, position="bottomright").add_to(m)
        
        clicked_lat = st.session_state.get('clicked_lat')
        clicked_lon = st.session_state.get('clicked_lon')
        
        if clicked_lat and clicked_lon:
            folium.Marker([clicked_lat, clicked_lon], tooltip="Nova Fazenda", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        
        st.markdown("<p style='font-size:14px; color:#69F0AE;'>👉 <b>DICA:</b> Clique na sua lavoura para fixar um pino. Use o ícone de GPS no mapa para achar sua localização atual.</p>", unsafe_allow_html=True)
        
        map_data = st_folium(m, height=400, use_container_width=True)
        
        if map_data and map_data.get('last_clicked'):
            new_lat = map_data['last_clicked']['lat']
            new_lon = map_data['last_clicked']['lng']
            if new_lat != clicked_lat or new_lon != clicked_lon:
                st.session_state['clicked_lat'] = new_lat
                st.session_state['clicked_lon'] = new_lon
                st.rerun()
                
        if clicked_lat and clicked_lon:
            st.success(f"📍 Ponto de Monitoramento Capturado: Latitude {clicked_lat:.4f} | Longitude {clicked_lon:.4f}")
        
        col_f, col_a = st.columns([3, 1])
        fazenda = col_f.text_input("Nome do Novo Talhão:", placeholder="Ex: Talhão Sul")
        area_ha = col_a.number_input("Área (ha):", min_value=1, value=100)
        
        if st.button("Salvar Fazenda 🚀", type="primary", use_container_width=True):
            if not fazenda:
                st.error("Dê um nome para o talhão!")
            elif not clicked_lat or not clicked_lon:
                st.error("Clique no mapa para marcar o ponto exato da fazenda!")
            else:
                lat = clicked_lat
                lon = clicked_lon
                
                # Reverso para achar a cidade baseada no clique
                import requests
                try:
                    r = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}", headers={"User-Agent": "SugarCaneCopilot"})
                    city = r.json().get('address', {}).get('city', 'Fazenda')
                except:
                    city = "Local Desconhecido"
                
                cfg = {
                    "farm_name": fazenda,
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "variedade": "RB867515",
                    "area_ha": area_ha,
                    "alert_amarelo": 0.6,
                    "alert_vermelho": 0.4,
                    "chuva_critica": 30,
                    "gda_critico": 150
                }
                
                from components.farm_config import save_config
                save_config(cfg)
                st.session_state['farm_name'] = fazenda
                st.session_state['city'] = city
                
                from components.db import insert_farm
                user_id = st.session_state['user'].id
                insert_farm(user_id, fazenda, city, lat, lon)
                
                st.session_state['show_onboarding'] = False
                st.session_state['active_farm'] = True
                st.rerun()
                
        if st.button("Cancelar", use_container_width=True):
            st.session_state['show_onboarding'] = False
            st.rerun()

# 3. Função do App Principal
def render_main_app():
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




    # ── KPIs ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-header">Condições do Talhão Hoje</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Temperatura Média",   f"{today['t_mean']:.1f} °C",
              f"Max {today['t_max']:.0f} / Min {today['t_min']:.0f} °C")
    k2.metric("Precipitacao",        f"{today['precipitacao_total']:.1f} mm")
    k3.metric("Chuva Acum. 30d", f"{today.get('chuva_acumulada_30d',0):.1f} mm")
    k4.metric("Umidade do Solo",     f"{today['umidade_solo_mean']:.2f}")
    k5.metric("Radiação Solar",      f"{today['radiacao_solar_mean']:.0f} W/m²")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gauge + DSS ───────────────────────────────────────────────
    st.markdown('<div class="sec-header">Satellite Virtual · Diagnóstico IA</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="sec-header">Histórico Real · Últimos 90 Dias (Open-Meteo)</div>',
                unsafe_allow_html=True)

    hist = df.iloc[-90:]
    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown("**Temperatura (°C)**")
        st.plotly_chart(temp_lines(hist), use_container_width=True, config={"displayModeBar": False})
    with h2:
        st.markdown("**Precipitação Diária (mm)**")
        st.plotly_chart(rain_bars(hist), use_container_width=True, config={"displayModeBar": False})
    with h3:
        st.markdown("**GDA Acumulado 30d**")
        import plotly.express as px
        fig_bh = px.line(hist, x="date", y="GDA_mensal",
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

# 4. Gatilho Final
if not st.session_state['user']:
    render_auth_page()
elif st.session_state['show_onboarding']:
    render_onboarding()
elif not st.session_state['active_farm']:
    render_farm_selector()
else:
    render_main_app()
