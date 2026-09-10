import streamlit as st
from pathlib import Path

def render_landing_page():
    # Navbar SaaS
    base_dir = Path(__file__).resolve().parents[1] # points to frontend
    logo_path = str(base_dir / "assets" / "logo.png")

    nav_left, nav_mid, nav_right = st.columns([1, 4, 1])
    with nav_left:
        st.image(logo_path, use_container_width=True)
    with nav_right:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Login / Entrar", use_container_width=True):
            st.session_state['show_login'] = True
            st.rerun()

    # Usando o estilo de injecao de CSS base da aplicacao
    st.markdown("""
    <style>
    .landing-hero {
        text-align: center;
        padding: 60px 20px;
        background: rgba(10, 25, 15, 0.55);
        border: 1px solid rgba(105, 240, 174, 0.15);
        border-radius: 24px;
        backdrop-filter: blur(10px);
        margin-bottom: 40px;
    }
    .landing-title {
        font-size: 56px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        margin-bottom: 16px;
    }
    .landing-subtitle {
        font-size: 20px;
        color: rgba(180, 230, 180, 0.8);
        font-weight: 400;
        margin-bottom: 32px;
        line-height: 1.5;
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
        border-color: rgba(105, 240, 174, 0.3);
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

    # Hero Section
    st.markdown("""
    <div class="landing-hero">
        <div class="landing-title">OmniCrop <span style="color: #69F0AE;">AI</span></div>
        <div class="landing-subtitle">
            Inteligência Agronômica e Machine Learning para gestão de safras e previsibilidade climática em tempo real.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA Dinâmico
    _, col_cta, _ = st.columns([1.5, 2, 1.5])
    
    with col_cta:
        if 'user' in st.session_state and st.session_state['user']:
            if st.button("🚀 Ir para o Dashboard", use_container_width=True, type="primary"):
                st.session_state['show_landing'] = False
                st.rerun()
        else:
            if st.button("Entrar na Plataforma", use_container_width=True, type="primary"):
                st.session_state['show_login'] = True
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Features Grid
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
