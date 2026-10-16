import pytest
import pandas as pd
from pathlib import Path
import sys

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.predict import load_model, FEATURE_KEYS, get_prediction, explain_prediction_delta


def test_model_loading_default():
    """O Cérebro da Inteligência Artificial precisa carregar sem quebrar (padrão Cana-de-Açúcar)."""
    model = load_model("sugarcane")
    assert model is not None, "O modelo não foi carregado corretamente."


def test_model_routing_all_crops():
    """Valida que o roteador de modelos carrega com sucesso os 5 modelos treinados."""
    crops_to_test = ["sugarcane", "soybean", "corn", "coffee", "pasture"]
    for crop in crops_to_test:
        model = load_model(crop)
        assert model is not None, f"Falha ao carregar modelo para a cultura {crop}"


def test_model_routing_unimplemented_crop_raises():
    """Valida que o carregamento de cultura sem modelo treinado (ex: trigo) levanta NotImplementedError amigável."""
    with pytest.raises(NotImplementedError) as exc_info:
        load_model("wheat")
    assert "fase de treino" in str(exc_info.value)


def test_feature_keys_match():
    """As chaves que vão para o payload do Gradient Boosting devem ser as mesmas treinadas."""
    expected_keys = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']
    assert FEATURE_KEYS == expected_keys, "As features do modelo mudaram e quebrarão a previsão."


def test_prediction_output_all_crops():
    """Garantir que get_prediction retorna formato correto com NDVI em [0, 1] para todas as 5 culturas."""
    payload = {
        'chuva_acumulada_30d': 65.0, 
        'chuva_acumulada_60d': 120.0, 
        'chuva_acumulada_90d': 180.0, 
        'GDA_mensal': 320.0
    }
    crops_to_test = ["sugarcane", "soybean", "corn", "coffee", "pasture"]
    for crop in crops_to_test:
        res = get_prediction(payload, crop_id=crop)
        assert res is not None, f"Retorno nulo para predição da cultura {crop}"
        assert "ndvi_previsto" in res
        assert isinstance(res["ndvi_previsto"], float)
        assert 0.0 <= res["ndvi_previsto"] <= 1.0, f"NDVI fora dos limites biológicos para {crop}: {res['ndvi_previsto']}"
        assert "fase_fenologica" in res
        assert "confiabilidade_modelo" in res


def test_prediction_output_unimplemented_crop():
    """Valida que get_prediction retorna dict seguro com status amigável de 'Em Treinamento' para cultura não cadastrada."""
    payload = {
        'chuva_acumulada_30d': 50, 
        'chuva_acumulada_60d': 100, 
        'chuva_acumulada_90d': 150, 
        'GDA_mensal': 300
    }
    res_trigo = get_prediction(payload, crop_id="wheat")
    assert res_trigo is not None
    assert "Treinamento" in res_trigo["status_geral"]
    assert res_trigo["ndvi_previsto"] == 0.0


def test_model_static_matrix_bounds():
    """Teste de Unidade (Cérebro): Injeta matrizes extremas para verificar limites de NDVI (0 a 1) nas culturas."""
    for crop in ["sugarcane", "soybean", "corn", "coffee", "pasture"]:
        model = load_model(crop)
        
        payload_seca = pd.DataFrame([{
            'chuva_acumulada_30d': 0.0, 
            'chuva_acumulada_60d': 0.0, 
            'chuva_acumulada_90d': 0.0, 
            'GDA_mensal': 600.0
        }])
        
        payload_enchente = pd.DataFrame([{
            'chuva_acumulada_30d': 1000.0, 
            'chuva_acumulada_60d': 2000.0, 
            'chuva_acumulada_90d': 3000.0, 
            'GDA_mensal': 50.0
        }])
        
        pred_seca = model.predict(payload_seca)[0]
        pred_enchente = model.predict(payload_enchente)[0]
        
        assert 0.0 <= pred_seca <= 1.0, f"NDVI da seca fora dos limites para {crop}: {pred_seca}"
        assert 0.0 <= pred_enchente <= 1.0, f"NDVI da enchente fora dos limites para {crop}: {pred_enchente}"


def test_xai_explain_prediction_delta():
    """Valida a decomposição de contribuição marginal de atributos (XAI) entre cenários."""
    base = {'chuva_acumulada_30d': 20.0, 'chuva_acumulada_60d': 60.0, 'chuva_acumulada_90d': 100.0, 'GDA_mensal': 120.0}
    sim = {'chuva_acumulada_30d': 80.0, 'chuva_acumulada_60d': 60.0, 'chuva_acumulada_90d': 100.0, 'GDA_mensal': 140.0}

    for crop in ["sugarcane", "soybean", "coffee"]:
        res = explain_prediction_delta(base, sim, crop_id=crop)

        assert "total_delta" in res
        assert "contributions" in res
        assert "top_driver" in res
        assert "narrativa" in res
        assert len(res["contributions"]) == 4
        assert isinstance(res["narrativa"], str)


