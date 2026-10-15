import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.styles import inject_css
from src.utils.farm_config import load_config, is_configured
from src.data.fetch_api import fetch_farm_data
from src.models.predict import (
    build_payload,
    get_prediction,
    explain_prediction_delta,
    plot_xai_waterfall,
    calcular_dss,
)
from src.data.ingest_azure import transform_to_gold, load_latest_gold_kpis
from components.header import render_sidebar, render_page_header
from src.utils.copilot_context import build_copilot_grounded_prompt, get_gemini_api_key

import google.generativeai as genai

st.set_page_config(
    page_title="Assistente de Manejo · OmniCrop AI",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "user" not in st.session_state or not st.session_state["user"]:
    st.session_state["show_landing"] = True
    st.switch_page("app.py")
    st.stop()

inject_css()

if not is_configured():
    st.warning("Fazenda não configurada. Conclua o Onboarding primeiro.")
    st.stop()

cfg = load_config() or {}


def render_copilot():
    # ── 1. Telemetria e Dados Vivos da Fazenda ────────────────────────
    with st.spinner("Sincronizando telemetria climática e Camada Ouro..."):
        df_live, today = fetch_farm_data(cfg["lat"], cfg["lon"])

    payload_hoje = build_payload(today)
    resultado_hoje = get_prediction(payload_hoje)

    render_sidebar(today, resultado_hoje)
    render_page_header(
        "Assistente de Manejo",
        "COPILOT AGRONÔMICO GENERATIVO · RAG GROUNDED EM DADOS OURO & XAI",
    )

    now = pd.Timestamp.now(tz="America/Sao_Paulo").normalize().tz_localize(None)
    df_past = df_live[df_live["date"] <= now]
    df_future = df_live[df_live["date"] > now].head(15)

    chuva_15d_futura = (
        float(df_future["precipitacao_total"].sum())
        if not df_future.empty and "precipitacao_total" in df_future.columns
        else 0.0
    )
    gda_15d_futuro = (
        float(df_future["gdd"].sum())
        if not df_future.empty and "gdd" in df_future.columns
        else 0.0
    )

    # ── 2. Camada Ouro (Gold KPIs Consolidados com Isolamento RLS) ────
    gold = {}
    farm_id = cfg.get("id")

    # 2.1 Tenta carregar do Supabase com proteção RLS por farm_id
    if farm_id:
        try:
            from src.data.db import get_latest_farm_gold_kpi
            gold = get_latest_farm_gold_kpi(farm_id) or {}
        except Exception:
            gold = {}

    # 2.2 Se não encontrar no banco, tenta carregar do Azure Blob Storage
    if not gold:
        try:
            gold_df = load_latest_gold_kpis()
            if gold_df is not None and not gold_df.empty:
                gold = gold_df.iloc[0].to_dict()
        except Exception:
            gold = {}

    # 2.3 Se ainda não tiver, calcula a partir dos dados refinados e persiste no Supabase
    if not gold:
        window_df = df_past.tail(14) if len(df_past) >= 14 else df_past
        gold_df = transform_to_gold(window_df)
        gold = gold_df.iloc[0].to_dict() if not gold_df.empty else {}
        if farm_id and gold:
            try:
                from src.data.db import insert_farm_gold_kpis
                insert_farm_gold_kpis(farm_id, gold)
            except Exception:
                pass

    balanco_hidrico = float(gold.get("balanco_hidrico_mm", 0.0))
    dias_sem_chuva = int(gold.get("dias_sem_chuva", 0))
    gda_total = float(gold.get("gda_total_acumulado", 0.0))
    risco_estresse = str(gold.get("risco_estresse_hidrico", "BAIXO"))
    recomendacao_gold = str(
        gold.get("recomendacao_manejo", "Condições hídricas favoráveis.")
    )
    chuva_total_w = float(gold.get("chuva_total_mm", 0.0))
    et0_total_w = float(gold.get("et0_total_mm", 0.0))
    temp_max_w = float(gold.get("temp_max_media_c", 0.0))
    temp_min_w = float(gold.get("temp_min_media_c", 0.0))
    amplitude_w = float(gold.get("amplitude_termica_media_c", 0.0))

    # ── 3. Seletor de Cenário e Decomposição Matemática XAI ───────────
    sim_salva = st.session_state.get("ultima_simulacao")

    opcoes_cenario = []
    if sim_salva:
        opcoes_cenario.append(
            f"✨ Última Simulação ({sim_salva.get('cenario', 'Personalizada')})"
        )
    opcoes_cenario.extend([
        "⛅ Previsão Natural (15 dias futuros)",
        "💧 Irrigação de Salvamento (+40 mm)",
        "🌿 Aplicação de Maturador Químico",
        "🌱 Adubação de Cobertura (+Nitrato)",
        "🚜 Janela Operacional de Colheita",
    ])

    cenario_selecionado = st.selectbox(
        "🎯 Cenário Agronômico para Grounding da IA:",
        opcoes_cenario,
        index=0,
        help="O assistente analisa e fundamenta as recomendações nas métricas exatas deste cenário.",
    )

    mes_atual = (
        today["date"].month
        if hasattr(today.get("date", ""), "month")
        else datetime.now().month
    )

    if cenario_selecionado.startswith("✨ Última Simulação") and sim_salva:
        payload_sim = sim_salva["payload_sim"]
        resultado_sim = sim_salva["resultado_sim"]
        xai_res = sim_salva["xai"]
        dss = sim_salva["dss"]
        cenario_nome = sim_salva.get("cenario", "Simulação Customizada")
    elif "Irrigação" in cenario_selecionado:
        vol_total = 40.0
        payload_sim = payload_hoje.copy()
        payload_sim["chuva_acumulada_30d"] = float(
            today.get("chuva_acumulada_30d", 0) + chuva_15d_futura + vol_total
        )
        payload_sim["GDA_mensal"] = float(
            today.get("GDA_mensal", 0) + gda_15d_futuro
        )
        resultado_sim = get_prediction(payload_sim)
        xai_res = explain_prediction_delta(payload_hoje, payload_sim)
        dss = calcular_dss(
            mes_atual,
            resultado_hoje["ndvi_previsto"],
            resultado_sim["ndvi_previsto"],
            cenario="Irrigação",
            chuva_projetada=chuva_15d_futura + vol_total,
            gda_projetado=gda_15d_futuro,
        )
        cenario_nome = "Irrigação de Salvamento (+40 mm)"
    elif "Maturador" in cenario_selecionado:
        dose_mat = 50.0
        payload_sim = payload_hoje.copy()
        payload_sim["chuva_acumulada_30d"] = float(
            today.get("chuva_acumulada_30d", 0) + chuva_15d_futura
        ) * (1 - (dose_mat / 150))
        payload_sim["GDA_mensal"] = float(
            today.get("GDA_mensal", 0) + gda_15d_futuro + (dose_mat * 1.5)
        )
        resultado_sim = get_prediction(payload_sim)
        xai_res = explain_prediction_delta(payload_hoje, payload_sim)
        dss = calcular_dss(
            mes_atual,
            resultado_hoje["ndvi_previsto"],
            resultado_sim["ndvi_previsto"],
            cenario="Maturador",
            chuva_projetada=chuva_15d_futura,
            gda_projetado=gda_15d_futuro,
        )
        cenario_nome = "Aplicação de Maturador Químico (50 L/ha)"
    elif "Adubação" in cenario_selecionado:
        payload_sim = payload_hoje.copy()
        payload_sim["chuva_acumulada_30d"] = float(
            today.get("chuva_acumulada_30d", 0) + chuva_15d_futura
        )
        payload_sim["GDA_mensal"] = float(
            today.get("GDA_mensal", 0) + gda_15d_futuro
        )
        resultado_sim = get_prediction(payload_sim)
        if resultado_sim:
            resultado_sim["ndvi_previsto"] = min(
                0.95, resultado_sim["ndvi_previsto"] + 0.08
            )
        xai_res = explain_prediction_delta(payload_hoje, payload_sim)
        dss = calcular_dss(
            mes_atual,
            resultado_hoje["ndvi_previsto"],
            resultado_sim["ndvi_previsto"],
            cenario="Adubação - Nitrato",
            chuva_projetada=chuva_15d_futura,
            gda_projetado=gda_15d_futuro,
        )
        cenario_nome = "Adubação Nitrogenada em Cobertura (Nitrato)"
    elif "Colheita" in cenario_selecionado:
        payload_sim = payload_hoje.copy()
        payload_sim["chuva_acumulada_30d"] = float(
            today.get("chuva_acumulada_30d", 0) + chuva_15d_futura
        )
        payload_sim["GDA_mensal"] = float(
            today.get("GDA_mensal", 0) + gda_15d_futuro
        )
        resultado_sim = get_prediction(payload_sim)
        xai_res = explain_prediction_delta(payload_hoje, payload_sim)
        dss = calcular_dss(
            mes_atual,
            resultado_hoje["ndvi_previsto"],
            resultado_sim["ndvi_previsto"],
            cenario="Operação de Colheita",
            chuva_projetada=chuva_15d_futura,
            gda_projetado=gda_15d_futuro,
        )
        cenario_nome = "Janela Operacional de Colheita"
    else:
        # Previsão Natural 15 dias
        payload_sim = payload_hoje.copy()
        payload_sim["chuva_acumulada_30d"] = float(
            today.get("chuva_acumulada_30d", 0) + chuva_15d_futura
        )
        payload_sim["GDA_mensal"] = float(
            today.get("GDA_mensal", 0) + gda_15d_futuro
        )
        resultado_sim = get_prediction(payload_sim)
        xai_res = explain_prediction_delta(payload_hoje, payload_sim)
        dss = calcular_dss(
            mes_atual,
            resultado_hoje["ndvi_previsto"],
            resultado_sim["ndvi_previsto"],
            cenario="Previsão Natural",
            chuva_projetada=chuva_15d_futura,
            gda_projetado=gda_15d_futuro,
        )
        cenario_nome = "Previsão Natural (15 dias futuros)"

    ndvi_base = float(resultado_hoje.get("ndvi_previsto", 0.0))
    ndvi_proj = float(resultado_sim.get("ndvi_previsto", 0.0))
    delta = ndvi_proj - ndvi_base
    delta_pct = (delta / ndvi_base * 100) if ndvi_base else 0.0
    top_driver = xai_res.get("top_driver", "Chuva Recente (30d)")
    contributions = xai_res.get("contributions", {})
    xai_narrativa = xai_res.get("narrativa", "")

    # ── 4. Cockpit Visual de Métricas (Camada Ouro) ───────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c_m1, c_m2, c_m3, c_m4 = st.columns(4)

    with c_m1:
        delta_color = "normal" if balanco_hidrico >= 0 else "inverse"
        st.metric(
            "Balanço Hídrico Líquido",
            f"{balanco_hidrico:+.1f} mm",
            delta=f"{'Superávit' if balanco_hidrico >= 0 else 'Déficit'} Hídrico",
            delta_color=delta_color,
            help="Chuva Total menos Demanda Evapotranspirativa (ET0 FAO) na janela monitorada.",
        )

    with c_m2:
        st.metric(
            "Dias Sem Chuva (Veranico)",
            f"{dias_sem_chuva} dias",
            delta="Risco de Seca" if dias_sem_chuva >= 5 else "Normal",
            delta_color="inverse" if dias_sem_chuva >= 5 else "off",
            help="Dias consecutivos com precipitação inferior a 1.0 mm.",
        )

    with c_m3:
        st.metric(
            "GDA Acumulado (18°C)",
            f"{gda_total:.1f} °C",
            delta="Soma Térmica",
            delta_color="off",
            help="Graus-Dia Acumulados acima da temperatura basal da cana (18°C).",
        )

    with c_m4:
        badge_color = (
            "#EF5350"
            if risco_estresse == "CRÍTICO"
            else "#FFD600"
            if risco_estresse == "MODERADO"
            else "#69F0AE"
        )
        st.markdown(
            f"""
        <div data-testid="metric-container" style="padding:14px !important;">
            <div data-testid="stMetricLabel">Risco de Estresse Hídrico</div>
            <div style="font-size:22px; font-weight:700; color:{badge_color}; margin-top:2px;">
                {risco_estresse}
            </div>
            <div style="font-size:11px; color:#94A3B8; margin-top:4px;">
                Vigor: <b>{ndvi_base:.3f}</b> ➔ <b>{ndvi_proj:.3f}</b> ({delta_pct:+.1f}%)
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Banner de Contexto Grounded Ativo
    st.markdown(
        f"""
    <div style="background:rgba(20,40,25,0.65); border:1px solid rgba(105,240,174,0.25); border-radius:12px; padding:12px 18px; margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <span style="font-size:11px; text-transform:uppercase; letter-spacing:0.08em; color:#69F0AE; font-weight:700;">
                    🌱 Contexto Grounded Ativo:
                </span>
                <span style="color:#FFF; font-weight:600; font-size:13px; margin-left:6px;">{cenario_nome}</span>
            </div>
            <div style="font-size:12px; color:#CBD5E1;">
                🎯 <b>Vigor Simulado:</b> {ndvi_base:.3f} ➔ <b>{ndvi_proj:.3f}</b> ({delta:+.3f}) | 🔍 <b>Top Driver XAI:</b> <span style="color:#69F0AE; font-weight:600;">{top_driver}</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── 5. Auditoria de Dados e XAI Waterfall (Transparência) ─────────
    with st.expander(
        "🔍 Transparência de Dados e Decomposição Matemática XAI (Auditoria de Grounding)",
        expanded=False,
    ):
        x_col1, x_col2 = st.columns([1.2, 0.8], gap="medium")
        with x_col1:
            st.caption(f"**Interpretabilidade XAI:** {xai_narrativa}")
            fig_waterfall = plot_xai_waterfall(xai_res)
            st.plotly_chart(
                fig_waterfall,
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with x_col2:
            st.markdown("**📊 Telemetria da Camada Ouro (Gold KPIs):**")
            st.write({
                "Balanço Hídrico Líquido": f"{balanco_hidrico:+.1f} mm",
                "Chuva Total (Janela)": f"{chuva_total_w:.1f} mm",
                "Evapotranspiração ET0": f"{et0_total_w:.1f} mm",
                "Dias Sem Chuva": f"{dias_sem_chuva} dias",
                "GDA Acumulado": f"{gda_total:.1f} °C",
                "Amplitude Térmica": f"{amplitude_w:.1f} °C",
                "Diretriz Oficial DSS": dss.get("status_title", ""),
            })
            st.info(
                f"💡 **Recomendação DSS:** {dss.get('mensagem_recomendacao', '')}"
            )

    # ── 6. Montagem do Contexto Oculto (RAG Grounded Prompt) ──────────
    hoje_ref = today.get("date", datetime.now().date())
    hoje_str = (
        hoje_ref.strftime("%d/%m/%Y")
        if hasattr(hoje_ref, "strftime")
        else str(hoje_ref)
    )

    contexto_oculto = build_copilot_grounded_prompt(
        farm_cfg=cfg,
        gold_kpis=gold,
        xai_res=xai_res,
        dss=dss,
        cenario_nome=cenario_nome,
        ndvi_base=ndvi_base,
        ndvi_proj=ndvi_proj,
        reference_date=hoje_str,
        current_month=mes_atual,
    )

    # ── 7. Sugestões Rápidas de Perguntas (Grounding Pills) ───────────
    st.markdown(
        '<div class="sec-header">Sugestões de Análise Técnica (Quick Prompt Chips)</div>',
        unsafe_allow_html=True,
    )
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    p1 = f"💧 Com balanço de {balanco_hidrico:+.1f} mm e {dias_sem_chuva}d de veranico, devo irrigar?"
    p2 = f"🔍 Explique o impacto do '{top_driver}' no NDVI ({delta:+.3f})"
    p3 = f"🚜 As condições de solo e chuva permitem a colheita agora?"
    p4 = f"📋 Faça um diagnóstico agronômico executivo completo da fazenda"

    prompt_acionado = None
    with p_col1:
        if st.button(p1, key="chip_p1", use_container_width=True):
            prompt_acionado = p1
    with p_col2:
        if st.button(p2, key="chip_p2", use_container_width=True):
            prompt_acionado = p2
    with p_col3:
        if st.button(p3, key="chip_p3", use_container_width=True):
            prompt_acionado = p3
    with p_col4:
        if st.button(p4, key="chip_p4", use_container_width=True):
            prompt_acionado = p4

    # ── 8. Histórico de Conversação ───────────────────────────────────
    if "mensagens_chat" not in st.session_state:
        st.session_state["mensagens_chat"] = [{
            "role": "assistant",
            "content": f"Olá! Sou o **OmniCrop AI**, seu consultor agronômico sênior. Conectei a telemetria da fazenda **{cfg.get('farm_name', 'sua fazenda')}** com a Camada Ouro e os modelos preditivos.\n\n"
            f"📊 **Telemetria de Campo:** Balanço Hídrico de **{balanco_hidrico:+.1f} mm** com **{dias_sem_chuva} dias sem chuva** (Risco de Estresse: **{risco_estresse}**).\n"
            f"🌾 **Vigor Vegetativo (NDVI):** Atual de **{ndvi_base:.3f}** com projeção de **{ndvi_proj:.3f}** ({delta_pct:+.1f}%) no cenário *{cenario_nome}*.\n\n"
            f"Qual decisão de manejo você deseja avaliar hoje? Selecione um dos botões acima ou faça sua pergunta!",
        }]

    # Renderiza mensagens anteriores
    for msg in st.session_state["mensagens_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── 9. Gestão de Chave e Processamento de IA ──────────────────────
    api_key = get_gemini_api_key()

    if not api_key:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            "🔑 **Google Gemini API Key não detectada:** Você pode inserir sua chave temporária abaixo para ativar o streaming do modelo `gemini-3.6-flash`, ou usar a análise autônoma grounded."
        )
        c_k1, c_k2 = st.columns([3, 1])
        with c_k1:
            input_key = st.text_input(
                "Gemini API Key:",
                type="password",
                key="gemini_key_input",
                placeholder="Cole sua chave AIzaSy...",
                label_visibility="collapsed",
            )
        with c_k2:
            if st.button("Ativar Chave", use_container_width=True):
                if input_key.strip():
                    st.session_state["gemini_api_key"] = input_key.strip()
                    st.rerun()

    # Input do Usuário (Chat Input ou Chip selecionado)
    user_input = prompt_acionado or st.chat_input(
        "Pergunte ao OmniCrop AI sobre irrigação, colheita, adubação ou XAI..."
    )

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state["mensagens_chat"].append({
            "role": "user",
            "content": user_input,
        })

        with st.chat_message("assistant"):
            if not api_key:
                # Resposta Grounded Autônoma via DSS + XAI se a API do Gemini não tiver chave
                resposta_offline = (
                    f"### 🌾 Diagnóstico Técnico Grounded · OmniCrop AI\n\n"
                    f"**1. Análise Hídrica (Camada Ouro):**\n"
                    f"- Balanço Hídrico Líquido: **{balanco_hidrico:+.1f} mm** ({'Déficit' if balanco_hidrico < 0 else 'Superávit'})\n"
                    f"- Veranico Atual: **{dias_sem_chuva} dias consecutivos** sem precipitação significativa.\n"
                    f"- Risco Operacional: **{risco_estresse}** — *{recomendacao_gold}*\n\n"
                    f"**2. Decomposição de Vigor & Interpretabilidade (XAI):**\n"
                    f"- Vigor Atual (NDVI): **{ndvi_base:.3f}** ➔ Projetado: **{ndvi_proj:.3f}** ({delta:+.3f} / {delta_pct:+.1f}%)\n"
                    f"- Fator Dominante: **{top_driver}** impulsionou a decisão do algoritmo.\n"
                    f"- Justificativa Matemática: *{xai_narrativa}*\n\n"
                    f"**3. Parecer do Sistema Especialista (DSS):**\n"
                    f"- **{dss.get('status_title', 'Status')}**: {dss.get('mensagem_recomendacao', '')}\n\n"
                    f"**🎯 Plano de Ação Imediato (Recomendação do Agrônomo):**\n"
                    f"- Monitorar o ponto de murcha permanente do solo nas próximas 48h.\n"
                    f"- Adequar a escala de maquinário e defensivos à janela termohídrica ({temp_max_w:.1f}°C de máx).\n\n"
                    f"*(Dica: Insira sua Google Gemini API Key acima para dialogar livremente e em tempo real com o modelo 3.6 Flash.)*"
                )
                st.markdown(resposta_offline)
                st.session_state["mensagens_chat"].append({
                    "role": "assistant",
                    "content": resposta_offline,
                })
            else:
                with st.spinner(
                    "Consultando base de conhecimento agronômico e telemetria Ouro..."
                ):
                    try:
                        genai.configure(api_key=api_key)

                        # Suporte a modelos modernos com fallback resiliente
                        model_candidates = [
                            "gemini-3.6-flash",
                            "gemini-2.5-flash",
                            "gemini-1.5-flash",
                        ]
                        chat_session = None

                        for m_cand in model_candidates:
                            try:
                                model = genai.GenerativeModel(
                                    m_cand, system_instruction=contexto_oculto
                                )
                                chat_session = model.start_chat(history=[])
                                break
                            except Exception:
                                continue

                        if chat_session is None:
                            model = genai.GenerativeModel(
                                "gemini-1.5-flash",
                                system_instruction=contexto_oculto,
                            )
                            chat_session = model.start_chat(history=[])

                        response = chat_session.send_message(
                            user_input, stream=True
                        )

                        def parse_stream():
                            for chunk in response:
                                if chunk.text:
                                    yield chunk.text

                        try:
                            resposta_texto = st.write_stream(parse_stream())
                        except ValueError:
                            resposta_texto = (
                                "⚠️ A resposta foi restrita pelos filtros de segurança da API. "
                                "Por favor, reformule sua solicitação para mantê-la focada em práticas agronômicas."
                            )
                            st.markdown(resposta_texto)

                        st.session_state["mensagens_chat"].append({
                            "role": "assistant",
                            "content": resposta_texto,
                        })

                    except Exception as e:
                        err_msg = str(e)
                        st.error(f"Erro na comunicação com a API Google: {err_msg}")
                        st.session_state["mensagens_chat"].append({
                            "role": "assistant",
                            "content": f"Erro de comunicação com a IA: {err_msg}",
                        })

    # ── 10. Ações Adicionais ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c_spc, c_clr = st.columns([5, 1])
    with c_clr:
        if st.button("🗑️ Limpar Chat", use_container_width=True):
            st.session_state["mensagens_chat"] = []
            st.rerun()


render_copilot()
