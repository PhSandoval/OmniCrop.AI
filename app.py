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

st.set_page_config(page_title="OmniCrop AI - Inteligência Agronômica", page_icon="🌾", layout="wide",
                   initial_sidebar_state="expanded", page_icon="")

inject_css()

# -- CAPTURA DE CALLBACK DO SUPABASE (EMAIL CONFIRMATION PKCE) --
if 'code' in st.query_params:
    try:
        from components.db import get_supabase
        auth_code = st.query_params['code']
        # Troca o auth_code por uma sessao real
        res = get_supabase().auth.exchange_code_for_session({"auth_code": auth_code})
        st.session_state['user'] = res.user
        st.session_state['access_token'] = res.session.access_token
        
        # Salva nos cookies para não perder
        from streamlit_cookies_controller import CookieController
        controller = CookieController()
        controller.set('sb-access-token', res.session.access_token, max_age=86400*30)
        controller.set('sb-refresh-token', res.session.refresh_token, max_age=86400*30)
        
        st.query_params.clear() # Limpa a URL
        st.rerun()
    except Exception as e:
        pass
# ---------------------------------------------------------------


# 1. Controle de Estado
if 'user' not in st.session_state:
    st.session_state['user'] = None
    try:
        from streamlit_cookies_controller import CookieController
        controller = CookieController()
        access_token = controller.get('sb-access-token')
        refresh_token = controller.get('sb-refresh-token')
        
        if access_token and refresh_token:
            from components.db import get_supabase
            res = get_supabase().auth.set_session(access_token, refresh_token)
            if res and getattr(res, 'user', None):
                st.session_state['user'] = res.user
                st.session_state['access_token'] = res.session.access_token
    except Exception as e:
        pass

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
                    st.session_state['active_farm'] = cfg
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
            try:
                from streamlit_cookies_controller import CookieController
                controller = CookieController()
                controller.remove('sb-access-token')
                controller.remove('sb-refresh-token')
            except:
                pass
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
        st.markdown("📍 **Como deseja encontrar sua lavoura?**")
        tab_busca, tab_coord = st.tabs(["🏙️ Buscar por Cidade", "🧭 Inserir Coordenadas Manuais"])
        
        with tab_busca:
            busca = st.text_input("Buscar Cidade ou Município:", placeholder="Ex: Ribeirão Preto, SP", label_visibility="collapsed")
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
                    
        with tab_coord:
            c1, c2, c3 = st.columns([2, 2, 1])
            man_lat = c1.number_input("Latitude:", value=float(st.session_state['map_center'][0]), step=1e-6)
            man_lon = c2.number_input("Longitude:", value=float(st.session_state['map_center'][1]), step=1e-6)
            if c3.button("Pular para Coordenada", use_container_width=True):
                st.session_state['map_center'] = [man_lat, man_lon]
                st.session_state['clicked_lat'] = man_lat
                st.session_state['clicked_lon'] = man_lon
                st.session_state['map_zoom'] = 15
                st.rerun()
                
        import folium
        from streamlit_folium import st_folium
        
        m = folium.Map(location=st.session_state['map_center'], zoom_start=st.session_state['map_zoom'], tiles=None)
        
        # Adiciona Camada de Satelite
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite (Esri)',
            overlay=False,
            control=False
        ).add_to(m)
        
        # Adiciona Camada de Mapa Hibrido (Ruas e Nomes)
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='Ruas e Cidades (OpenStreetMap)',
            overlay=False,
            control=False
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        # Botão de GPS nativo do Folium para voar para a localização do usuário
        from folium.plugins import LocateControl
        LocateControl(auto_start=False, position="bottomright").add_to(m)
        
        clicked_lat = st.session_state.get('clicked_lat')
        clicked_lon = st.session_state.get('clicked_lon')
        
        if clicked_lat and clicked_lon:
            folium.Marker([clicked_lat, clicked_lon], tooltip="Nova Fazenda", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        
        st.markdown("<p style='font-size:14px; color:#69F0AE;'>👉 <b>DICA:</b> Clique no ícone de 'Camadas' (canto superior direito do mapa) para alternar entre <b>Satélite</b> e mapa de <b>Ruas</b>, facilitando encontrar sua fazenda.</p>", unsafe_allow_html=True)
        
        map_data = st_folium(m, height=500, use_container_width=True)
        
        if map_data and map_data.get('last_clicked'):
            new_lat = map_data['last_clicked']['lat']
            new_lon = map_data['last_clicked']['lng']
            if new_lat != clicked_lat or new_lon != clicked_lon:
                st.session_state['clicked_lat'] = new_lat
                st.session_state['clicked_lon'] = new_lon
                st.rerun()
                
        if clicked_lat and clicked_lon:
            st.success(f"📍 Ponto de Monitoramento Capturado: Latitude {clicked_lat:.6f} | Longitude {clicked_lon:.6f}")
        
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
                    r = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}", headers={"User-Agent": "OmniCropAI"})
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
                st.session_state['active_farm'] = cfg
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

    from components.pdf_generator import generate_pdf_report
    pdf_bytes = generate_pdf_report(
        cfg.get("farm_name", "Minha Fazenda"),
        cfg.get("city", "Desconhecida"),
        payload,
        resultado
    )
    st.download_button(
        label="📄 Baixar Relatório Semanal (PDF)",
        data=pdf_bytes,
        file_name=f"Relatorio_{cfg.get('farm_name', 'Fazenda')}.pdf",
        mime="application/pdf",
        type="primary"
    )
    st.markdown("<br>", unsafe_allow_html=True)


    with st.expander("🤔 Dicionário Agronômico: O que significam essas siglas?"):
        st.markdown('''
        O **OmniCrop AI** atua como um **Satélite Virtual** (um *DSS* - Sistema de Suporte à Decisão). 
        Ele utiliza Inteligência Artificial para ler o clima e prever a saúde da sua lavoura, ajudando você a tomar decisões mesmo de longe.
        
        **📖 Dicionário Leigo de Termos do Agro:**
        - **NDVI (Índice de Vigor Vegetativo):** Uma "nota de saúde" de 0 a 1 que o satélite dá para a planta. 
          * Valores altos (próximos a 1) significam cana verde, alta e crescendo saudável. 
          * Valores baixos (abaixo de 0.4) indicam que a planta está seca, estressada ou já madura e pronta para ser cortada.
        - **GDA (Graus-Dia Acumulados):** É o "relógio biológico" da planta. Mede a quantidade de calor que a cana recebeu do sol. Dias frios não geram calor útil, o que "trava" o crescimento da lavoura.
        - **Precipitação / Lâmina (mm):** É a quantidade de água da chuva ou irrigação. 1 milímetro equivale a jogar 1 litro de água espalhado em 1 metro quadrado de terra.
        - **Déficit Hídrico:** A "conta bancária" de água da fazenda. Fica no vermelho quando a planta transpira mais água do que chove.
        - **ROI (Retorno sobre Investimento):** O cálculo de quanto dinheiro uma ação (como ligar o pivô de irrigação) vai custar versus o quanto vai salvar de safra.
        ''')





    # ── KPIs ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-header">Condições do Talhão Hoje</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Temperatura Média",   f"{today['t_mean']:.1f} °C",
              f"Max {today['t_max']:.0f} / Min {today['t_min']:.0f} °C", 
              help="Média de calor do dia.\n\nPARÂMETROS:\n• Ideal: 25°C a 30°C\n• Abaixo de 20°C: Crescimento trava\n• Acima de 35°C: Estresse térmico")
    
    k2.metric("Precipitação",        f"{today['precipitacao_total']:.1f} mm", 
              help="Chuva de hoje (1mm = 1 Litro/m²).\n\nPARÂMETROS:\n• > 10mm: Chuva boa\n• > 50mm: Chuva forte (risco de atolamento para máquinas)")
    
    k3.metric("Chuva Acum. 30d", f"{today.get('chuva_acumulada_30d',0):.1f} mm", 
              help="Reserva de chuva do último mês.\n\nPARÂMETROS:\n• Ideal (Crescimento): > 120mm/mês\n• Crítico: < 50mm/mês (Déficit Hídrico)")
    
    k4.metric("Umidade do Solo",     f"{today['umidade_solo_mean']:.2f}", 
              help="Água disponível na raiz (escala 0 a 1).\n\nPARÂMETROS:\n• 0.0 a 0.2: Seca extrema\n• 0.3 a 0.6: Ideal para crescimento\n• > 0.8: Solo encharcado/alagado")
    
    k5.metric("Radiação Solar",      f"{today['radiacao_solar_mean']:.0f} W/m²", 
              help="Energia solar para fotossíntese.\n\nPARÂMETROS:\n• > 200 W/m²: Excelente\n• < 100 W/m²: Dias muito nublados (atrasam a maturação)")

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
            status_titulo = dss['status_title']
            chuva_30 = f"{today.get('chuva_acumulada_30d', 0):.1f}"
            umidade = f"{today.get('umidade_solo_mean', 0):.2f}"
            
            # Inicializa chaves de sessao se nao existirem (prefixo por talhao para isolar checkboxes)
            c_talhao = cfg.get('farm_name', 'default')
            k1, k2, k3 = f'chk_1_{c_talhao}', f'chk_2_{c_talhao}', f'chk_3_{c_talhao}'
            if k1 not in st.session_state: st.session_state[k1] = False
            if k2 not in st.session_state: st.session_state[k2] = False
            if k3 not in st.session_state: st.session_state[k3] = False
            
            # Calcula progresso
            tasks_done = sum([st.session_state[k1], st.session_state[k2], st.session_state[k3]])
            porcentagem = int((tasks_done / 3) * 100)
            
            # Renderiza barra de progresso
            st.progress(porcentagem, text=f'Progresso das Ações Diárias ({porcentagem}%)')
            if porcentagem == 100:
                st.success('✅ Todas as ações de mitigação foram validadas para este talhão hoje!')
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Renderiza 3 tarefas dependendo do contexto
            if "Pronto p/ Corte" in status_titulo or "Critico" in status_titulo:
                t1 = st.checkbox('🚜 Liberar Frente de Corte Mecanizado', key=k1)
                st.caption(f'Trafegabilidade excelente devido ao baixo acúmulo de apenas {chuva_30}mm de chuva recente.')
                
                t2 = st.checkbox('🚁 Agendar Voo de Drone Pré-Colheita', key=k2)
                st.caption('Necessário para mapear as linhas de plantio e configurar piloto automático (evita pisoteio da soqueira).')
                
                t3 = st.checkbox('🔥 Alertar Brigada de Incêndio', key=k3)
                st.caption(f'Risco crítico de fogo devido à palhada seca e umidade do solo perigosamente baixa ({umidade}).')
            else:
                t1 = st.checkbox('💧 Acionar Programa de Irrigação', key=k1)
                st.caption('Verifique o módulo Simulador para calcular a lâmina exata em milímetros que maximiza o vigor sem desperdício.')
                
                t2 = st.checkbox('🧪 Programar Adubação de Cobertura', key=k2)
                st.caption('Recomenda-se aplicar fertilizante nitrogenado antes da próxima chuva para garantir incorporação no solo e evitar volatilização.')
                
                t3 = st.checkbox('🌱 Inspecionar Pragas (Broca-da-Cana)', key=k3)
                st.caption('Fase de alto vigor vegetativo é o prato principal para pragas. Desloque um técnico para amostragem destrutiva.')

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
