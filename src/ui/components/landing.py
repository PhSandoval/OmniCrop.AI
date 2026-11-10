import streamlit as st
from pathlib import Path

def render_landing_page():
    # Configurar paths
    base_dir = Path(__file__).resolve().parents[1] # points to frontend
    logo_path = str(base_dir / "assets" / "logo.png")

    # Estilos CSS dos cards
    st.markdown("""
    <style>
    .landing-hero {
        text-align: center;
        padding: 40px 30px;
        background: rgba(10, 25, 15, 0.55);
        border: 1px solid rgba(105, 240, 174, 0.15);
        border-radius: 24px;
        backdrop-filter: blur(10px);
        margin-top: 20px;
        margin-bottom: 40px;
    }
    .feature-card {
        background: rgba(8, 20, 12, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        height: 100%;
        backdrop-filter: blur(8px);
        transition: transform 0.2s;
    }
    .feature-card:hover {
        border-color: rgba(16, 185, 129, 0.4);
        transform: translateY(-2px);
    }
    .feature-icon {
        font-size: 32px;
        margin-bottom: 16px;
    }
    .feature-title {
        font-size: 18px;
        font-weight: 700;
        color: #fff;
        margin-bottom: 12px;
    }
    .feature-text {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.65);
        line-height: 1.6;
    }
    
    /* Leitura de textos soltos e caixas de alerta sobre a imagem */
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
        text-shadow: 0px 2px 10px rgba(0,0,0,0.9), 0px 4px 20px rgba(0,0,0,0.7) !important;
        font-weight: 600;
    }
    [data-testid="stAlert"] {
        background: rgba(8, 20, 12, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    [data-testid="stAlert"] * {
        color: #ffffff !important;
        text-shadow: none !important;
    }
    
    .glass-label {
        background: rgba(10, 26, 16, 0.65) !important;
        border: 1px solid rgba(105, 240, 174, 0.25) !important;
        border-radius: 14px;
        padding: 12px 24px;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        display: inline-block;
    }

    /* Glassmorphism Expander (Validação Científica) */
    div[data-testid="stExpander"] {
        background: rgba(8, 24, 15, 0.58) !important;
        border: 1px solid rgba(105, 240, 174, 0.25) !important;
        border-radius: 18px !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        box-shadow: 0 10px 32px 0 rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.12) !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="stExpander"]:hover {
        border-color: rgba(105, 240, 174, 0.45) !important;
        box-shadow: 0 14px 42px 0 rgba(0, 0, 0, 0.55), inset 0 1px 2px rgba(105, 240, 174, 0.2) !important;
    }

    div[data-testid="stExpander"] summary {
        background: rgba(12, 34, 20, 0.70) !important;
        border-bottom: 1px solid rgba(105, 240, 174, 0.15) !important;
        padding: 18px 22px !important;
        font-weight: 700 !important;
        font-size: 15.5px !important;
        color: #ffffff !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        transition: background 0.2s ease, color 0.2s ease !important;
        cursor: pointer !important;
    }

    div[data-testid="stExpander"] summary:hover {
        background: rgba(18, 48, 28, 0.85) !important;
        color: #69F0AE !important;
    }

    div[data-testid="stExpander"] summary svg {
        fill: #69F0AE !important;
        color: #69F0AE !important;
    }

    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        padding: 24px 22px !important;
        background: transparent !important;
    }

    /* Glassmorphism Metrics Cards */
    div[data-testid="stExpander"] div[data-testid="stMetric"] {
        background: rgba(10, 28, 18, 0.60) !important;
        border: 1px solid rgba(105, 240, 174, 0.18) !important;
        border-radius: 14px !important;
        padding: 18px 14px !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        transition: all 0.25s ease !important;
    }

    div[data-testid="stExpander"] div[data-testid="stMetric"]:hover {
        border-color: rgba(105, 240, 174, 0.50) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5), 0 0 14px rgba(16, 185, 129, 0.25) !important;
    }

    div[data-testid="stExpander"] div[data-testid="stMetric"] label {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }

    div[data-testid="stExpander"] div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 26px !important;
        text-shadow: 0 0 18px rgba(105, 240, 174, 0.4) !important;
    }

    div[data-testid="stExpander"] div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        color: #69F0AE !important;
        font-weight: 600 !important;
        font-size: 12.5px !important;
    }

    /* Glassmorphism Crop Cards */
    .glass-crop-card {
        background: rgba(10, 28, 18, 0.60) !important;
        border: 1px solid rgba(105, 240, 174, 0.22) !important;
        border-radius: 14px !important;
        padding: 14px 10px !important;
        text-align: center !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
        transition: all 0.25s ease !important;
    }

    .glass-crop-card:hover {
        border-color: rgba(105, 240, 174, 0.5) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(16, 185, 129, 0.25) !important;
    }

    /* Glassmorphism Methodology Card */
    .glass-methodology-card {
        background: rgba(8, 22, 14, 0.65) !important;
        padding: 20px 24px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(105, 240, 174, 0.22) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }

    /* Estilos Premium dos Botões da Landing */
    div[data-testid="stButton"] button {
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 15.5px !important;
        min-height: 52px !important;
        padding: 10px 22px !important;
        white-space: nowrap !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
    }
    
    div[data-testid="stButton"] button p {
        font-size: 15.5px !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        margin: 0 !important;
        text-shadow: none !important;
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: 1px solid rgba(105, 240, 174, 0.45) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35) !important;
    }

    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        border-color: #69f0ae !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.55) !important;
    }

    div[data-testid="stButton"] button[kind="secondary"],
    div[data-testid="stButton"] button:not([kind="primary"]) {
        background: rgba(10, 25, 15, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        color: #f8fafc !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover,
    div[data-testid="stButton"] button:not([kind="primary"]):hover {
        background: rgba(18, 42, 26, 0.90) !important;
        border-color: rgba(105, 240, 174, 0.5) !important;
        color: #69f0ae !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _has_dashboard = bool(('user' in st.session_state and st.session_state['user']) or (st.session_state.get('is_guest') and st.session_state.get('active_farm')))

    # 1.5 Navbar no Topo (Logo na esquerda, Botão na direita)
    col_nav_logo, _, col_nav_btn = st.columns([1.2, 3.2, 2.6])
    with col_nav_logo:
        st.image(logo_path, width=80)
    with col_nav_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if _has_dashboard:
            if st.button("Painel", use_container_width=True):
                st.session_state['show_landing'] = False
                st.rerun()
        else:
            nav_col1, nav_col2 = st.columns([1.1, 0.9], gap="small")
            with nav_col1:
                if st.button("Experimentar", use_container_width=True, type="primary", key="nav_guest"):
                    st.session_state['show_guest_onboarding'] = True
                    st.session_state['show_landing'] = False
                    st.rerun()
            with nav_col2:
                if st.button("Entrar", use_container_width=True, key="nav_login"):
                    st.session_state['show_login'] = True
                    st.session_state['show_landing'] = False
                    st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 2. O Centro da Tela (Logo e Textos)
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        # Centralizar a logo usando colunas aninhadas
        _, col_logo, _ = st.columns([1, 1, 1])
        with col_logo:
            st.image(logo_path, width=432)
            
        st.markdown("""
        <div class="landing-hero">
            <h1 style='text-align: center; color: white; font-size: 56px; font-weight: 800; letter-spacing: -0.02em; margin-top: 0px;'>OmniCrop AI</h1>
            <h3 style='text-align: center; color: #10b981; font-size: 22px; font-weight: 400; margin-bottom: 24px;'>
                O seu Satélite Virtual e Assistente Agronômico.
            </h3>
            <p style='text-align: center; color: rgba(255,255,255,0.7); font-size: 16px; line-height: 1.6; margin-bottom: 0px;'>
                Não dependa de dias ensolarados para saber a saúde da sua lavoura. O OmniCrop AI cruza dados de clima em tempo real para dizer exatamente como estão as suas plantas hoje. Descubra o risco de estresse hídrico, a janela ideal de colheita e receba planos de ação automáticos para evitar perdas na safra, tudo em um painel simples e direto.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if _has_dashboard:
            _, col_btn_dash, _ = st.columns([1, 2, 1])
            with col_btn_dash:
                if st.button("Ir para o Dashboard", use_container_width=True, type="primary"):
                    st.session_state['show_landing'] = False
                    st.rerun()
        else:
            col_b1, col_b2 = st.columns([1.15, 1.0], gap="medium")
            with col_b1:
                if st.button("Experimentar Grátis", use_container_width=True, type="primary", key="hero_guest"):
                    st.session_state['show_guest_onboarding'] = True
                    st.session_state['show_landing'] = False
                    st.rerun()
            with col_b2:
                if st.button("Já sou cliente / Entrar", use_container_width=True, key="hero_login"):
                    st.session_state['show_login'] = True
                    st.session_state['show_landing'] = False
                    st.rerun()

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # 3. Features Grid (Cards Inferiores - Mantidos Intactos)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛰️</div>
            <div class="feature-title">Satélite Virtual (Gradient Boosting)</div>
            <div class="feature-text">
                Não dependa de dias sem nuvens. Nosso motor de Machine Learning infere 
                o Índice de Vegetação (NDVI) usando cruzamento de dados térmicos e hídricos 
                em tempo real.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌦️</div>
            <div class="feature-title">Clima e DSS Integrado</div>
            <div class="feature-text">
                Monitoramento automático de Graus-Dia Acumulados (GDA) e estresse hídrico. 
                Tome decisões baseadas em dados sobre a janela ideal de colheita e plantio.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">Agrônomo GenAI (RAG)</div>
            <div class="feature-text">
                Um assistente inteligente alimentado pelo Google Gemini 3.6, que conhece 
                o clima e a umidade exata da sua fazenda para responder dúvidas técnicas 24/7.
            </div>
        </div>
        """, unsafe_allow_html=True)
        

    st.markdown("<br>", unsafe_allow_html=True)

    # SEÇÃO: RESILIÊNCIA CLIMÁTICA (EL NIÑO)
    st.markdown('''
    <div style="background: rgba(30, 10, 10, 0.75); border: 1px solid rgba(239, 83, 80, 0.35); border-radius: 16px; padding: 32px; margin-bottom: 0px; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);">
        <h3 style='color: #EF5350; font-weight: 700; margin-top: 0; margin-bottom: 12px;'>Previsão à Prova de El Niño</h3>
        <p style='color: rgba(255,255,255,0.85); font-size: 15.5px; line-height: 1.6; margin-bottom: 0;'>
            O clima extremo quebra as médias históricas. O <b>OmniCrop AI</b> é o primeiro sistema que ensina o oceano à Inteligência Artificial. Nossa plataforma ingere o <strong>Índice ENSO (Oceanic Niño Index)</strong> em tempo real. Se o algoritmo detectar um El Niño forte ou La Niña, ele ajusta os <i>Lags</i> de umidade e alerta o agricultor para mitigar a seca com antecedência.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")

    # SEÇÃO: COMO FUNCIONA (Foco no Utilizador)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <div class="glass-label">
            <h2 style='margin-bottom: 8px; margin-top: 0;'>Como Funciona o OmniCrop AI?</h2>
            <p style='color: #a1a1aa; font-size: 16px; margin-bottom: 0;'>A jornada da informação: do satélite até à sua tomada de decisão em 4 passos simples.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info("**1. Mapeamento**\n\nAdicione a sua fazenda com um clique. O sistema registra as coordenadas e conecta-se aos satélites instantaneamente.")
    with col2:
        st.warning("**2. Monitoramento**\n\nColeta automática e contínua de dados de chuva, temperatura e radiação solar da sua região.")
    with col3:
        st.success("**3. Análise da IA**\n\nO nosso Satélite Virtual calcula a saúde da planta cruzando o clima com a biologia da cultura.")
    with col4:
        st.error("**4. Ação e Decisão**\n\nReceba alertas de risco hídrico, simule cenários e descarregue relatórios automáticos.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <div class="glass-label" style="padding: 10px 24px;">
            <h4 style='color: #E2E8F0; margin: 0;'>Culturas Monitoradas</h4>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cc1, cc2, cc3, cc4, cc5 = st.columns(5)
    crops_data = [
        ("Cana-de-Açúcar", "Operacional"),
        ("Soja", "Operacional"),
        ("Milho", "Operacional"),
        ("Café", "Operacional"),
        ("Pastagem", "Operacional"),
    ]
    for col, (crop_name, status) in zip([cc1, cc2, cc3, cc4, cc5], crops_data):
        with col:
            st.markdown(f"""
            <div class="glass-crop-card">
                <div style="font-weight: 700; color: #fff; font-size: 14.5px; margin-bottom: 4px;">{crop_name}</div>
                <div style="font-size: 11px; color: #69F0AE; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;">
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #69F0AE; margin-right: 5px; box-shadow: 0 0 6px #69F0AE;"></span>{status}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Validação Científica & Métricas de Acurácia (Cross-Validation Temporal 2024–2026)", expanded=True):
        st.markdown("""
        <p style='color: #cbd5e1; font-size: 14px;'>
        Métricas de acurácia obtidas no conjunto de teste independente (out-of-time test set) utilizando o algoritmo 
        <b>HistGradientBoostingRegressor</b> com hiperparâmetros otimizados por cultura:
        </p>
        """, unsafe_allow_html=True)

        m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
        with m_c1:
            st.metric(label="Cana-de-Açúcar", value="MAE 0.0217", delta="RMSE 0.0315")
            st.caption("Alta precisão no monitoramento do ciclo semi-perene e acúmulo de ATR.")
        with m_c2:
            st.metric(label="Soja", value="R² 0.8685", delta="MAE 0.0557")
            st.caption("Forte correlação no pico vegetativo das fases reprodutivas R1 a R5.")
        with m_c3:
            st.metric(label="Milho", value="R² 0.7053", delta="MAE 0.1022")
            st.caption("Robustez frente à alta volatilidade no pendoamento VT-R1.")
        with m_c4:
            st.metric(label="Café", value="R² 0.8801", delta="MAE 0.0254")
            st.caption("Estabilidade excelente para dossel contínuo de culturas perenes.")
        with m_c5:
            st.metric(label="Pastagem", value="R² 0.9674", delta="MAE 0.0238")
            st.caption("Precisão superior a 96% na captação do vigor estival da Brachiaria.")

        st.markdown("<div style='height: 1px; background: rgba(105, 240, 174, 0.2); margin: 24px 0 20px 0;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-methodology-card">
            <h5 style="color: #69F0AE; margin-top: 0; margin-bottom: 12px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                Notas Metodológicas de Governança e Interpretação dos Indicadores:
            </h5>
            <ul style="color: #cbd5e1; font-size: 13.5px; line-height: 1.7; margin-bottom: 0; padding-left: 20px;">
                <li><b style="color: #fff;">O que é o R² (Coeficiente de Determinação)?</b> Indica a porcentagem da variação do vigor da biomassa que o modelo explica (ex: 96,7% na pecuária e 88,0% no café).</li>
                <li><b style="color: #fff;">O que é o MAE (Erro Médio Absoluto)?</b> Erro médio na escala contínua do NDVI (0 a 1). Um MAE de ~0.02 significa desvio ínfimo de apenas 2 centésimos em relação ao satélite físico Sentinel-2/MODIS.</li>
                <li><b style="color: #fff;">Validação Cruzada Temporal (Backtesting Out-of-Time):</b> Modelos avaliados estritamente em safras subsequentes futuras (2024–2026), garantindo ausência total de contaminação cruzada (<i>data leakage</i>) e replicabilidade em campo.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center;">
        <div class="glass-label" style="padding: 8px 20px;">
            <p style='color: #a1a1aa; font-size: 14px; margin: 0;'><b>INFRAESTRUTURA:</b> Python • Streamlit • Supabase (Auth/RLS) • Gradient Boosting (scikit-learn) • Google Gemini AI (RAG)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_copy, col_links = st.columns(2)
    with col_copy:
        st.markdown("<p style='color: rgba(255,255,255,0.3); font-size: 12px; margin: 0;'>OmniCrop AI © 2026 — Inteligência Agronômica SaaS<br>v2.0 (Plataforma Multi-Culturas: Cana, Soja, Milho, Café e Pastagem)</p>", unsafe_allow_html=True)
    with col_links:
        st.markdown("<p style='text-align: right; color: rgba(255,255,255,0.3); font-size: 12px; margin: 0;'><a href='https://www.linkedin.com/in/pedro-sandoval-92bb92261' target='_blank' style='color: #10b981; text-decoration: none;'>LinkedIn</a> • <a href='https://github.com/PhSandoval' target='_blank' style='color: #10b981; text-decoration: none;'>GitHub</a></p>", unsafe_allow_html=True)
