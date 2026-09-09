"""Global CSS — glassmorphism + sugarcane field background."""
import streamlit as st
import base64

def inject_css(is_login=False) -> None:
    import base64
    from pathlib import Path
    
    base_dir = Path(__file__).resolve().parents[1] # points to frontend/
    
    if is_login:
        bg_file = base_dir / "assets" / "fundo_tech.jpg"
    else:
        bg_file = base_dir / "assets" / "background.jpg"

    with open(bg_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()

    if is_login:
        # Sem gradiente — imagem crua sem escurecimento
        bg_html = f"""
    <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -999;
                background: url('data:image/jpeg;base64,{encoded_string}') center/cover no-repeat;">
    </div>
    """
    else:
        bg_html = f"""
    <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -999;
                background: linear-gradient(180deg, rgba(2, 8, 4, 0.70) 0%, rgba(5, 15, 8, 0.95) 100%),
                url('data:image/jpeg;base64,{encoded_string}') center/cover no-repeat;">
    </div>
    """
    # Div de fundo com a imagem

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
"""
    if is_login:
        css += """
<style>
/* Oculta totalmente a sidebar em páginas de login e landing */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
</style>
"""

    css += """
<style>
/* ── Metricas com Cards (Opacidade) ── */
[data-testid="metric-container"] {
    background: rgba(10, 25, 15, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    padding: 16px !important;
    margin-bottom: 24px !important;
    backdrop-filter: blur(8px);
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

/* ── Botoes (Logout Hover Fix) ── */
[data-testid="baseButton-secondary"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #E2E8F0 !important;
}
[data-testid="baseButton-secondary"]:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    color: #FFF !important;
}

/* ── Esconder "Press Enter to Submit" do Formulario ── */
[data-testid="InputInstructions"], 
div[data-testid="InputInstructions"], 
.st-emotion-cache-1629p8f, 
.st-emotion-cache-nahz7x {
    display: none !important;
    visibility: hidden !important;
}

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


/* ── Estilizacao da Logo ── */
/* Logo e PNG transparente, sem necessidade de recorte circular */

</style>
"""
    st.markdown(css, unsafe_allow_html=True)
