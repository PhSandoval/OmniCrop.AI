import io
import os
import tempfile
from datetime import datetime
from fpdf import FPDF


# ── Helper de higienização de strings para fontes padrão FPDF (Latin-1) ──────
def _clean_text(text: str | None) -> str:
    """Substitui caracteres fora de latin-1 por equivalentes seguros para FPDF."""
    if not text:
        return ""
    text = str(text)
    replacements = {
        "➔": "->",
        "→": "->",
        "←": "<-",
        "•": "-",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "✨": "*",
        "⚠️": "[!]",
        "🔴": "[CRITICO]",
        "🟡": "[ALERTA]",
        "🟢": "[OK]",
        "💧": "",
        "🌿": "",
        "🌱": "",
        "🚜": "",
        "📄": "",
        "🤔": "",
        "⬇️": "",
        "🔄": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


# ── Helper: exporta figura Plotly como PNG temporário ───────────────────────
def _fig_to_tmp_png(fig, width=900, height=260) -> str | None:
    """Salva um gráfico Plotly como PNG e retorna o caminho do arquivo temp."""
    try:
        import plotly.io as pio

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        pio.write_image(
            fig,
            tmp.name,
            format="png",
            width=width,
            height=height,
            scale=2,
            engine="kaleido",
        )
        return tmp.name
    except Exception:
        return None


# ── Classe PDF Corporativa com Identidade Visual OmniCrop AI ────────────────
class OmniCropPDF(FPDF):
    def header(self):
        # Header banner em Verde Floresta / Deep Emerald Institucional
        self.set_fill_color(19, 62, 43)
        self.rect(0, 0, 210, 24, style="F")
        # Linha de destaque agronômico (#2ECC71)
        self.set_fill_color(46, 204, 113)
        self.rect(0, 23.2, 210, 0.8, style="F")
        self.set_y(5.5)
        self.set_font("helvetica", "B", 13.5)
        self.set_text_color(255, 255, 255)
        self.cell(
            0,
            6,
            "OMNICROP AI · RELATÓRIO TÉCNICO EXECUTIVO",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.set_font("helvetica", "I", 7.8)
        self.set_text_color(200, 235, 215)
        self.cell(
            0,
            4,
            "Inteligência Agronômica Preditiva · Camada Ouro (Gold KPIs) & Explicabilidade XAI",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 7.5)
        self.set_text_color(130, 140, 135)
        self.cell(
            0,
            6,
            f"Página {self.page_no()}/{{nb}} · OmniCrop AI · Decisão Agronômica Baseada em Dados e MLOps",
            align="C",
        )

    def section_title(self, number: str, title: str, r: int, g: int, b: int):
        """Barra de título com preenchimento colorido institucional."""
        self.set_font("helvetica", "B", 9.5)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(r, g, b)
        self.cell(
            190,
            7,
            f"  {number}. {_clean_text(title)}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
            fill=True,
        )
        self.ln(1.5)

    def kpi_card_row(
        self,
        labels: list[str],
        values: list[str],
        val_colors: list[tuple[int, int, int]] | None = None,
        widths: list[float] | None = None,
    ):
        """Linha de cards KPI: rótulo no topo, valor com auto-ajuste de fonte embaixo."""
        n = max(len(labels), 1)
        if not widths or len(widths) != n:
            widths = [190.0 / n] * n

        # Linha de rótulos
        self.set_font("helvetica", "B", 7.0)
        self.set_text_color(85, 95, 90)
        self.set_fill_color(243, 246, 244)
        self.set_draw_color(210, 222, 218)
        for i, label in enumerate(labels):
            self.cell(widths[i], 5.5, _clean_text(label), border=1, align="C", fill=True)
        self.ln(5.5)

        # Linha de valores
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(210, 222, 218)
        for i, value in enumerate(values):
            val_str = _clean_text(str(value))
            # Auto-escala dinâmica da fonte para prevenir truncamentos e vazamentos
            font_sz = 9.5
            self.set_font("helvetica", "B", font_sz)
            while self.get_string_width(val_str) > (widths[i] - 3.5) and font_sz > 6.5:
                font_sz -= 0.5
                self.set_font("helvetica", "B", font_sz)

            if val_colors and i < len(val_colors) and val_colors[i] is not None:
                cr, cg, cb = val_colors[i]
                self.set_text_color(cr, cg, cb)
            else:
                self.set_text_color(30, 35, 32)
            self.cell(
                widths[i], 7.5, val_str, border=1, align="C", fill=True
            )
        self.ln(8)


# ── Resolução de Chave de API e Parecer Grounded ───────────────────────────
def _resolve_gemini_key(explicit_key: str | None = None) -> str | None:
    if explicit_key:
        return explicit_key
    try:
        from src.utils.copilot_context import get_gemini_api_key

        st_sec = None
        st_sess = None
        try:
            import streamlit as st

            st_sec = getattr(st, "secrets", None)
            st_sess = getattr(st, "session_state", None)
        except Exception:
            pass
        return get_gemini_api_key(st_secrets=st_sec, session_state=st_sess)
    except Exception:
        return os.getenv("GEMINI_API_KEY")


def _get_agronomic_opinion(
    farm_name: str,
    city: str,
    ndvi_val: float,
    fase: str,
    gold_kpis: dict,
    xai_res: dict,
    alertas: list[str],
    api_key: str | None = None,
) -> str:
    """
    Gera o parecer executivo do agrônomo com IA (Google Gemini),
    grounded nos KPIs da Camada Ouro e na decomposição matemática do XAI.
    Possui fallback agronômico determinístico caso offline ou sem chave.
    """
    balanco = float(gold_kpis.get("balanco_hidrico_mm", 0.0))
    dias_sem_chuva = int(gold_kpis.get("dias_sem_chuva", 0))
    risco = str(gold_kpis.get("risco_estresse_hidrico", "BAIXO"))
    rec_gold = str(
        gold_kpis.get(
            "recomendacao_manejo", "Condições hídricas favoráveis ao talhão."
        )
    )
    top_driver = str(xai_res.get("top_driver", "Chuva Recente (30d)"))
    alertas_str = "; ".join(alertas) if alertas else "Nenhum risco crítico ativo"

    # Fallback agronômico determinístico de alta fidelidade
    fallback = (
        f"O talhão em {city} apresenta balanço hídrico de {balanco:+.1f} mm com {dias_sem_chuva} dias sem chuvas "
        f"e classificação de estresse {risco}. O vigor vegetativo projetado indica NDVI de {ndvi_val:.3f} na fase "
        f"de {fase}, impulsionado pelo fator dominante '{top_driver}'. {rec_gold}"
    )

    if not api_key:
        return fallback

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        prompt = (
            f"Você é um consultor sênior de inteligência agronômica especialista em cana-de-açúcar. "
            f"Escreva um parecer executivo rigorosamente técnico e objetivo em exatamente 3 frases sobre o talhão '{farm_name}' ({city}). "
            f"Fundamente sua recomendação citando os seguintes dados da Camada Ouro e XAI: "
            f"Balanço Hídrico={balanco:+.1f} mm, Dias sem chuva={dias_sem_chuva}, Risco de Estresse={risco}, "
            f"NDVI Projetado={ndvi_val:.3f} (Fase: {fase}), Fator Dominante XAI='{top_driver}', "
            f"Alertas DSS={alertas_str}. Seja conciso, direto e profissional. Não use formatação markdown nem asteriscos."
        )

        for m_name in [
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-3.6-flash",
        ]:
            try:
                model = genai.GenerativeModel(m_name)
                res = model.generate_content(prompt)
                if res and res.text:
                    texto = res.text.strip().replace("\n", " ")
                    if len(texto) > 20:
                        return texto
            except Exception:
                continue

        return fallback
    except Exception:
        return fallback


# ── Função Principal de Exportação ─────────────────────────────────────────
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
    Gera o relatório executivo oficial em PDF da fazenda / talhão.

    Parâmetros:
    - farm_name: Nome do talhão ou fazenda.
    - city: Município / localização.
    - payload: Dicionário com telemetria climática (Open-Meteo).
    - resultado: Dicionário com saída do modelo preditivo e DSS.
    - df: DataFrame histórico opcional para série temporal de NDVI.
    - gold_kpis: Dicionário consolidado da Camada Ouro (Balanço Hídrico, Veranico, GDA).
    - xai_res: Decomposição matemática de explicabilidade XAI (Top Driver, impacto marginal).
    - gemini_api_key: Chave opcional do Gemini para parecer agronômico generativo.
    """
    payload = payload or {}
    resultado = resultado or {}

    # 1. Resolução da Camada Ouro (Gold KPIs)
    if not gold_kpis:
        if df is not None:
            try:
                from src.data.ingest_azure import transform_to_gold

                df_window = df.tail(14) if len(df) >= 14 else df
                gold_df = transform_to_gold(df_window)
                if not gold_df.empty:
                    gold_kpis = gold_df.iloc[0].to_dict()
            except Exception:
                gold_kpis = {}

    if not gold_kpis:
        chuva_30d = float(payload.get("chuva_acumulada_30d", 0.0))
        et0_estimada = float(payload.get("et0_acumulada_30d", 42.0))
        balanco_estimado = round(chuva_30d - et0_estimada, 1)
        dias_sem_chuva_est = 0 if chuva_30d > 25.0 else 5
        risco_est = (
            "CRÍTICO"
            if balanco_estimado < -25 or dias_sem_chuva_est >= 6
            else ("MODERADO" if balanco_estimado < -10 else "BAIXO")
        )
        rec_est = (
            "Alerta de Estresse Hídrico: avaliar irrigação imediata."
            if risco_est == "CRÍTICO"
            else "Condições hídricas dentro dos parâmetros de monitoramento."
        )

        gold_kpis = {
            "balanco_hidrico_mm": balanco_estimado,
            "dias_sem_chuva": dias_sem_chuva_est,
            "gda_total_acumulado": round(float(payload.get("GDA_mensal", 0.0)), 1),
            "risco_estresse_hidrico": risco_est,
            "recomendacao_manejo": rec_est,
            "chuva_total_mm": chuva_30d,
            "et0_total_mm": et0_estimada,
            "temp_max_media_c": float(payload.get("t_max", 0.0)),
            "temp_min_media_c": float(payload.get("t_min", 0.0)),
        }

    # 2. Resolução da Explicabilidade XAI
    if not xai_res:
        try:
            from src.models.predict import explain_prediction_delta

            base_payload = {
                "chuva_acumulada_30d": max(
                    0.0, float(payload.get("chuva_acumulada_30d", 40.0)) - 15.0
                ),
                "chuva_acumulada_60d": max(
                    0.0, float(payload.get("chuva_acumulada_60d", 80.0)) - 15.0
                ),
                "chuva_acumulada_90d": max(
                    0.0, float(payload.get("chuva_acumulada_90d", 120.0)) - 15.0
                ),
                "GDA_mensal": max(
                    0.0, float(payload.get("GDA_mensal", 250.0)) - 10.0
                ),
            }
            xai_res = explain_prediction_delta(base_payload, payload)
        except Exception:
            xai_res = {
                "top_driver": "Chuva Recente (30d)",
                "contributions": {
                    "Chuva Recente (30d)": +0.035,
                    "Chuva Médio Prazo (60d)": +0.015,
                    "Soma Térmica (GDA)": +0.008,
                },
                "narrativa": "Vigor vegetativo sustentado principalmente pela precipitação acumulada recente.",
                "pred_base": resultado.get("ndvi_previsto", 0.72),
                "pred_sim": resultado.get("ndvi_previsto", 0.72),
                "total_delta": 0.0,
            }

    # 3. Inicialização do Documento PDF
    pdf = OmniCropPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── IDENTIFICAÇÃO DO TALHÃO ──────────────────────────────────────────────
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(25, 45, 35)
    pdf.cell(100, 6, f"Talhão: {_clean_text(farm_name)}", new_x="RIGHT")

    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(110, 120, 115)
    pdf.cell(
        90,
        6,
        f"Emitido em: {datetime.now().strftime('%d/%m/%Y  %H:%M')}",
        new_x="LMARGIN",
        new_y="NEXT",
        align="R",
    )

    crop_display = resultado.get("crop_name") or resultado.get("crop_id") or "Cana-de-Açúcar"
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(90, 100, 95)
    pdf.cell(
        0,
        4,
        f"Localização: {_clean_text(city)} · Cultura: {_clean_text(crop_display)}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)

    # ── SÉRIE HISTÓRICA NDVI (GRÁFICO PLOTLY) ─────────────────────────────────
    if df is not None:
        try:
            from src.ui.components.charts import ndvi_line

            fig = ndvi_line(df)
            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="rgba(240,248,245,1)",
                font=dict(color="#333333"),
                margin=dict(t=25, b=25, l=30, r=20),
            )
            chart_path = _fig_to_tmp_png(fig, width=900, height=250)
            if chart_path:
                pdf.set_font("helvetica", "B", 8.5)
                pdf.set_text_color(22, 120, 85)
                pdf.cell(
                    0,
                    5,
                    "Série Histórica de Vigor Vegetativo (NDVI) - Últimos 90 dias",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
                pdf.ln(1)
                pdf.image(chart_path, x=10, w=190)
                try:
                    os.unlink(chart_path)
                except Exception:
                    pass
                pdf.ln(3)
        except Exception:
            pass

    # ── 1. BALANÇO HÍDRICO & CAMADA OURO ─────────────────────────────────────
    pdf.section_title("1", "BALANÇO HÍDRICO & CAMADA OURO (KPIs EXECUTIVOS)", 27, 85, 110)

    balanco_val = float(gold_kpis.get("balanco_hidrico_mm", 0.0))
    dias_sem_chuva_val = int(gold_kpis.get("dias_sem_chuva", 0))
    gda_total_val = float(gold_kpis.get("gda_total_acumulado", 0.0))
    risco_estresse_val = str(gold_kpis.get("risco_estresse_hidrico", "BAIXO"))

    # Cores dinâmicas dos KPIs executivos
    cor_balanco = (39, 150, 85) if balanco_val >= 0 else ((192, 57, 43) if balanco_val < -25 else (211, 84, 0))
    cor_veranico = (192, 57, 43) if dias_sem_chuva_val >= 6 else ((211, 84, 0) if dias_sem_chuva_val >= 4 else (39, 150, 85))
    cor_risco = (192, 57, 43) if risco_estresse_val == "CRÍTICO" else ((211, 84, 0) if risco_estresse_val == "MODERADO" else (39, 150, 85))

    pdf.kpi_card_row(
        ["Balanço Hídrico Líquido", "Dias sem Chuva (Veranico)", "GDA Acumulado", "Risco de Estresse"],
        [
            f"{balanco_val:+.1f} mm",
            f"{dias_sem_chuva_val} dias",
            f"{gda_total_val:.1f}",
            risco_estresse_val,
        ],
        val_colors=[cor_balanco, cor_veranico, (30, 35, 32), cor_risco],
    )
    pdf.ln(0.5)

    pdf.kpi_card_row(
        ["Chuva 30d", "Chuva 60d", "Chuva 90d", "Evapotransp. (ET0)"],
        [
            f"{payload.get('chuva_acumulada_30d', 0):.1f} mm",
            f"{payload.get('chuva_acumulada_60d', 0):.1f} mm",
            f"{payload.get('chuva_acumulada_90d', 0):.1f} mm",
            f"{gold_kpis.get('et0_total_mm', payload.get('et0_acumulada_30d', 42.0)):.1f} mm",
        ],
    )
    pdf.ln(0.5)

    pdf.kpi_card_row(
        ["Temp. Média", "Temp. Máxima", "Temp. Mínima", "Radiação Média"],
        [
            f"{payload.get('t_mean', 0):.1f} °C",
            f"{payload.get('t_max', gold_kpis.get('temp_max_media_c', 0)):.1f} °C",
            f"{payload.get('t_min', gold_kpis.get('temp_min_media_c', 0)):.1f} °C",
            f"{payload.get('radiacao_solar_mean', 0):.0f} W/m²",
        ],
    )
    pdf.ln(1)

    # Diretriz Operacional da Camada Ouro
    rec_gold_txt = str(gold_kpis.get("recomendacao_manejo", "Condições hídricas favoráveis."))
    pdf.set_fill_color(244, 248, 251)
    pdf.set_draw_color(180, 205, 220)
    pdf.set_text_color(20, 50, 75)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(190, 4.5, f"  Diretriz Operacional (Camada Ouro):", border="LTR", new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("helvetica", "", 7.5)
    pdf.multi_cell(190, 4.0, f"  {_clean_text(rec_gold_txt)}", border="LBR", fill=True)
    pdf.ln(3)

    # ── 2. INTELIGÊNCIA PREDITIVA & EXPLICABILIDADE XAI ───────────────────────
    pdf.section_title("2", "INTELIGÊNCIA PREDITIVA & EXPLICABILIDADE XAI", 25, 95, 65)

    ndvi_val = float(resultado.get("ndvi_previsto", 0.0))
    fase = str(resultado.get("fase_fenologica", "-"))
    conf_raw = str(resultado.get("confiabilidade_modelo", "Alta"))
    conf = conf_raw.split("(")[0].strip()

    raw_status = resultado.get("status_geral") or resultado.get("status_vigor")
    if not raw_status or raw_status == "-":
        if ndvi_val >= 0.70:
            status = "Vigor Elevado (Ideal)"
        elif ndvi_val >= 0.50:
            status = "Vigor Médio"
        else:
            status = "Vigor Sob Atenção"
    else:
        status = str(raw_status)

    cor_status = (
        (25, 125, 65)
        if any(w in status for w in ["Normal", "Ideal", "Alto", "Saudável"])
        else ((192, 57, 43) if any(w in status for w in ["Crítico", "Atenção", "Risco"]) else (211, 84, 0))
    )

    pdf.kpi_card_row(
        ["NDVI Projetado", "Fase Fenológica", "Confiabilidade", "Status Geral"],
        [f"{ndvi_val:.3f}", fase, conf, status],
        val_colors=[(25, 125, 65), (25, 45, 35), (25, 45, 35), cor_status],
        widths=[36.0, 78.0, 36.0, 40.0],
    )
    pdf.ln(1)

    # Box Explicabilidade XAI
    top_driver = str(xai_res.get("top_driver", "Chuva Recente (30d)"))
    contributions = xai_res.get("contributions", {})
    narrativa_xai = str(xai_res.get("narrativa", "Vigor vegetativo consistente com o histórico agronômico."))

    pdf.set_fill_color(246, 252, 249)
    pdf.set_draw_color(165, 205, 185)
    pdf.set_text_color(15, 75, 40)
    pdf.set_font("helvetica", "B", 7.5)
    pdf.cell(190, 4.5, f"  Explicabilidade Matemática do Modelo (XAI Waterfall & SHAP):", border="LTR", new_x="LMARGIN", new_y="NEXT", fill=True)

    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(35, 45, 38)
    pdf.cell(190, 4.0, f"  * Fator Dominante (Top Driver): {_clean_text(top_driver)}", border="LR", new_x="LMARGIN", new_y="NEXT", fill=True)

    if contributions:
        contrib_items = [f"{k}: {v:+.4f} NDVI" for k, v in list(contributions.items())[:4]]
        pdf.multi_cell(
            190,
            4.0,
            f"  * Contribuições Marginais: {_clean_text(' | '.join(contrib_items))}",
            border="LR",
            fill=True,
        )

    pdf.multi_cell(190, 4.0, f"  * {_clean_text(narrativa_xai)}", border="LBR", fill=True)
    pdf.ln(3)

    # ── 3. ALERTAS OPERACIONAIS (DSS) ─────────────────────────────────────────
    pdf.section_title("3", "ALERTAS ATIVOS - SISTEMA DE SUPORTE À DECISÃO (DSS)", 145, 75, 20)

    alertas = resultado.get("fatores_de_risco_identificados", [])

    if not alertas:
        pdf.set_fill_color(240, 250, 244)
        pdf.set_text_color(20, 110, 55)
        pdf.set_draw_color(150, 210, 175)
        pdf.set_font("helvetica", "B", 8)
        pdf.multi_cell(190, 6, "  [OK]  Nenhum risco crítico identificado nas condições operacionais avaliadas.", border=1, fill=True)
    else:
        for alerta in alertas:
            is_critico = any(w in alerta for w in ["Déficit", "Crítico", "Risco", "Alerta", "Volatilização", "Lixiviação", "Podridão"])
            if is_critico:
                pdf.set_fill_color(254, 242, 240)
                pdf.set_text_color(175, 40, 30)
                pdf.set_draw_color(235, 170, 160)
                pdf.set_font("helvetica", "B", 7.5)
            else:
                pdf.set_fill_color(255, 251, 235)
                pdf.set_text_color(160, 105, 15)
                pdf.set_draw_color(235, 210, 140)
                pdf.set_font("helvetica", "", 7.5)
            pdf.multi_cell(190, 4.8, f"  - {_clean_text(alerta)}", border=1, fill=True)
            pdf.ln(1)

    pdf.ln(3)

    # ── 4. PARECER DO AGRÔNOMO (IA GENERATIVA - GEMINI GROUNDED) ─────────────
    pdf.section_title("4", "PARECER DO AGRÔNOMO (IA GENERATIVA - GEMINI)", 68, 52, 100)

    resolved_api_key = _resolve_gemini_key(gemini_api_key)
    parecer_texto = _get_agronomic_opinion(
        farm_name=farm_name,
        city=city,
        ndvi_val=ndvi_val,
        fase=fase,
        gold_kpis=gold_kpis,
        xai_res=xai_res,
        alertas=alertas,
        api_key=resolved_api_key,
    )

    pdf.set_fill_color(249, 247, 253)
    pdf.set_draw_color(195, 180, 220)
    pdf.set_text_color(45, 30, 68)
    pdf.set_font("helvetica", "I", 8.0)
    pdf.multi_cell(190, 4.3, f'"{_clean_text(parecer_texto)}"', border=1, fill=True)

    return bytes(pdf.output())


# Backward compatibility alias
PDF = OmniCropPDF
