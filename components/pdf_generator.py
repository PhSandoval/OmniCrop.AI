import io
import tempfile
import os
from fpdf import FPDF
from datetime import datetime
import streamlit as st
import google.generativeai as genai


# ── Helper: exporta figura Plotly como PNG temporário ───────────────────────
def _fig_to_tmp_png(fig, width=900, height=300) -> str | None:
    """Salva um gráfico Plotly como PNG e retorna o caminho do arquivo temp."""
    try:
        import plotly.io as pio
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        pio.write_image(
            fig, tmp.name,
            format="png", width=width, height=height, scale=2,
            engine="kaleido"
        )
        return tmp.name
    except Exception:
        return None


# ── Classe PDF com cabeçalho e rodapé corporativos ──────────────────────────
class PDF(FPDF):
    def header(self):
        self.set_fill_color(22, 160, 133)        # Verde OmniCrop
        self.rect(0, 0, 210, 25, style="F")
        self.set_y(8)
        self.set_font("helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "RELATÓRIO EXECUTIVO - OMNICROP AI", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}} - Gerado automaticamente por OmniCrop AI", align="C")

    def section_title(self, number: str, title: str, r: int, g: int, b: int):
        """Barra colorida de seção."""
        self.set_font("helvetica", "B", 12)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(r, g, b)
        self.cell(190, 9, f"  {number}. {title}", new_x="LMARGIN", new_y="NEXT", align="L", fill=True)
        self.ln(3)

    def kpi_card_row(self, labels: list[str], values: list[str]):
        """Linha de cards KPI: rótulo cinza claro em cima, valor em negrito embaixo."""
        n = len(labels)
        w = 190 / n
        # Linha de rótulos
        self.set_font("helvetica", "B", 8)
        self.set_text_color(90, 90, 90)
        self.set_fill_color(235, 238, 240)
        for label in labels:
            self.cell(w, 7, label, border=1, align="C", fill=True)
        self.ln(7)
        # Linha de valores
        self.set_font("helvetica", "B", 13)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(255, 255, 255)
        for value in values:
            self.cell(w, 11, value, border=1, align="C", fill=True)
        self.ln(11)


