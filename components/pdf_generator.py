import tempfile
from fpdf import FPDF
from datetime import datetime
import streamlit as st
import google.generativeai as genai

class PDF(FPDF):
    def header(self):
        self.set_fill_color(22, 160, 133) # Verde Corporativo
        self.rect(0, 0, 210, 25, style='F')
        
        self.set_y(8)
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'RELATÓRIO EXECUTIVO - SUGARCANE COPILOT', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Gerado automaticamente por IA', align='C')

def generate_pdf_report(farm_name: str, city: str, payload: dict, resultado: dict) -> bytes:
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # ------------------ CABEÇALHO DA FAZENDA ------------------
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, f"Identificação do Talhão: {farm_name}", new_x="LMARGIN", new_y="NEXT", align="L")
    
    pdf.set_font("helvetica", "", 11)
    pdf.cell(95, 6, f"Localização: {city}", align="L")
    pdf.cell(95, 6, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="R")
    
    pdf.ln(10)
    
    # ------------------ SEÇÃO: RESUMO CLIMÁTICO ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(41, 128, 185) # Azul
    pdf.cell(190, 8, " 1. DADOS MICROCLIMÁTICOS", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(2)
    
    # Tabela
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(240, 240, 240)
    
    pdf.cell(47.5, 8, "Chuva 30d", border=1, align="C", fill=True)
    pdf.cell(47.5, 8, "Chuva 60d", border=1, align="C", fill=True)
    pdf.cell(47.5, 8, "Chuva 90d", border=1, align="C", fill=True)
    pdf.cell(47.5, 8, "Graus-Dia (GDA)", border=1, align="C", fill=True)
    pdf.ln(8)
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(47.5, 8, f"{payload.get('chuva_acumulada_30d', 0):.1f} mm", border=1, align="C")
    pdf.cell(47.5, 8, f"{payload.get('chuva_acumulada_60d', 0):.1f} mm", border=1, align="C")
    pdf.cell(47.5, 8, f"{payload.get('chuva_acumulada_90d', 0):.1f} mm", border=1, align="C")
    pdf.cell(47.5, 8, f"{payload.get('GDA_mensal', 0):.1f}", border=1, align="C")
    
    pdf.ln(10)
    
    # ------------------ SEÇÃO: PREDIÇÃO DE VIGOR ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(39, 174, 96) # Verde
    pdf.cell(190, 8, " 2. INTELIGÊNCIA PREDITIVA (NDVI)", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 6, "Baseado nas condições edafoclimáticas históricas e recentes, o modelo de Inteligência Artificial estimou o Vigor Vegetativo atual.")
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(90, 8, f"Índice Previsto (NDVI): {resultado.get('ndvi_previsto', 0):.3f}", border=0)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("helvetica", "I", 10)
    pdf.cell(100, 8, f"Confiabilidade: {resultado.get('confiabilidade_modelo', 'Alta')}", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # ------------------ SEÇÃO: ALERTAS OPERACIONAIS ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(230, 126, 34) # Laranja
    pdf.cell(190, 8, " 3. ALERTAS ATIVOS (DSS)", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(4)
    
    alertas = resultado.get("fatores_de_risco_identificados", [])
    pdf.set_font("helvetica", "", 11)
    
    if not alertas:
        pdf.set_text_color(39, 174, 96)
        pdf.cell(0, 8, "[OK] Nenhum risco crítico identificado.", new_x="LMARGIN", new_y="NEXT")
    else:
        for alerta in alertas:
            if "Déficit" in alerta or "Crítico" in alerta or "Risco" in alerta:
                pdf.set_text_color(192, 57, 43) # Red
                pdf.set_font("helvetica", "B", 11)
            else:
                pdf.set_text_color(44, 62, 80)
                pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 6, f"- {alerta}")
            pdf.ln(1)
            
    pdf.ln(5)
    
    # ------------------ SEÇÃO: PARECER DO LLM ------------------
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(142, 68, 173) # Roxo IA
    pdf.cell(190, 8, " 4. PARECER DO AGRÔNOMO (IA)", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
    pdf.ln(4)
    
    parecer_texto = "Gerando parecer..."
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            modelo = genai.GenerativeModel('gemini-3.6-flash')
            prompt = f"Crie um parecer executivo de exatas 3 linhas sobre este talhão. Dados: NDVI={resultado.get('ndvi_previsto', 0):.3f}, Chuva30d={payload.get('chuva_acumulada_30d', 0):.1f}mm. Alertas: {', '.join(alertas)}. Seja direto e profissional."
            res = modelo.generate_content(prompt)
            parecer_texto = res.text.replace("\n", " ")
        else:
            parecer_texto = "API Key do Gemini não configurada. Impossível gerar parecer."
    except Exception as e:
        parecer_texto = f"Erro ao contatar IA: {str(e)}"
        
    pdf.set_text_color(44, 62, 80)
    pdf.set_font("helvetica", "I", 11)
    pdf.multi_cell(0, 6, f'"{parecer_texto}"')
    
    return bytes(pdf.output())
