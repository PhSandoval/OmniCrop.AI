import os
import sys
from pathlib import Path
import pytest
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.reports.pdf import generate_pdf_report, OmniCropPDF, _clean_text, _get_agronomic_opinion
from components.pdf_generator import generate_pdf_report as frontend_generate_pdf_report


@pytest.fixture
def sample_payload():
    return {
        "chuva_acumulada_30d": 45.2,
        "chuva_acumulada_60d": 88.0,
        "chuva_acumulada_90d": 130.5,
        "GDA_mensal": 275.4,
        "t_mean": 24.8,
        "t_max": 31.2,
        "t_min": 18.5,
        "radiacao_solar_mean": 320.0,
        "et0_acumulada_30d": 40.0,
    }


@pytest.fixture
def sample_resultado():
    return {
        "ndvi_previsto": 0.742,
        "fase_fenologica": "Crescimento Vegetativo",
        "confiabilidade_modelo": "Alta (R2=0.88)",
        "status_geral": "Vigor Vegetativo Saudável",
        "fatores_de_risco_identificados": [
            "Déficit hídrico incipiente nos últimos 10 dias",
            "Monitorar janela de adubação",
        ],
    }


@pytest.fixture
def sample_gold_kpis():
    return {
        "balanco_hidrico_mm": -14.8,
        "dias_sem_chuva": 5,
        "gda_total_acumulado": 156.2,
        "risco_estresse_hidrico": "MODERADO",
        "recomendacao_manejo": "Atenção Operacional: monitorar umidade do solo e previsão climática.",
        "chuva_total_mm": 18.2,
        "et0_total_mm": 33.0,
        "temp_max_media_c": 30.5,
        "temp_min_media_c": 19.1,
    }


@pytest.fixture
def sample_xai_res():
    return {
        "top_driver": "Chuva Recente (30d)",
        "contributions": {
            "Chuva Recente (30d)": +0.038,
            "Chuva Médio Prazo (60d)": +0.012,
            "Soma Térmica (GDA)": -0.005,
        },
        "narrativa": "A elevação no vigor (+0.045 NDVI) foi impulsionada por Chuva Recente.",
        "pred_base": 0.697,
        "pred_sim": 0.742,
        "total_delta": +0.045,
    }


def test_clean_text_sanitizes_unsupported_characters():
    """Garante que emojis e setas unicode não quebrem a codificação Latin-1 do FPDF."""
    raw = "Alerta 🔴: Veranico ➔ 5 dias! Vigor: 0.850 ✨ Grau: 28°C"
    cleaned = _clean_text(raw)
    assert "🔴" not in cleaned
    assert "➔" not in cleaned
    assert "✨" not in cleaned
    assert "[CRITICO]" in cleaned
    assert "->" in cleaned
    # Deve ser encodável em latin-1 sem erro
    cleaned.encode("latin-1")


def test_generate_pdf_report_with_gold_and_xai(sample_payload, sample_resultado, sample_gold_kpis, sample_xai_res):
    """Valida geração do PDF consumindo explicitamente Gold KPIs e XAI."""
    pdf_bytes = generate_pdf_report(
        farm_name="Fazenda Esperança",
        city="Ribeirão Preto - SP",
        payload=sample_payload,
        resultado=sample_resultado,
        df=None,
        gold_kpis=sample_gold_kpis,
        xai_res=sample_xai_res,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_pdf_report_fallback_when_none_passed(sample_payload, sample_resultado):
    """Valida resiliência quando gold_kpis e xai_res são None (auto-derivação)."""
    pdf_bytes = generate_pdf_report(
        farm_name="Fazenda Santa Cruz",
        city="Sertãozinho - SP",
        payload=sample_payload,
        resultado=sample_resultado,
        df=None,
        gold_kpis=None,
        xai_res=None,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_pdf_report_with_df_derives_gold(sample_payload, sample_resultado):
    """Valida se um DataFrame histórico gera o gráfico NDVI e deriva a Camada Ouro."""
    dates = [datetime.now() - timedelta(days=i) for i in range(20, 0, -1)]
    df_mock = pd.DataFrame({
        "date": dates,
        "ndvi": [0.65 + 0.005 * i for i in range(20)],
        "precipitacao_total": [2.0 if i % 4 == 0 else 0.0 for i in range(20)],
        "evapotranspiracao_total": [3.5 for _ in range(20)],
        "t_max": [31.0 for _ in range(20)],
        "t_min": [18.0 for _ in range(20)],
        "gdd": [14.0 for _ in range(20)],
    })

    pdf_bytes = generate_pdf_report(
        farm_name="Talhão 04 - Canavial Norte",
        city="Piracicaba - SP",
        payload=sample_payload,
        resultado=sample_resultado,
        df=df_mock,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_frontend_component_delegation(sample_payload, sample_resultado, sample_gold_kpis, sample_xai_res):
    """Valida se o componente components.pdf_generator delega perfeitamente para o módulo core."""
    pdf_bytes = frontend_generate_pdf_report(
        farm_name="Fazenda Frontend Teste",
        city="Jaú - SP",
        payload=sample_payload,
        resultado=sample_resultado,
        gold_kpis=sample_gold_kpis,
        xai_res=sample_xai_res,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_agronomic_opinion_fallback(sample_gold_kpis, sample_xai_res):
    """Valida que o parecer agronômico determinístico é gerado mesmo sem chave de API."""
    opinion = _get_agronomic_opinion(
        farm_name="Fazenda Modelo",
        city="Araraquara - SP",
        ndvi_val=0.750,
        fase="Crescimento Vegetativo",
        gold_kpis=sample_gold_kpis,
        xai_res=sample_xai_res,
        alertas=["Risco Moderado de Veranico"],
        api_key=None,
    )

    assert isinstance(opinion, str)
    assert "Araraquara - SP" in opinion
    assert "-14.8 mm" in opinion
    assert "5 dias" in opinion
    assert "MODERADO" in opinion
    assert "0.750" in opinion
    assert "Chuva Recente (30d)" in opinion
