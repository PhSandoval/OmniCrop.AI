import tempfile
from fpdf import FPDF
from datetime import datetime

def generate_pdf_report(farm_name: str, city: str, ndvi: float, chuva_30d: float, alertas: list) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(10, 100, 30)
    pdf.cell(0, 15, "SugarCane Copilot - Relatorio Semanal", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, f"Fazenda: {farm_name} | Local: {city}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 10, f"Data da Analise: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.ln(10)
    
    # KPIs
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "1. Indicadores Principais (KPIs)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"-> Vigor Vegetativo (NDVI Previsto): {ndvi:.3f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"-> Chuva Acumulada (Ultimos 30 dias): {chuva_30d:.1f} mm", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    
    # Alertas
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(200, 50, 50)
    pdf.cell(0, 10, "2. Alertas Operacionais (DSS)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(50, 50, 50)
    
    if len(alertas) == 0:
        pdf.cell(0, 8, "Nenhum risco severo identificado na operacao atual.", new_x="LMARGIN", new_y="NEXT")
    else:
        for alerta in alertas:
            # handle encoding for special characters (FPDF basic fonts only support latin-1)
            clean_alerta = alerta.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, f"- {clean_alerta}")
            
    pdf.ln(10)
    
    # Footer
    pdf.set_font("helvetica", "I", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Este relatorio e gerado automaticamente por Inteligencia Artificial (XGBoost).", new_x="LMARGIN", new_y="NEXT", align="C")
    
    return bytes(pdf.output())
