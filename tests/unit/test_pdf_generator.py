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


def test_pdf_helpers_and_gemini_opinion(sample_gold_kpis, sample_xai_res, tmp_path):
    """Cobre helpers internos de higienização, exportação de figuras e integração com Gemini."""
    from unittest.mock import MagicMock, patch
    from src.reports.pdf import _fig_to_tmp_png, _resolve_gemini_key

    # 1. _clean_text casos vazios
    assert _clean_text("") == ""
    assert _clean_text(None) == ""

    # 2. _resolve_gemini_key
    assert _resolve_gemini_key("chave_explicita") == "chave_explicita"

    with patch("src.utils.copilot_context.get_gemini_api_key", side_effect=RuntimeError("Erro mock")):
        res_key = _resolve_gemini_key(None)
        assert res_key == os.getenv("GEMINI_API_KEY")

    # Cobre linhas 169-170 (exceção ao inspecionar streamlit)
    broken_st = MagicMock()
    type(broken_st).secrets = property(lambda self: (_ for _ in ()).throw(RuntimeError("error secrets")))
    with patch.dict("sys.modules", {"streamlit": broken_st}):
        _resolve_gemini_key(None)

    # 3. _fig_to_tmp_png
    # Caso de erro:
    assert _fig_to_tmp_png("nao_e_figura") is None
    # Caso de sucesso com mock de write_image (cobre linhas 50-63):
    from PIL import Image
    with patch("plotly.io.write_image") as mock_write:
        def fake_write(fig, file_path, **kwargs):
            img = Image.new("RGB", (20, 20), color="green")
            img.save(file_path, format="PNG")
        mock_write.side_effect = fake_write
        tmp_path_gen = _fig_to_tmp_png(MagicMock())
        assert tmp_path_gen is not None
        if os.path.exists(tmp_path_gen):
            os.unlink(tmp_path_gen)

    # 4. _get_agronomic_opinion com Gemini mockado retornando texto
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Parecer técnico da IA agronômica validando as condições hídricas ideais do talhão."
    mock_model.generate_content.return_value = mock_response

    with patch("google.generativeai.GenerativeModel", return_value=mock_model):
        res_text = _get_agronomic_opinion(
            farm_name="Fazenda IA Teste",
            city="Ribeirão Preto",
            ndvi_val=0.78,
            fase="Maturação",
            gold_kpis=sample_gold_kpis,
            xai_res=sample_xai_res,
            alertas=[],
            api_key="chave_gemini_valida",
        )
        assert "Parecer técnico da IA" in res_text

    # 5. _get_agronomic_opinion com Gemini disparando exceção no loop (cobre fallback)
    with patch("google.generativeai.GenerativeModel", side_effect=RuntimeError("Falha na API")):
        res_fallback = _get_agronomic_opinion(
            farm_name="Fazenda IA Teste",
            city="Ribeirão Preto",
            ndvi_val=0.78,
            fase="Maturação",
            gold_kpis=sample_gold_kpis,
            xai_res=sample_xai_res,
            alertas=[],
            api_key="chave_gemini_valida",
        )
        assert "Ribeirão Preto" in res_fallback

    # 6. _get_agronomic_opinion com exceção externa na configuração (cobre linhas 241-242)
    with patch("google.generativeai.configure", side_effect=Exception("Falha na inicialização")):
        res_fallback_outer = _get_agronomic_opinion(
            farm_name="Fazenda IA Teste",
            city="Ribeirão Preto",
            ndvi_val=0.78,
            fase="Maturação",
            gold_kpis=sample_gold_kpis,
            xai_res=sample_xai_res,
            alertas=[],
            api_key="chave_gemini_valida",
        )
        assert "Ribeirão Preto" in res_fallback_outer


def test_generate_pdf_report_with_chart_and_empty_alerts(sample_payload, sample_gold_kpis, sample_xai_res, tmp_path):
    """Valida renderização de gráfico Plotly e bloco de alerta OK quando não há fatores de risco."""
    from unittest.mock import MagicMock, patch
    from PIL import Image

    # Cria uma imagem PNG real de 100x50 pixels para o FPDF aceitar sem erro
    tmp_png = tmp_path / "chart.png"
    img = Image.new("RGB", (100, 50), color="#16A085")
    img.save(str(tmp_png), format="PNG")

    df_sample = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10),
        "ndvi_medio": [0.65] * 10,
        "precipitacao_total": [5.0] * 10,
    })

    # Mock _fig_to_tmp_png para retornar o arquivo PNG real
    with patch("src.reports.pdf._fig_to_tmp_png", return_value=str(tmp_png)):
        # Resultado sem alertas (cobre linhas 508-512)
        res_sem_alertas = {
            "ndvi_previsto": 0.81,
            "fase_fenologica": "Maturação",
            "confiabilidade_modelo": "Alta",
            "fatores_de_risco_identificados": [],
        }

        pdf_bytes = generate_pdf_report(
            farm_name="Fazenda Gráfico Teste",
            city="Sertãozinho - SP",
            payload=sample_payload,
            resultado=res_sem_alertas,
            gold_kpis=sample_gold_kpis,
            xai_res=sample_xai_res,
            df=df_sample,
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")

    # Testa também o bloco de tratamento de erro ao desvincular o arquivo temporário (linhas 398-399)
    tmp_png2 = tmp_path / "chart2.png"
    img.save(str(tmp_png2), format="PNG")
    with patch("src.reports.pdf._fig_to_tmp_png", return_value=str(tmp_png2)), \
         patch("os.unlink", side_effect=OSError("Erro de permissão mock")):
        pdf_bytes2 = generate_pdf_report(
            farm_name="Fazenda Gráfico Teste",
            city="Sertãozinho - SP",
            payload=sample_payload,
            resultado=res_sem_alertas,
            gold_kpis=sample_gold_kpis,
            xai_res=sample_xai_res,
            df=df_sample,
        )
        assert isinstance(pdf_bytes2, bytes)


def test_generate_pdf_report_exception_fallbacks(sample_payload, sample_resultado):
    """Cobre blocos de exceção ao derivar gold_kpis e xai_res automaticamente."""
    from unittest.mock import patch

    df_sample = pd.DataFrame({"dummy": [1, 2, 3]})

    # Mock de falha em transform_to_gold e explain_prediction_delta
    with patch("src.data.ingest_azure.transform_to_gold", side_effect=RuntimeError("Erro Gold")), \
         patch("src.models.predict.explain_prediction_delta", side_effect=RuntimeError("Erro XAI")):
        
        pdf_bytes = generate_pdf_report(
            farm_name="Fazenda Fallback Teste",
            city="Catanduva - SP",
            payload=sample_payload,
            resultado=sample_resultado,
            gold_kpis=None,
            xai_res=None,
            df=df_sample,
        )

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")
