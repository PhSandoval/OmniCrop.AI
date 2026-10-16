"""
Módulo de Relatórios Executivos da Plataforma OmniCrop AI.
Gera relatórios em PDF corporativos com dados da Camada Ouro e explicabilidade XAI.
"""
from src.reports.pdf import generate_pdf_report, OmniCropPDF

__all__ = ["generate_pdf_report", "OmniCropPDF"]
