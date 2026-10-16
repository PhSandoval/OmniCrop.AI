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
