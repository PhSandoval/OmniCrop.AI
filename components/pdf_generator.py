import tempfile
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        # Logo ou Titulo do Header
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(22, 160, 133) # Verde Esmeralda
        self.cell(0, 10, 'SUGARCANE COPILOT', ln=True, align='L')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Relatório Executivo de Inteligência Agronômica', ln=True, align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Gerado automaticamente por Inteligência Artificial (XGBoost)', align='C')

def generate_pdf_report(farm_name: str, city: str, payload: dict, resultado: dict) -> bytes:
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # ------------------ CABEÇALHO DA FAZENDA ------------------
    pdf.set_fill_color(240, 248, 245)
    pdf.set_draw_color(22, 160, 133)
    pdf.set_line_width(0.5)
    pdf.rect(10, pdf.get_y(), 190, 25, style='F')
    
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, f" Identificação do Talhão: {farm_name}", new_x="LMARGIN", new_y="NEXT", align="L")
    
    pdf.set_font("helvetica", "", 11)
    pdf.cell(95, 6, f" Localização: {city}", align="L")
    pdf.cell(95, 6, f" Data Base: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="R")
    
    pdf.ln(12)
    
    # ------------------ SEÇÃO: RESUMO CLIMÁTICO ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(41, 128, 185) # Azul
    pdf.cell(190, 8, " 1. DADOS MICROCLIMÁTICOS (OPEN-METEO)", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(2)
    
    # Tabela Climática
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 230, 230)
    
    # Headers
    pdf.cell(47.5, 8, "Chuva 30 Dias", border=1, align="C", fill=True)
    pdf.cell(47.5, 8, "Chuva 60 Dias", border=1, align="C", fill=True)
    pdf.cell(47.5, 8, "Chuva 90 Dias", border=1, align="C", fill=True)
    pdf.cell(47.5, 8, "Graus-Dia (GDA)", border=1, align="C", fill=True)
    pdf.ln(8)
    
    # Dados
    pdf.set_font("helvetica", "", 10)
    c30 = payload.get("chuva_acumulada_30d", 0)
    c60 = payload.get("chuva_acumulada_60d", 0)
    c90 = payload.get("chuva_acumulada_90d", 0)
    gda = payload.get("GDA_mensal", 0)
    
    pdf.cell(47.5, 8, f"{c30:.1f} mm", border=1, align="C")
    pdf.cell(47.5, 8, f"{c60:.1f} mm", border=1, align="C")
    pdf.cell(47.5, 8, f"{c90:.1f} mm", border=1, align="C")
    pdf.cell(47.5, 8, f"{gda:.1f}", border=1, align="C")
    
    pdf.ln(15)
    
    # ------------------ SEÇÃO: PREDIÇÃO DE VIGOR (MACHINE LEARNING) ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(39, 174, 96) # Verde
    pdf.cell(190, 8, " 2. INTELIGÊNCIA PREDITIVA (NDVI)", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(2)
    
    ndvi = resultado.get("ndvi_previsto", 0)
    conf = resultado.get("confiabilidade_modelo", "Alta")
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 6, "Baseado nas condições edafoclimáticas históricas e recentes, o modelo de Machine Learning estimou o Vigor Vegetativo atual da lavoura.")
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(90, 8, f"Índice Previsto (NDVI): {ndvi:.3f}", border=0)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(100, 8, f"Confiabilidade Estatística: {conf}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    
    # ------------------ SEÇÃO: ALERTAS OPERACIONAIS ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(192, 57, 43) # Vermelho
    pdf.cell(190, 8, " 3. DECISION SUPPORT SYSTEM (DSS) - ALERTAS ATIVOS", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(4)
    
    alertas = resultado.get("fatores_de_risco_identificados", [])
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(44, 62, 80)
    
    if not alertas:
        pdf.set_text_color(39, 174, 96)
        pdf.cell(0, 8, "✓ Nenhum risco crítico identificado para a operação atual.", new_x="LMARGIN", new_y="NEXT")
    else:
        for alerta in alertas:
            clean_alerta = alerta.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f"⚠️ {clean_alerta}")
            pdf.ln(2)
            
    pdf.ln(10)
    
    # ------------------ NOTA DE RESPONSABILIDADE ------------------
    pdf.set_y(-40)
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    msg = "Nota Técnica: Este documento consolida dados ambientais e processamento por inteligência artificial (XGBoost Regressor). O NDVI listado não é uma leitura óptica de satélite em tempo real, mas sim uma inferência (nowcast) baseada nos graus-dia e volume hídrico."
    clean_msg = msg.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_msg)
    
    return bytes(pdf.output())
