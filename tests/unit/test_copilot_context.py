import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.copilot_context import build_copilot_grounded_prompt, get_gemini_api_key


def test_build_copilot_grounded_prompt_contains_gold_kpis():
    """Valida se a instrução de sistema injeta com precisão todos os KPIs da Camada Ouro."""
    farm_cfg = {
        "farm_name": "Fazenda Boa Vista Teste",
        "lat": -21.17,
        "lon": -47.81,
        "city": "Ribeirão Preto - SP",
        "variedade": "CTC-4",
        "area_ha": 350.0,
    }
    gold_kpis = {
        "balanco_hidrico_mm": -18.5,
        "dias_sem_chuva": 6,
        "gda_total_acumulado": 142.3,
        "risco_estresse_hidrico": "CRÍTICO",
        "recomendacao_manejo": "Alerta de Estresse Hídrico: avaliar irrigação imediata.",
        "chuva_total_mm": 5.0,
        "et0_total_mm": 23.5,
        "temp_max_media_c": 32.5,
        "temp_min_media_c": 19.0,
        "amplitude_termica_media_c": 13.5,
    }
    xai_res = {
        "top_driver": "Chuva Recente (30d)",
        "contributions": {
            "Chuva Recente (30d)": +0.045,
            "Soma Térmica (GDA)": -0.012,
        },
        "narrativa": "A elevação no vigor foi impulsionada por Chuva Recente.",
    }
    dss = {
        "status_title": "🔴 Risco Crítico",
        "mensagem_recomendacao": "Irrigação de salvamento recomendada para evitar perda de TCH.",
    }

    prompt = build_copilot_grounded_prompt(
        farm_cfg=farm_cfg,
        gold_kpis=gold_kpis,
        xai_res=xai_res,
        dss=dss,
        cenario_nome="Irrigação de Salvamento (+40 mm)",
        ndvi_base=0.520,
        ndvi_proj=0.585,
        reference_date="15/10/2026",
        current_month=10,
    )

    # Asserts de Presença e Rigor Técnico da Camada Ouro
    assert "Fazenda Boa Vista Teste" in prompt
    assert "-18.5 mm" in prompt
    assert "6 dias" in prompt
    assert "142.3 °C" in prompt
    assert "CRÍTICO" in prompt
    assert "Alerta de Estresse Hídrico: avaliar irrigação imediata." in prompt


def test_build_copilot_grounded_prompt_contains_xai_metrics():
    """Valida se as métricas matemáticas e contribuições do XAI / SHAP são injetadas no prompt."""
    farm_cfg = {"farm_name": "Fazenda Horizonte"}
    gold_kpis = {"balanco_hidrico_mm": 12.0, "risco_estresse_hidrico": "BAIXO"}
    xai_res = {
        "top_driver": "Soma Térmica (GDA)",
        "contributions": {
            "Soma Térmica (GDA)": +0.032,
            "Chuva Recente (30d)": +0.005,
        },
        "narrativa": "Impacto positivo dominante da temperatura.",
    }
    dss = {
        "status_title": "🟢 Normal",
        "mensagem_recomendacao": "Condições ideais de desenvolvimento.",
    }

    prompt = build_copilot_grounded_prompt(
        farm_cfg=farm_cfg,
        gold_kpis=gold_kpis,
        xai_res=xai_res,
        dss=dss,
        cenario_nome="Previsão Natural (15 dias futuros)",
        ndvi_base=0.610,
        ndvi_proj=0.647,
        current_month=2,
    )

    # Asserts do XAI e Simulação
    assert "0.610 (atual) ➔ 0.647" in prompt
    assert "Top Driver de Decisão: 'Soma Térmica (GDA)'" in prompt
    assert "+0.0320 NDVI" in prompt
    assert "Impacto positivo dominante da temperatura." in prompt
    assert "Crescimento Vegetativo Intenso (Primavera/Verão)" in prompt


def test_build_copilot_grounded_prompt_strict_agronomic_rules():
    """Valida se o prompt contém as diretrizes que proíbem respostas genéricas e orientam sobre ATR, TCH e compactação."""
    prompt = build_copilot_grounded_prompt(
        farm_cfg={},
        gold_kpis={},
        xai_res={},
        dss={},
        cenario_nome="Operação de Colheita",
        ndvi_base=0.45,
        ndvi_proj=0.45,
    )

    assert "RESPOSTAS RIGOROSAMENTE GROUNDED" in prompt
    assert "proibido fornecer respostas genéricas" in prompt
    assert "TCH" in prompt
    assert "ATR" in prompt
    assert "compactação e pisoteio" in prompt
    assert "volatilização de amônia" in prompt
    assert "Plano de Ação Imediato" in prompt


def test_get_gemini_api_key_hierarchy(monkeypatch):
    """Testa a precedência correta de recuperação de chave de API."""
    # 1. Sem nada
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert get_gemini_api_key({}, {}) is None

    # 2. Presente apenas em session_state
    assert get_gemini_api_key({}, {"gemini_api_key": "key_session_123"}) == "key_session_123"

    # 3. Presente em environ (tem precedência sobre session)
    monkeypatch.setenv("GEMINI_API_KEY", "key_env_456")
    assert get_gemini_api_key({}, {"gemini_api_key": "key_session_123"}) == "key_env_456"

    # 4. Presente em secrets (tem precedência máxima)
    secrets_dict = {"GEMINI_API_KEY": "key_secrets_789"}
    assert get_gemini_api_key(secrets_dict, {"gemini_api_key": "key_session_123"}) == "key_secrets_789"
