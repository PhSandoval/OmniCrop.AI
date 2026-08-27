"""Global CSS — Clean SaaS Light Theme."""
import streamlit as st

def inject_css() -> None:
    css = """
<style>
/* ── Tema Claro e Limpo (SaaS) ── */
body {
    background-color: #F8FAFC !important;
}

html, body, [class*="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp {
    background-color: #F8FAFC !important;
    background: #F8FAFC !important;
}

/* Garante texto legivel */
* {
    color: #334155;
    font-family: 'Inter', -apple-system, sans-serif;
}

/* ── Remocao de Ruido Global ── */
hr { display: none !important; }
footer { display: none !important; }

/* ── Sidebar Limpa ── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] * { color: #475569 !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Metricas Minimalistas ── */
[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 16px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
[data-testid="stMetricLabel"] {
    color: #64748B !important; 
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
}
[data-testid="stMetricValue"] {
    color: #0F172A !important; 
    font-size: 32px !important; 
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricDelta"] { color: #10B981 !important; font-weight: 500 !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

/* ── Headers de Secao ── */
.sec-header {
    font-size: 13px; 
    font-weight: 700; 
    color: #475569;
    text-transform: uppercase; 
    letter-spacing: 0.1em;
    margin-top: 32px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #F1F5F9;
}

/* ── Markdown colors ── */
.stMarkdown p, .stMarkdown span {
    color: #334155 !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    color: #0F172A !important;
}

/* ── Alertas ── */
.stAlert {
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
}

/* ── Botoes ── */
.stButton > button {
    background-color: #10B981 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #059669 !important;
}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)
