"""Simulator — Página 2: Simulador de Intervenções com dados reais."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.styles import inject_css
from components.farm_config import load_config, is_configured
from components.live_data import fetch_farm_data
from components.api_client import build_payload, get_prediction, badge_html, calcular_dss
from components.charts import ndvi_gauge
from components.header import render_sidebar, render_page_header

st.set_page_config(page_title="Simulador · OmniCrop AI", page_icon="🌾", layout="wide",
                   initial_sidebar_state="expanded")

inject_css()

if 'user' not in st.session_state or not st.session_state['user']:
    st.info("A sua sessão expirou. Faça login novamente para acessar o sistema.")
    st.page_link("app.py", label="Ir para Login 🔒")
    st.stop()


if not is_configured():
    render_sidebar({}, None)
    st.info("Configure a localizacao da sua fazenda em Settings para usar o Simulator.")
    st.stop()

cfg = load_config()
with st.spinner("Carregando dados reais..."):
    df, today = fetch_farm_data(cfg["lat"], cfg["lon"])

payload_hoje = build_payload(today)
resultado_hoje = get_prediction(payload_hoje)

render_sidebar(today, resultado_hoje)
render_page_header("Simulator", "SIMULADOR DE INTERVENÇÕES · ANÁLISE WHAT-IF")

st.markdown(
    "<div style='color:rgba(180,230,180,.55);font-size:13px;margin-bottom:24px;'>"
    f"Baseline: dados reais de hoje ({today['date'].strftime('%d/%m/%Y') if hasattr(today.get('date', ''), 'strftime') else str(today.get('date',''))}) "
    f"em {cfg.get('farm_name','sua fazenda')}. Ajuste os parâmetros para projetar o impacto de uma intervenção."
    "</div>", unsafe_allow_html=True)

cenario = st.radio("Cenário de Intervenção:",
                   ["Planejamento de Plantio", "Irrigação de Salvamento", "Aplicação de Adubação", "Maturador Químico", "Operação de Colheita"],
                   horizontal=True)
cenario_dss = cenario

import pandas as pd
now = pd.Timestamp.now(tz="America/Sao_Paulo").normalize().tz_localize(None)
df_future = df[df["date"] > now].head(15)
chuva_15d_futura = df_future["precipitacao_total"].sum() if not df_future.empty else 0
gda_15d_futuro = df_future["gdd"].sum() if "gdd" in df_future.columns and not df_future.empty else 0

st.markdown("<br>", unsafe_allow_html=True)
col_ctrl, col_out = st.columns([1, 1], gap="large")
payload_sim = payload_hoje.copy()

with col_ctrl:
    st.markdown('<div class="sec-header">Parâmetros da Simulação</div>', unsafe_allow_html=True)
    st.info(f"⛅ **Previsão Real (Próximos 15 dias):**\n- **Chuva Esperada:** {chuva_15d_futura:.1f} mm\n- **Calor (GDA) Esperado:** {gda_15d_futuro:.1f}")
    st.markdown("<br>", unsafe_allow_html=True)

    if "Plantio" in cenario:
        st.write("Decisão: Aplicar irrigação de salvamento no plantio ou confiar na chuva?")
        irrigacao = st.slider("Irrigação no Sulco de Plantio", 0, 100, 0, format="%d mm")
        # Soma a chuva passada + chuva futura + irrigação humana
        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + chuva_15d_futura + irrigacao)
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + gda_15d_futuro)
        
    elif "Irrigação" in cenario:
        lame    = st.slider("Lâmina de Irrigação (Pivô/Gotejo)", 0, 100, 40, format="%d mm/dia", help="Milimetros de água aplicados no campo por dia")
        duracao = st.slider("Duração do Programa", 1, 30, 10, format="%d dias")
        vol_total = lame * duracao
        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + chuva_15d_futura + vol_total)
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + gda_15d_futuro)
        st.caption(f"Água Total Projetada (Chuva + Irrigação): **{chuva_15d_futura + vol_total:.0f} mm**")
        
        custo_por_mm_ha = 5.00
        custo_total = vol_total * custo_por_mm_ha
        st.caption(f'Custo Estimado de Energia/Bombeamento: **R$ {custo_total:,.2f} / hectare**')

    elif "Adubação" in cenario:
        st.write("Decisão: Qual fertilizante aplicar considerando a chuva prevista?")
        eficiencia = st.selectbox("Qualidade e Tipo do Fertilizante", ["Ureia Comum", "Ureia Protegida (Polímero)", "Nitrato (Alta Absorção)"])
        dose = st.slider("Dose de Aplicação", 0, 500, 200, format="%d kg/ha", help="Quantidade de fertilizante aplicado por hectare.")
        cenario_dss = f"Adubação - {eficiencia}" 
        
        preco_kg = 3.50
        bonus_ndvi = 0
        if "Comum" in eficiencia:
            preco_kg = 3.00
            if chuva_15d_futura > 15:
                bonus_ndvi = 0.05 * (dose / 200)
        elif "Protegida" in eficiencia:
            preco_kg = 4.50
            bonus_ndvi = 0.08 * (dose / 200)
        elif "Nitrato" in eficiencia:
            preco_kg = 5.50
            bonus_ndvi = 0.12 * (dose / 200)
            
        custo_adubacao = dose * preco_kg
        st.caption(f"💰 Custo Estimado do Fertilizante: **R$ {custo_adubacao:,.2f} / hectare**")
            
        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + chuva_15d_futura)
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + gda_15d_futuro)
        
    elif "Maturador" in cenario:
        st.write("Decisão: Qual a dose de maturador químico para forçar a secagem e acúmulo de sacarose?")
        dose_mat = st.slider("Dose de Maturador", 0, 100, 50, format="%d L/ha")
        # Maturador corta o vigor vegetativo. A dose simula estresse hídrico artificial e aumento de temperatura.
        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + chuva_15d_futura) * (1 - (dose_mat/150))
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + gda_15d_futuro + (dose_mat * 1.5))
        
        custo_mat = dose_mat * 4.20
        st.caption(f"💰 Custo Estimado do Defensivo + Aplicação Aérea: **R$ {custo_mat:,.2f} / hectare**")

    elif "Colheita" in cenario:
        st.write("Decisão: Qual o melhor dia para agendar a frente de colheita?")
        st.info("🚜 A colheita requer solo seco para evitar atolamento de maquinário e compactação. O assistente avalia a previsão diária (próximos 15 dias) em busca de janelas contínuas de seca.")
        
        best_day = None
        consecutive_dry = 0
        for idx, row in df_future.iterrows():
            if row["precipitacao_total"] < 2.0:
                consecutive_dry += 1
                if consecutive_dry >= 3:
                    best_day = row["date"] - pd.Timedelta(days=2)
                    break
            else:
                consecutive_dry = 0
                
        if best_day:
            st.success(f"📅 **Janela Ideal Identificada:** Agende o corte para **{best_day.strftime('%d/%m/%Y')}** (previsão de 3+ dias consecutivos de solo seco).")
        else:
            st.error("⛈️ **Sem Janela Segura:** Chuvas frequentes nos próximos 15 dias impossibilitam a trafegabilidade. Não coloque máquinas no campo!")

        payload_sim["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + chuva_15d_futura)
        payload_sim["GDA_mensal"] = float(today.get("GDA_mensal", 0) + gda_15d_futuro)

with col_out:
    st.markdown('<div class="sec-header">Projeção Pós-Intervenção</div>', unsafe_allow_html=True)
    resultado_sim = get_prediction(payload_sim)

    if resultado_sim and resultado_hoje:
        ndvi_base = resultado_hoje["ndvi_previsto"]
        ndvi_proj = resultado_sim["ndvi_previsto"]
        
        bonus_ndvi_val = 0
        if "Adubação" in cenario:
            # We assume bonus_ndvi was defined in the Adubação block
            try:
                bonus_ndvi_val = bonus_ndvi
            except NameError:
                bonus_ndvi_val = 0
            ndvi_proj = min(0.95, ndvi_proj + bonus_ndvi_val)
            
        delta     = ndvi_proj - ndvi_base
        delta_pct = (delta / ndvi_base * 100) if ndvi_base else 0

        gc1, gc2 = st.columns(2)
        with gc1:
            st.plotly_chart(ndvi_gauge(ndvi_base, "NDVI Atual"),
                            use_container_width=True, config={"displayModeBar": False})
            st.markdown("<div style='text-align:center;font-size:10px;color:rgba(180,230,180,.45);'>BASELINE REAL</div>",
                        unsafe_allow_html=True)
        with gc2:
            st.plotly_chart(ndvi_gauge(ndvi_proj, "NDVI Projetado"),
                            use_container_width=True, config={"displayModeBar": False})
            arrow = "▲" if delta > 0 else "▼"
            color = "#69F0AE" if delta > 0 else "#EF5350"
            st.markdown(
                f"<div style='text-align:center;color:{color};font-size:20px;font-weight:700;'>"
                f"{arrow} {abs(delta):.3f} ({abs(delta_pct):.1f}%)</div>",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        mes_atual = today["date"].month if hasattr(today.get("date", ""), "month") else 8
        
        # Calcular apenas a chuva futura projetada para as regras do DSS
        chuva_futura_DSS = chuva_15d_futura
        if "Irrigação" in cenario: chuva_futura_DSS += vol_total
        elif "Plantio" in cenario: chuva_futura_DSS += irrigacao
            
        dss = calcular_dss(mes_atual, ndvi_base, ndvi_proj, cenario=cenario_dss, chuva_projetada=chuva_futura_DSS, gda_projetado=gda_15d_futuro)
        
        if "Maturador" in cenario:
            if delta < 0:
                st.success(f"Maturador eficiente — redução esperada de {abs(delta_pct):.1f}% no vigor foliar (força acúmulo de ATR).")
            else:
                st.warning(f"Atenção — Vigor aumentou {abs(delta_pct):.1f}%. A dose pode ser insuficiente ou o clima está favorável demais ao crescimento vegetativo.")
        elif "Colheita" in cenario:
            st.info("NDVI projetado inalterado pela simulação. Avalie apenas a recomendação logística abaixo.")
        elif "Plantio" in cenario and ndvi_base < 0.25:
            st.info(f"Solo exposto (NDVI={ndvi_base:.3f}). Variação de {abs(delta_pct):.1f}% inicial é normal durante a brotação.")
        else:
            if delta > 0:
                st.success(f"Intervenção benéfica — melhora de {abs(delta_pct):.1f}% no vigor.")
            elif delta < 0:
                st.error(f"Cenário crítico — queda de {abs(delta_pct):.1f}% no vigor.")
            
        st.info(f"**Ação Recomendada ({dss['status_title']}):**  \n{dss['mensagem_recomendacao']}")
        if "Plantio" in cenario or "Irrigação" in cenario:
            best_ndvi = -1
            best_irr = 0
            for irr_test in range(0, 151, 5):
                test_payload = payload_hoje.copy()
                test_payload["chuva_acumulada_30d"] = float(today.get("chuva_acumulada_30d", 0) + chuva_15d_futura + irr_test)
                test_payload["GDA_mensal"] = float(today.get("GDA_mensal", 0) + gda_15d_futuro)
                res_test = get_prediction(test_payload)
                if res_test:
                    if (res_test["ndvi_previsto"] - best_ndvi) > 0.001:
                        best_ndvi = res_test["ndvi_previsto"]
                        best_irr = irr_test
            
            st.markdown("<br>", unsafe_allow_html=True)
            if best_irr > 0:
                st.markdown(f"<div style='padding:15px; border-radius:8px; border:1px solid #4CAF50; background:rgba(76,175,80,0.1); color:#A5D6A7;'>"
                            f"💡 <b>Ponto Ótimo de Irrigação (IA):</b> Para maximizar o vigor e evitar desperdício de bombeamento, aplique exatamente <b>{best_irr} mm</b> (teto alcançável: NDVI {best_ndvi:.3f})."
                            f"</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding:15px; border-radius:8px; border:1px solid #4CAF50; background:rgba(76,175,80,0.1); color:#A5D6A7;'>"
                            f"💡 <b>Ponto Ótimo de Irrigação (IA):</b> Economize energia! A chuva natural projetada já atinge o teto máximo de vigor para os próximos 15 dias (NDVI {best_ndvi:.3f}). Nenhuma irrigação adicional é recomendada."
                            f"</div>", unsafe_allow_html=True)

        
        if "Irrigação" in cenario and payload_sim["chuva_acumulada_30d"] > 250:
            st.error("⚠️ **Risco de Alagamento (Waterlogging)**: Volume excessivo de água pode causar sufocamento radicular e queda brusca de vigor.")
    else:
        st.error("Erro na projeção local.")
