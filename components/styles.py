"""Global CSS — glassmorphism + sugarcane field background."""
import streamlit as st
from components.assets import BG_B64

def inject_css() -> None:
    # Div de fundo com a imagem
    bg_html = f"""
    <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -999;
                background: linear-gradient(180deg, rgba(2, 8, 4, 0.50) 0%, rgba(5, 15, 8, 0.75) 100%), 
                url('data:image/jpeg;base64,{BG_B64}') center/cover no-repeat;">
    </div>
    """
    st.markdown(bg_html, unsafe_allow_html=True)
    
    # Resto do estilo (minimalista dark)
    css = """
<style>
/* Força bruta contra o fundo padrao do Streamlit */
html, body, [class*="stApp"], [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"], .stApp {
    background-color: transparent !important;
    background: transparent !important;
}

/* Garante texto legivel em caso extremo */
* {
    color: #E2E8F0;
    font-family: 'Inter', -apple-system, sans-serif;
}

/* ── Remocao de Ruido Global ── */
hr { display: none !important; }
[data-testid="stHeader"] { 
    background: transparent !important; 
}
[data-testid="stHeader"]::before {
    display: none !important;
}
footer { display: none !important; }

/* ── Sidebar Limpa ── */
[data-testid="stSidebar"] {
    background-color: rgba(8, 61, 21, 0.95) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; font-weight: 400; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Metricas Minimalistas (Sem Caixas) ── */
[data-testid="metric-container"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-bottom: 24px !important;
}
[data-testid="stMetricLabel"] {
    color: #94A3B8 !important; 
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF !important; 
    font-size: 32px !important; 
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
}
[data-testid="stMetricDelta"] { color: #4ADE80 !important; font-weight: 500 !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

/* ── Headers de Secao ── */
.sec-header {
    font-size: 11px; 
    font-weight: 600; 
    color: #94A3B8;
    text-transform: uppercase; 
    letter-spacing: 0.1em;
    margin-top: 32px;
    margin-bottom: 16px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

/* ── Markdown colors ── */
.stMarkdown p, .stMarkdown span {
    color: #E2E8F0 !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    color: #FFFFFF !important;
}

</style>
"""
    st.markdown(css, unsafe_allow_html=True)