# ── Função principal ─────────────────────────────────────────────────────────
def generate_pdf_report(
    farm_name: str,
    city: str,
    payload: dict,
    resultado: dict,
    df=None           # DataFrame histórico para gerar o gráfico NDVI
) -> bytes:

    pdf = PDF()
    pdf.alias_nb_pages()

    # ① FIX: quebra automática de página - evita corte de texto no rodapé
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()

    # ── IDENTIFICAÇÃO DO TALHÃO ──────────────────────────────────────────────
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, f"Talhão: {farm_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 6, f"Localização: {city}")
    pdf.cell(95, 6, f"Emitido em: {datetime.now().strftime('%d/%m/%Y  %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.ln(6)

    # ── ③ GRÁFICO NDVI (O "EFEITO UAU") ─────────────────────────────────────
    if df is not None:
        try:
            from components.charts import ndvi_line
            fig = ndvi_line(df)
            # Fundo branco para o PNG do PDF
            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="rgba(240,248,245,1)",
                font=dict(color="#333333"),
            )
            chart_path = _fig_to_tmp_png(fig, width=900, height=280)
            if chart_path:
                pdf.set_font("helvetica", "B", 10)
                pdf.set_text_color(22, 160, 133)
                pdf.cell(0, 6, "Série Histórica de Vigor Vegetativo (NDVI) - Últimos 90 dias", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                pdf.image(chart_path, x=10, w=190)
                os.unlink(chart_path)   # limpa o arquivo temp
                pdf.ln(4)
        except Exception:
            pass   # Se kaleido não estiver instalado, ignora o gráfico silenciosamente

    # ── 1. DADOS MICROCLIMÁTICOS (CARDS) ────────────────────────────────────
    pdf.section_title("1", "DADOS MICROCLIMÁTICOS", 41, 128, 185)

    pdf.kpi_card_row(
        ["Chuva 30d", "Chuva 60d", "Chuva 90d", "Graus-Dia (GDA)"],
        [
            f"{payload.get('chuva_acumulada_30d', 0):.1f} mm",
            f"{payload.get('chuva_acumulada_60d', 0):.1f} mm",
            f"{payload.get('chuva_acumulada_90d', 0):.1f} mm",
            f"{payload.get('GDA_mensal', 0):.1f}",
        ],
    )

    pdf.kpi_card_row(
        ["Temp. Média", "Temp. Máxima", "Temp. Mínima", "Radiação Média"],
        [
            f"{payload.get('temp_media', 0):.1f} °C",
            f"{payload.get('temp_max', 0):.1f} °C",
            f"{payload.get('temp_min', 0):.1f} °C",
            f"{payload.get('radiacao_media', 0):.0f} W/m²",
        ],
    )
    pdf.ln(4)

    # ── 2. INTELIGÊNCIA PREDITIVA (NDVI) ─────────────────────────────────────
    pdf.section_title("2", "INTELIGÊNCIA PREDITIVA (NDVI)", 39, 174, 96)

    ndvi_val = resultado.get("ndvi_previsto", 0)
    fase = resultado.get("fase_fenologica", "-")
    # Truncate to avoid PDF cell overflow
    conf_raw = str(resultado.get("confiabilidade_modelo", "Alta"))
    conf = conf_raw.split("(")[0].strip()
    status = resultado.get("status_geral", "-")

    pdf.kpi_card_row(
        ["NDVI Estimado", "Fase Fenológica", "Confiabilidade", "Status Geral"],
        [f"{ndvi_val:.3f}", fase, conf, status],
    )

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(70, 70, 70)
    pdf.multi_cell(
        0, 5,
        "O Índice NDVI foi estimado pelo modelo XGBoost treinado com 10 anos de histórico climático e "
        "leituras de satélite. Valores próximos a 1.0 indicam lavoura saudável e em pleno crescimento.",
    )
    pdf.ln(4)

    # ── 3. ALERTAS OPERACIONAIS (DSS) ─────────────────────────────────────────
    pdf.section_title("3", "ALERTAS ATIVOS - DSS", 230, 126, 34)

    alertas = resultado.get("fatores_de_risco_identificados", [])
    pdf.set_font("helvetica", "", 11)

    if not alertas:
        pdf.set_fill_color(232, 248, 240)
        pdf.set_text_color(39, 174, 96)
        pdf.set_draw_color(39, 174, 96)
        pdf.cell(0, 9, "  [OK]  Nenhum risco crítico identificado.", border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
    else:
        for alerta in alertas:
            is_critico = any(w in alerta for w in ["Déficit", "Crítico", "Risco", "Alerta"])
            if is_critico:
                pdf.set_fill_color(253, 235, 232)
                pdf.set_text_color(192, 57, 43)
                pdf.set_draw_color(192, 57, 43)
                pdf.set_font("helvetica", "B", 10)
            else:
                pdf.set_fill_color(250, 250, 250)
                pdf.set_text_color(44, 62, 80)
                pdf.set_draw_color(180, 180, 180)
                pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 8, f"  - {alerta}", border=1, new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(1)

    pdf.ln(5)

    # ── 4. PARECER DO AGRÔNOMO (GEMINI IA) ───────────────────────────────────
    pdf.section_title("4", "PARECER DO AGRÔNOMO (IA - GEMINI)", 142, 68, 173)

    parecer_texto = "Análise indisponível."
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            modelo = genai.GenerativeModel("gemini-3.6-flash")
            prompt = (
                f"Você é um agrônomo especialista em cana-de-açúcar. Escreva um parecer executivo "
                f"objetivo com exatamente 3 frases sobre este talhão. "
                f"Dados: NDVI={ndvi_val:.3f}, Chuva30d={payload.get('chuva_acumulada_30d', 0):.1f}mm, "
                f"GDA={payload.get('GDA_mensal', 0):.1f}, Fase={fase}. "
                f"Alertas ativos: {', '.join(alertas) if alertas else 'Nenhum'}. "
                f"Seja direto, técnico e profissional. Não use markdown."
            )
            res = modelo.generate_content(prompt)
            parecer_texto = res.text.strip().replace("\n", " ")
    except Exception as e:
        parecer_texto = f"Erro ao contatar IA: {str(e)}"

    # Box visual com fundo lilás suave
    pdf.set_fill_color(245, 240, 252)
    pdf.set_draw_color(142, 68, 173)
    pdf.set_text_color(60, 30, 80)
    pdf.set_font("helvetica", "I", 11)
    pdf.multi_cell(0, 6, f'"{parecer_texto}"', border=1, fill=True)

    return bytes(pdf.output())