def test_model_missing_file_fallback():
    """Valida que load_model levanta NotImplementedError se os arquivos de modelo não existirem."""
    from unittest.mock import patch

    load_model.clear()
    try:
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(NotImplementedError) as exc:
                load_model("sugarcane")
            assert "fase de treino" in str(exc.value)
    finally:
        load_model.clear()


def test_get_prediction_generic_exception():
    """Valida tratamento seguro de exceção inesperada em get_prediction."""
    from unittest.mock import patch

    with patch("src.models.predict.load_model", side_effect=RuntimeError("Erro inesperado mock")):
        assert get_prediction({"chuva_acumulada_30d": 10}) is None


def test_build_payload_and_badge_html():
    """Valida os helpers build_payload e badge_html."""
    from src.models.predict import build_payload, badge_html

    row = {
        "chuva_acumulada_30d": 10,
        "chuva_acumulada_60d": 20,
        "chuva_acumulada_90d": 30,
        "GDA_mensal": 40,
        "extra_field": 999,
    }
    p = build_payload(row)
    assert p == {
        "chuva_acumulada_30d": 10.0,
        "chuva_acumulada_60d": 20.0,
        "chuva_acumulada_90d": 30.0,
        "GDA_mensal": 40.0,
    }

    assert "badge-green" in badge_html("Vigor Alto")
    assert "badge-yellow" in badge_html("Vigor Médio")
    assert "badge-red" in badge_html("Vigor Sob Atenção")


def test_calcular_dss_all_decision_branches():
    """Valida todas as ramificações de regras fenológicas e cenários do DSS."""
    from src.models.predict import calcular_dss

    # 1. Maturador
    assert "Desperdício" in calcular_dss(8, 0.7, 0.5, cenario="Maturador", chuva_projetada=90)["status_title"]
    assert "Aplicação Ideal" in calcular_dss(8, 0.7, 0.5, cenario="Maturador", chuva_projetada=10)["status_title"]
    assert "Dose Insuficiente" in calcular_dss(8, 0.5, 0.6, cenario="Maturador", chuva_projetada=10)["status_title"]

    # 2. Colheita
    assert "Risco Operacional" in calcular_dss(8, 0.4, 0.4, cenario="Colheita", chuva_projetada=60)["status_title"]
    assert "Corte Liberado" in calcular_dss(8, 0.4, 0.4, cenario="Colheita", chuva_projetada=10, gda_projetado=120)["status_title"]
    assert "Janela Aceitável" in calcular_dss(8, 0.4, 0.4, cenario="Colheita", chuva_projetada=30, gda_projetado=50)["status_title"]

    # 3. Plantio
    assert "Risco de Falha" in calcular_dss(10, 0.2, 0.2, cenario="Plantio", chuva_projetada=10)["status_title"]
    assert "Risco de Podridão" in calcular_dss(10, 0.2, 0.2, cenario="Plantio", chuva_projetada=160)["status_title"]
    assert "Plantio Liberado" in calcular_dss(10, 0.2, 0.2, cenario="Plantio", chuva_projetada=50, gda_projetado=90)["status_title"]
    assert "Plantio com Restrições" in calcular_dss(10, 0.3, 0.3, cenario="Plantio", chuva_projetada=30, gda_projetado=50)["status_title"]

    # 4. Adubação
    assert "Volatilização Severa" in calcular_dss(1, 0.5, 0.6, cenario="Adubação Comum", chuva_projetada=10)["status_title"]
    assert "Absorção Lenta" in calcular_dss(1, 0.5, 0.6, cenario="Adubação Nitrato", chuva_projetada=10)["status_title"]
    assert "Ureia Protegida Segura" in calcular_dss(1, 0.5, 0.6, cenario="Adubação Protegida", chuva_projetada=10)["status_title"]
    assert "Risco Crítico de Lixiviação" in calcular_dss(1, 0.5, 0.6, cenario="Adubação Nitrato", chuva_projetada=120)["status_title"]
    assert "Risco Moderado" in calcular_dss(1, 0.5, 0.6, cenario="Adubação Comum", chuva_projetada=120)["status_title"]
    assert "Ureia Protegida Segura" in calcular_dss(1, 0.5, 0.6, cenario="Adubação Protegida", chuva_projetada=120)["status_title"]
    assert "Janela Ideal" in calcular_dss(1, 0.5, 0.6, cenario="Adubação", chuva_projetada=40)["status_title"]

    # 5. Irrigação
    assert "Risco de Alagamento" in calcular_dss(1, 0.4, 0.5, cenario="Irrigação", chuva_projetada=160)["status_title"]

    # 6. Fenologia Padrão
    assert "Normal p/ Fase" in calcular_dss(8, 0.5, 0.5)["status_title"]
    assert "Normal" in calcular_dss(1, 0.7, 0.7)["status_title"]
    assert "Atenção" in calcular_dss(1, 0.55, 0.55)["status_title"]


