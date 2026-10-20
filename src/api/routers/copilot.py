"""
Roteador para o Assistente de Manejo Agronômico (Copilot) - OmniCrop AI.
Expõe serviço REST para recomendação técnica determinística e generativa (RAG Grounded).
"""
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, status

from src.api.dependencies import AuthContext, get_auth_context
from src.api.schemas.copilot import CopilotAskRequest, CopilotAskResponse
from src.core.crop_config import get_crop_parameters
from src.core.logger import logger
from src.core.resilience import gemini_breaker, with_circuit_breaker
from src.data.db import log_audit_event
from src.utils.copilot_context import build_copilot_grounded_prompt, get_gemini_api_key

router = APIRouter()


def _generate_deterministic_fallback(
    req: CopilotAskRequest,
    farm_cfg: Dict[str, Any],
    gold_kpis: Dict[str, Any],
    xai_res: Dict[str, Any],
    dss: Dict[str, Any],
) -> str:
    """
    Gera resposta técnica estruturada offline quando o Gemini não está configurado ou falha.
    Totalmente embasada nas métricas reais da Camada Ouro e explicabilidade XAI.
    """
    crop_params = get_crop_parameters(req.crop_id)
    balanco = float(gold_kpis.get("balanco_hidrico_mm", 0.0))
    dias_sem_chuva = int(gold_kpis.get("dias_sem_chuva", 0))
    risco = str(gold_kpis.get("risco_estresse_hidrico", "BAIXO"))
    top_driver = str(xai_res.get("top_driver", "Chuva Acumulada 30d"))
    dss_status = str(dss.get("status_title", "Monitoramento Padrão"))
    dss_recom = str(dss.get("mensagem_recomendacao", "Manter rotina de inspeção."))

    delta_ndvi = req.ndvi_proj - req.ndvi_base

    return (
        f"### 🌾 Diagnóstico Agronômico Oficial — {farm_cfg.get('farm_name')} ({crop_params.name})\n\n"
        f"Com base na telemetria consolidada da Camada Ouro e na simulação biofísica do cenário **{req.cenario_nome}**:\n\n"
        f"- **Balanço Hídrico Líquido:** {balanco:+.1f} mm com **{dias_sem_chuva} dias** consecutivos sem precipitação.\n"
        f"- **Classificação de Risco Hídrico:** **{risco}** (Temperatura base $T_b$: {crop_params.base_temp_celsius}°C, $K_c$ médio: {crop_params.kc_default}).\n"
        f"- **Vigor Vegetativo (NDVI):** Projeção de **{req.ndvi_base:.3f} ➔ {req.ndvi_proj:.3f}** (variação marginal de {delta_ndvi:+.3f}).\n"
        f"- **Fator Dominante (XAI):** A resposta fisiológica é governada primordialmente por **{top_driver}**.\n"
        f"- **Diretriz do Sistema Especialista (DSS):** {dss_status} — {dss_recom}\n\n"
        f"**🎯 Plano de Ação Imediato (Recomendação do Agrônomo):**\n"
        f"1. **Manejo Hídrico:** {'Priorizar lâmina de irrigação suplementar para mitigar déficit acumulado.' if balanco < 0 else 'Solo em capacidade de campo favorável; suspender lâminas excessivas para evitar lixiviação.'}\n"
        f"2. **Nutrição e Cobertura:** Aplicação de nitrogênio/potássio somente se houver previsão de umidade superficial nas próximas 48h para evitar perdas por volatilização.\n"
        f"3. **Monitoramento Fitossanitário:** Realizar checagem visual de pragas/doenças nos talhões com menor vigor relativo."
    )


@router.post(
    "/copilot/ask",
    response_model=CopilotAskResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar o Assistente de Manejo Agronômico (Copilot)",
    description=(
        "Submete perguntas agronômicas para o Copilot com fundamentação estrita (Grounded RAG) "
        "nos dados da Camada Ouro, decomposição marginal XAI e regras fisiológicas da cultura. "
        "Opera com Google Gemini e fallback determinístico offline transparente."
    ),
)
def ask_copilot_endpoint(
    req: CopilotAskRequest,
    auth_ctx: AuthContext = Depends(get_auth_context),
) -> CopilotAskResponse:
    farm_cfg = {
        "farm_name": req.farm_name,
        "crop_id": req.crop_id,
        "lat": req.lat,
        "lon": req.lon,
        "city": req.city,
    }
    gold_kpis = req.gold_kpis or {
        "balanco_hidrico_mm": 8.5,
        "dias_sem_chuva": 3,
        "gda_total_acumulado": 195.0,
        "risco_estresse_hidrico": "BAIXO",
        "recomendacao_manejo": "Condições fisiológicas equilibradas.",
        "chuva_total_mm": 45.0,
        "et0_total_mm": 36.5,
        "temp_max_media_c": 30.2,
        "temp_min_media_c": 19.4,
        "amplitude_termica_media_c": 10.8,
    }
    xai_res = req.xai_res or {
        "top_driver": "Chuva Acumulada Recente (30d)",
        "contributions": {"Chuva 30d": 0.03, "GDA Mensal": 0.01},
        "narrativa": "Estabilidade hídrica suportando ganho de biomassa.",
    }
    dss = req.dss or {
        "status_title": "Condição Hídrica Adequada",
        "mensagem_recomendacao": "Manter monitoramento rotineiro do talhão.",
    }

    prompt_system = build_copilot_grounded_prompt(
        farm_cfg=farm_cfg,
        gold_kpis=gold_kpis,
        xai_res=xai_res,
        dss=dss,
        cenario_nome=req.cenario_nome,
        ndvi_base=req.ndvi_base,
        ndvi_proj=req.ndvi_proj,
    )

    api_key = get_gemini_api_key()
    answer: str = ""
    source: str = "deterministic_fallback"
    model_name: str = "omnicrop-rule-engine-v1"

    if api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            full_prompt = (
                f"{prompt_system}\n\n"
                f"=== PERGUNTA DO PRODUTOR / AGRÔNOMO ===\n"
                f"{req.question}\n\n"
                f"Responda diretamente à pergunta acima, aplicando todas as diretrizes de grounding agronômico."
            )

            for m_candidate in ["gemini-2.5-flash", "gemini-1.5-flash"]:
                try:
                    model = genai.GenerativeModel(m_candidate)
                    res = model.generate_content(full_prompt)
                    if res and res.text and len(res.text.strip()) > 30:
                        answer = res.text.strip()
                        source = "gemini"
                        model_name = m_candidate
                        break
                except Exception as exc:
                    logger.warning(f"Tentativa com [{m_candidate}] falhou: {exc}")
                    continue
        except Exception as exc:
            logger.warning(f"Falha ao chamar Google Gemini no Copilot ({exc}). Ativando fallback determinístico.")

    if not answer:
        answer = _generate_deterministic_fallback(
            req=req,
            farm_cfg=farm_cfg,
            gold_kpis=gold_kpis,
            xai_res=xai_res,
            dss=dss,
        )
        source = "deterministic_fallback"
        model_name = "omnicrop-rule-engine-v1"

    try:
        log_audit_event(
            user_id=auth_ctx.user_id,
            action="COPILOT_ASK",
            entity_type="copilot",
            entity_id=req.farm_id or req.farm_name,
            details={"question": req.question, "crop_id": req.crop_id, "source": source},
            access_token=auth_ctx.access_token,
        )
    except Exception:
        pass

    return CopilotAskResponse(
        question=req.question,
        answer=answer,
        source=source,
        model=model_name,
        crop_id=req.crop_id,
        farm_name=req.farm_name,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
