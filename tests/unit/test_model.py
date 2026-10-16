import pytest
import pandas as pd
from pathlib import Path
import sys

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.predict import load_model, FEATURE_KEYS, get_prediction, explain_prediction_delta


def test_model_loading():
    """O Cérebro da Inteligência Artificial precisa carregar sem quebrar (padrão Cana-de-Açúcar)."""
    model = load_model("sugarcane")
    assert model is not None, "O modelo não foi carregado corretamente."


def test_model_routing_sugarcane():
    """Valida que o roteador de modelos carrega o modelo de Cana-de-Açúcar normalmente."""
    model = load_model("sugarcane")
    assert model is not None


def test_model_routing_soybean_raises_not_implemented():
    """Valida que o carregamento de modelo de Soja (não treinado) levanta NotImplementedError amigável."""
    with pytest.raises(NotImplementedError) as exc_info:
        load_model("soybean")
    assert "Soja" in str(exc_info.value)
    assert "fase de treino" in str(exc_info.value)


def test_model_routing_corn_raises_not_implemented():
    """Valida que o carregamento de modelo de Milho (não treinado) levanta NotImplementedError amigável."""
    with pytest.raises(NotImplementedError) as exc_info:
        load_model("corn")
    assert "Milho" in str(exc_info.value)
    assert "fase de treino" in str(exc_info.value)


def test_feature_keys_match():
    """As chaves que vao para o payload do Gradient Boosting devem ser as mesmas treinadas."""
    expected_keys = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']
    assert FEATURE_KEYS == expected_keys, "As features do modelo mudaram e quebrarão a previsão."


def test_prediction_output():
    """Garantir que a previsão retorna o formato correto para o Streamlit com Cana-de-Açúcar."""
    payload = {
        'chuva_acumulada_30d': 50, 
        'chuva_acumulada_60d': 100, 
        'chuva_acumulada_90d': 150, 
        'GDA_mensal': 300
    }
    res = get_prediction(payload, crop_id="sugarcane")
    
    assert res is not None
    assert "ndvi_previsto" in res
    assert isinstance(res["ndvi_previsto"], float)


def test_prediction_output_unimplemented_crop():
    """Valida que get_prediction retorna dict seguro com status amigável de 'Em Treinamento' para Soja e Milho."""
    payload = {
        'chuva_acumulada_30d': 50, 
        'chuva_acumulada_60d': 100, 
        'chuva_acumulada_90d': 150, 
        'GDA_mensal': 300
    }
    res_soja = get_prediction(payload, crop_id="soybean")
    assert res_soja is not None
    assert "Treinamento" in res_soja["status_geral"]
    assert res_soja["ndvi_previsto"] == 0.0

    res_milho = get_prediction(payload, crop_id="corn")
    assert res_milho is not None
    assert "Treinamento" in res_milho["status_geral"]


def test_model_static_matrix_bounds():
    """Teste de Unidade (Cérebro): Injeta matrizes extremas para ver se o modelo respeita o limite do NDVI (0 a 1)."""
    model = load_model("sugarcane")
    
    # Cria matrizes numéricas sintéticas para limites climáticos absurdos
    payload_seca_extrema = pd.DataFrame([{
        'chuva_acumulada_30d': 0.0, 
        'chuva_acumulada_60d': 0.0, 
        'chuva_acumulada_90d': 0.0, 
        'GDA_mensal': 500.0
    }])
    
    payload_enchente = pd.DataFrame([{
        'chuva_acumulada_30d': 1000.0, 
        'chuva_acumulada_60d': 2000.0, 
        'chuva_acumulada_90d': 3000.0, 
        'GDA_mensal': 10.0
    }])
    
    pred_seca = model.predict(payload_seca_extrema)[0]
    pred_enchente = model.predict(payload_enchente)[0]
    
    assert 0.0 <= pred_seca <= 1.0, f"NDVI da seca fora dos limites: {pred_seca}"
    assert 0.0 <= pred_enchente <= 1.0, f"NDVI da enchente fora dos limites: {pred_enchente}"


def test_xai_explain_prediction_delta():
    """Valida a decomposição de contribuição marginal de atributos (XAI) entre cenários."""
    base = {'chuva_acumulada_30d': 20.0, 'chuva_acumulada_60d': 60.0, 'chuva_acumulada_90d': 100.0, 'GDA_mensal': 120.0}
    sim = {'chuva_acumulada_30d': 80.0, 'chuva_acumulada_60d': 60.0, 'chuva_acumulada_90d': 100.0, 'GDA_mensal': 140.0}

    res = explain_prediction_delta(base, sim, crop_id="sugarcane")

    assert "total_delta" in res
    assert "contributions" in res
    assert "top_driver" in res
    assert "narrativa" in res
    assert len(res["contributions"]) == 4
    assert isinstance(res["narrativa"], str)
