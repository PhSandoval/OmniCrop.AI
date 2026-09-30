import pytest
import pandas as pd
from pathlib import Path
import sys

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.predict import load_model, FEATURE_KEYS, get_prediction

def test_model_loading():
    """O Cérebro da Inteligencia Artificial precisa carregar sem quebrar."""
    model = load_model()
    assert model is not None, "O modelo não foi carregado corretamente."

def test_feature_keys_match():
    """As chaves que vao para o payload do Gradient Boosting devem ser as mesmas treinadas."""
    expected_keys = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']
    assert FEATURE_KEYS == expected_keys, "As features do modelo mudaram e quebrarão a previsão."
    
def test_prediction_output():
    """Garantir que a previsão retorna o formato correto para o Streamlit."""
    payload = {
        'chuva_acumulada_30d': 50, 
        'chuva_acumulada_60d': 100, 
        'chuva_acumulada_90d': 150, 
        'GDA_mensal': 300
    }
    res = get_prediction(payload)
    
    assert res is not None
    assert "ndvi_previsto" in res
    assert isinstance(res["ndvi_previsto"], float)

def test_model_static_matrix_bounds():
    """Teste de Unidade (Cérebro): Injeta matrizes extremas para ver se o modelo respeita o limite do NDVI (0 a 1)."""
    model = load_model()
    
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
