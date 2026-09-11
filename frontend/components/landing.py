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
        background: rgba(8, 20, 12, 0.70) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px;
        padding: 12px 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1.5 Navbar no Topo (Logo na esquerda, Botão na direita)
    col_nav_logo, _, col_nav_btn = st.columns([1, 4, 1])
    with col_nav_logo:
        st.image(logo_path, width=80)
    with col_nav_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if 'user' in st.session_state and st.session_state['user']:
            if st.button("Painel", use_container_width=True):
                st.session_state['show_landing'] = False
                st.rerun()
        else:
            if st.button("Login", use_container_width=True):
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
        
        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            if 'user' in st.session_state and st.session_state['user']:
                if st.button("🚀 Ir para o Dashboard", use_container_width=True, type="primary"):
                    st.session_state['show_landing'] = False
                    st.rerun()
            else:
                if st.button("Acessar Plataforma", use_container_width=True, type="primary"):
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
            <div class="feature-title">Satélite Virtual (XGBoost)</div>
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
        <h3 style='color: #EF5350; font-weight: 700; margin-top: 0; margin-bottom: 12px;'>🌍 Previsão à Prova de El Niño</h3>
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
        st.info("📍 **1. Mapeamento**\n\nAdicione a sua fazenda com um clique. O sistema regista as coordenadas e conecta-se aos satélites instantaneamente.")
    with col2:
        st.warning("☁️ **2. Monitoramento**\n\nColeta automática e contínua de dados de chuva, temperatura e radiação solar da sua região.")
    with col3:
        st.success("🧠 **3. Análise da IA**\n\nO nosso Satélite Virtual calcula a saúde da planta cruzando o clima com a biologia da cultura.")
    with col4:
        st.error("📊 **4. Ação e Decisão**\n\nReceba alertas de risco hídrico, simule cenários e descarregue relatórios automáticos.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <div class="glass-label" style="padding: 10px 24px;">
            <h4 style='color: #E2E8F0; margin: 0;'>Culturas Monitoradas</h4>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1: 
        st.success("🌱 Cana-de-Açúcar (Operacional)")
    with cc2: 
        st.warning("🌾 Soja (Treinando V2.0)")
    with cc3: 
        st.info("☕ Café (Em Breve)")
    with cc4: 
        st.info("🐄 Pastagens (Em Breve)")
        
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center;">
        <div class="glass-label" style="padding: 8px 20px;">
            <p style='color: #a1a1aa; font-size: 14px; margin: 0;'><b>INFRAESTRUTURA:</b> Python • Streamlit • Supabase (Auth/RLS) • XGBoost • Google Gemini AI (RAG)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_copy, col_links = st.columns(2)
    with col_copy:
        st.markdown("<p style='color: rgba(255,255,255,0.3); font-size: 12px; margin: 0;'>OmniCrop AI © 2026 — Inteligência Agronômica SaaS<br>v1.0 (Módulo Cana-de-Açúcar)</p>", unsafe_allow_html=True)
    with col_links:
        st.markdown("<p style='text-align: right; color: rgba(255,255,255,0.3); font-size: 12px; margin: 0;'><a href='https://www.linkedin.com/in/pedro-sandoval-92bb92261' target='_blank' style='color: #10b981; text-decoration: none;'>LinkedIn</a> • <a href='https://github.com/PhSandoval' target='_blank' style='color: #10b981; text-decoration: none;'>GitHub</a></p>", unsafe_allow_html=True)
