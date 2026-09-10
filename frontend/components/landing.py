import streamlit as st
from pathlib import Path

def render_landing_page():
    # Configurar paths
    base_dir = Path(__file__).resolve().parents[1] # points to frontend
    logo_path = str(base_dir / "assets" / "logo.png")

    # 1. Navbar (Topo Direito)
    col_space, col_login = st.columns([8, 2])
    with col_login:
        if 'user' in st.session_state and st.session_state['user']:
            if st.button("🚀 Ir para o Dashboard", use_container_width=True, type="primary"):
                st.session_state['show_landing'] = False
                st.rerun()
        else:
            if st.button("Acessar Plataforma", use_container_width=True, type="primary"):
                st.session_state['show_login'] = True
                st.session_state['show_landing'] = False
                st.rerun()

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
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 2. O Centro da Tela (Logo e Textos)
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        # Centralizar a logo usando colunas aninhadas
        _, col_logo, _ = st.columns([1, 0.5, 1])
        with col_logo:
            st.image(logo_path, width=180)
            
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
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 12px; margin-top: 40px;">
        OmniCrop AI © 2026 — Inteligência Agronômica SaaS<br>
        v1.0 (Módulo Cana-de-Açúcar)
    </div>
    """, unsafe_allow_html=True)
