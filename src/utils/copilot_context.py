"""
Utilitários de Construção de Contexto Dinâmico (Grounded RAG) e XAI
para o Assistente de Manejo Generativo (Google Gemini).
"""
import os
from datetime import datetime


def get_gemini_api_key(st_secrets=None, session_state=None) -> str | None:
    """
    Recupera a chave da API do Google Gemini com fallback hierárquico:
    1. st.secrets (secrets.toml)
    2. Variáveis de ambiente (os.environ)
    3. st.session_state (inserção manual do usuário na UI)
    """
    if st_secrets:
        try:
            if "GEMINI_API_KEY" in st_secrets:
                return st_secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key

    if session_state and isinstance(session_state, dict):
        return session_state.get("gemini_api_key")

    return None


def build_copilot_grounded_prompt(
    farm_cfg: dict,
    gold_kpis: dict,
    xai_res: dict,
    dss: dict,
    cenario_nome: str,
    ndvi_base: float,
    ndvi_proj: float,
    reference_date: str = None,
    current_month: int = None,
) -> str:
    """
    Constrói a instrução de sistema (System Instruction) do Google Gemini,
    injetando os dados mastigados da Camada Ouro (Gold KPIs) e a explicabilidade
    matemática do XAI (contribuições marginais e top driver), impedindo respostas
    genéricas e alinhando a IA estritamente à fisiologia da cana e à simulação ativa.
    """
    delta = round(ndvi_proj - ndvi_base, 3)
    delta_pct = round((delta / ndvi_base * 100), 1) if ndvi_base else 0.0

    hoje_str = reference_date or datetime.now().strftime("%d/%m/%Y")
    mes_atual = current_month or datetime.now().month

    fase_ciclo = (
        "Crescimento Vegetativo Intenso (Primavera/Verão)"
        if mes_atual in [11, 12, 1, 2, 3]
        else "Maturação / Acúmulo de ATR e Colheita (Outono/Inverno)"
    )

    balanco_hidrico = float(gold_kpis.get("balanco_hidrico_mm", 0.0))
    dias_sem_chuva = int(gold_kpis.get("dias_sem_chuva", 0))
    gda_total = float(gold_kpis.get("gda_total_acumulado", 0.0))
    risco_estresse = str(gold_kpis.get("risco_estresse_hidrico", "BAIXO"))
    recomendacao_gold = str(
        gold_kpis.get("recomendacao_manejo", "Condições hídricas favoráveis.")
    )
    chuva_total_w = float(gold_kpis.get("chuva_total_mm", 0.0))
    et0_total_w = float(gold_kpis.get("et0_total_mm", 0.0))
    temp_max_w = float(gold_kpis.get("temp_max_media_c", 0.0))
    temp_min_w = float(gold_kpis.get("temp_min_media_c", 0.0))
    amplitude_w = float(gold_kpis.get("amplitude_termica_media_c", 0.0))

    top_driver = xai_res.get("top_driver", "Chuva Recente (30d)")
    contributions = xai_res.get("contributions", {})
    xai_narrativa = xai_res.get("narrativa", "Vigor estável em relação ao baseline.")

    contribuicoes_str = "\n".join(
        [f"  - {k}: {v:+.4f} NDVI" for k, v in contributions.items()]
    )
    if not contribuicoes_str:
        contribuicoes_str = f"  - {top_driver}: {delta:+.4f} NDVI"

    dss_status = dss.get("status_title", "Análise Operacional")
    dss_msg = dss.get("mensagem_recomendacao", "Manter monitoramento de campo.")

    from src.core.crop_config import get_crop_parameters
    crop_ident = farm_cfg.get("crop_id") or farm_cfg.get("tipo_cultura", "sugarcane")
    crop_params = get_crop_parameters(crop_ident)
    crop_nome = crop_params.name

    crop_guidelines = {
        "sugarcane": "Cana-de-Açúcar: Em maturação, déficit hídrico controlado eleva o teor de sacarose (ATR); irrigar excessivamente dilui o caldo e prejudica a rentabilidade. Em crescimento vegetativo, o déficit hídrico reduz severamente a produtividade (TCH). Solo saturado por chuvas recentes ou previstas impede o tráfego, atola colhedoras e destrói as soqueiras por compactação e pisoteio.",
        "soybean": "Soja: Leguminosa C3 anual. Estresse hídrico na floração (R1-R2) e enchimento de grãos (R5-R6) provoca abortamento de flores/vagens. Solo com boa drenagem e inoculação com Bradyrhizobium são vitais.",
        "corn": "Milho: Gramínea C4 de alta exigência. Déficit hídrico no pendoamento e espigamento (VT-R1) causa perda irreversível de grãos. Alta resposta a nitrogênio em cobertura quando há umidade.",
        "coffee": "Café: Perene arbustivo. Florada (setembro/outubro) exige chuva para pegamento floral; granação dos frutos (dezembro a março) demanda água contínua. Inverno seco e frio favorece colheita uniforme.",
        "pasture": "Pecuária (Pastagem): Forrageiras tropicais (Brachiaria/Panicum). Estacionalidade estival marcada; águas exigem manejo de rotação de pastejo e ajuste de carga animal (UA/ha). Seca requer diferimento ou suplementação.",
    }
    guideline_especifica = crop_guidelines.get(crop_params.crop_id, crop_guidelines["sugarcane"])

    prompt = f"""Você é o OmniCrop AI, Consultor Sênior de Inteligência Agronômica e Fisiologia de {crop_nome}.
Você está atendendo o gestor/agrônomo da fazenda '{farm_cfg.get("farm_name", "Fazenda Modelo")}'.

=== DIRETRIZES FUNDAMENTAIS DE COMPORTAMENTO E RIGOR AGRONÔMICO ===
1. RESPOSTAS RIGOROSAMENTE GROUNDED: É terminantemente proibido fornecer respostas genéricas ou teóricas (ex: 'depende do clima', 'consulte seu agrônomo'). Você É o agrônomo sênior responsável. Você DEVE fundamentar cada recomendação citando os números exatos da Camada Ouro e a decomposição matemática do XAI:
   - Cultura Monitorada: {crop_nome} (Tb={crop_params.base_temp_celsius}°C, Kc={crop_params.kc_default})
   - Balanço Hídrico Líquido: {balanco_hidrico:+.1f} mm
   - Veranico: {dias_sem_chuva} dias sem chuva
   - Vigor Vegetativo NDVI: {ndvi_base:.3f} (atual) ➔ {ndvi_proj:.3f} (simulado no cenário {cenario_nome})
   - Decomposição XAI: Fator dominante '{top_driver}' com impacto direto na decisão do modelo.
2. DOMÍNIO TÉCNICO E FISIOLOGIA ({crop_nome.upper()}):
   - Ciclo Fenológico Atual: {fase_ciclo} (Mês {mes_atual}).
   - Particularidades da Cultura: {guideline_especifica}
   - Adubação de Cobertura: Ureia comum necessita de umidade imediata (>15mm) para incorporação; sem chuva há alta perda por volatilização de amônia. Chuvas extremas (>100mm) causam lixiviação grave de nitrato.
   - XAI & Modelagem: Explique ao produtor a lógica causal que o modelo Gradient Boosting utilizou ao correlacionar chuva acumulada e graus-dia com o índice de vigor.
3. FORMATO EXECUTIVO:
   - Responda em Markdown bem estruturado, com títulos em negrito e listas de tópicos concisas.
   - Conclua SEMPRE com um item em destaque: **🎯 Plano de Ação Imediato (Recomendação do Agrônomo)** contendo ações práticas e objetivas.

=== DADOS TELEMÉTRICOS DA FAZENDA ===
• Fazenda: {farm_cfg.get("farm_name", "Desconhecida")}
• Cultura Agrícola: {crop_nome} (Tb: {crop_params.base_temp_celsius}°C | Kc: {crop_params.kc_default})
• Localização: Latitude {farm_cfg.get("lat", -21.17):.4f}, Longitude {farm_cfg.get("lon", -47.81):.4f} ({farm_cfg.get("city", "SP")})
• Variedade / Cultivar: {farm_cfg.get("variedade", "Padrão")}
• Área Monitorada: {farm_cfg.get("area_ha", 120.0)} hectares
• Data de Referência: {hoje_str} | Mês: {mes_atual} | Fase: {fase_ciclo}

=== CAMADA OURO (DATA LAKE MEDALLION · KPIs EXECUTIVOS) ===
• Balanço Hídrico Líquido (Chuva - ET0): {balanco_hidrico:+.1f} mm (Chuva Total: {chuva_total_w:.1f} mm | ET0: {et0_total_w:.1f} mm)
• Dias Consecutivos Sem Chuva (Veranico): {dias_sem_chuva} dias
• Graus-Dia Acumulados (GDA base 18°C): {gda_total:.1f} °C
• Classificação de Risco de Estresse: {risco_estresse}
• Temperaturas na Janela: Máx Média {temp_max_w:.1f}°C | Mín Média {temp_min_w:.1f}°C | Amplitude Térmica {amplitude_w:.1f}°C
• Parecer Oficial da Camada Ouro: "{recomendacao_gold}"

=== SIMULAÇÃO ATIVA & JUSTIFICATIVAS MATEMÁTICAS (XAI / SHAP) ===
• Cenário em Análise: {cenario_nome}
• Vigor Vegetativo Atual (NDVI Baseline): {ndvi_base:.3f}
• Vigor Projetado pelo Modelo (NDVI Simulado): {ndvi_proj:.3f} (Variação: {delta:+.3f} ou {delta_pct:+.1f}%)
• Decomposição das Contribuições Marginais (XAI):
{contribuicoes_str}
• Top Driver de Decisão: '{top_driver}'
• Narrativa Matemática do Modelo: "{xai_narrativa}"
• Avaliação do Sistema Especialista (DSS): {dss_status} -> {dss_msg}

Assuma plenamente a persona de autoridade agronômica sênior do OmniCrop AI."""
    return prompt
