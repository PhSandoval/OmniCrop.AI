"""
Componente Frontend de Relatórios Executivos (OmniCrop AI).
Delega a compilação do relatório corporativo para o motor de relatórios em src.reports.pdf,
garantindo desacoplamento do backend e consumo integral da Camada Ouro e XAI.
"""
from src.reports.pdf import (
    generate_pdf_report as _core_generate_pdf_report,
    OmniCropPDF,
    PDF,
    _fig_to_tmp_png,
)
import streamlit as st


def generate_pdf_report(
    farm_name: str,
    city: str,
    payload: dict,
    resultado: dict,
    df=None,
    gold_kpis: dict | None = None,
    xai_res: dict | None = None,
    gemini_api_key: str | None = None,
) -> bytes:
    """
    Gera o relatório em PDF com integração nativa aos segredos e estado do Streamlit.
    """
    # Se a chave do Gemini não foi passada explicitamente, busca nos segredos do Streamlit
    if not gemini_api_key:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                gemini_api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    return _core_generate_pdf_report(
        farm_name=farm_name,
        city=city,
        payload=payload,
        resultado=resultado,
        df=df,
        gold_kpis=gold_kpis,
        xai_res=xai_res,
        gemini_api_key=gemini_api_key,
    )


__all__ = ["generate_pdf_report", "OmniCropPDF", "PDF"]