def test_explain_prediction_delta_stable_and_unimplemented():
    """Valida narrativa de estabilidade e fallback para cultura não implementada."""
    p = {'chuva_acumulada_30d': 50.0, 'chuva_acumulada_60d': 100.0, 'chuva_acumulada_90d': 150.0, 'GDA_mensal': 200.0}
    res_stable = explain_prediction_delta(p, p, crop_id="sugarcane")
    assert "estável" in res_stable["narrativa"]

    res_unimpl = explain_prediction_delta(p, p, crop_id="wheat")
    assert res_unimpl["top_driver"] == "Em Treinamento"


def test_plot_xai_waterfall():
    """Valida geração do gráfico Waterfall com Plotly."""
    from src.models.predict import plot_xai_waterfall

    explanation = {
        "pred_base": 0.5,
        "pred_sim": 0.6,
        "contributions": {"Chuva": 0.05, "GDA": 0.05}
    }
    fig = plot_xai_waterfall(explanation)
    assert fig is not None


def test_load_model_sugarcane_default_fallback():
    """Valida o fallback para ndvi_model.pkl caso specific_path não exista."""
    from unittest.mock import patch
    from pathlib import Path
    load_model.clear()
    try:
        def fake_exists(p):
            return "sugarcane_ndvi.pkl" not in str(p)
        with patch.object(Path, "exists", fake_exists):
            m = load_model("sugarcane")
            assert m is not None
    finally:
        load_model.clear()


def test_get_prediction_deficit_hidrico_alerta():
    """Valida disparo de alerta hídrico quando chuva_acumulada_30d < limiar."""
    res = get_prediction({
        "chuva_acumulada_30d": 5.0,
        "chuva_acumulada_60d": 20.0,
        "chuva_acumulada_90d": 30.0,
        "GDA_mensal": 100.0,
    }, crop_id="sugarcane")
    assert any("ALERTA HÍDRICO" in a for a in res["fatores_de_risco_identificados"])


def test_calcular_dss_remaining_branches():
    """Valida ramos residuais do DSS de irrigação e crescimento."""
    from src.models.predict import calcular_dss

    # Irrigação com delta negativo
    assert "Alerta Simulacao" in calcular_dss(mes_atual=5, ndvi_atual=0.6, ndvi_projetado=0.4, cenario="Irrigação")["status_title"]
    # Crescimento com ndvi baixo e delta positivo
    assert "Critico" in calcular_dss(mes_atual=1, ndvi_atual=0.3, ndvi_projetado=0.5)["status_title"]
    # Crescimento com ndvi baixo e delta <= 0
    assert "Atenção" in calcular_dss(mes_atual=1, ndvi_atual=0.3, ndvi_projetado=0.3)["status_title"]
    # Maturação com ndvi intermediário
    assert "Normal p/ Fase" in calcular_dss(mes_atual=8, ndvi_atual=0.5, ndvi_projetado=0.5)["status_title"]
    # ndvi_projetado is None
    res_none = calcular_dss(mes_atual=8, ndvi_atual=0.5, ndvi_projetado=None)
    assert "Normal p/ Fase" in res_none["status_title"]


def test_predict_ndvi_with_explanations_st_exception_handlers():
    """Valida blocos de contingência quando st.warning e st.error levantam exceção."""
    import streamlit as st
    from unittest.mock import patch
    from src.models.predict import get_prediction

    p = {'chuva_acumulada_30d': 50.0, 'chuva_acumulada_60d': 100.0, 'chuva_acumulada_90d': 150.0, 'GDA_mensal': 200.0}

    # 1. NotImplementedError com st.warning falhando
    with patch("src.models.predict.load_model", side_effect=NotImplementedError("Modelo em treinamento")):
        with patch.object(st, "warning", side_effect=RuntimeError("Streamlit UI absent")):
            res_nie = get_prediction(p, crop_id="wheat")
            assert res_nie["status_vigor"] == "Em Treinamento"


    # 2. Generic Exception com st.error falhando
    with patch("src.models.predict.load_model", side_effect=RuntimeError("Fatal IO")):
        with patch.object(st, "error", side_effect=RuntimeError("Streamlit UI absent")):
            res_err = get_prediction(p, crop_id="sugarcane")
            assert res_err is None


