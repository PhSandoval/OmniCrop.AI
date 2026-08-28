import unittest
from pathlib import Path
import pandas as pd

# Simular a carga dinamica do componente para teste
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.api_client import load_model, FEATURE_KEYS, get_prediction

class TestMonolithicPipeline(unittest.TestCase):
    def test_model_loading(self):
        """O Cérebro da Inteligencia Artificial precisa carregar sem quebrar."""
        model = load_model()
        self.assertIsNotNone(model, "O modelo não foi carregado corretamente.")

    def test_feature_keys_match(self):
        """As chaves que vao para o payload do XGBoost devem ser as mesmas treinadas."""
        expected_keys = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']
        self.assertEqual(FEATURE_KEYS, expected_keys, "As features do modelo mudaram e quebrarão a previsão.")
        
    def test_prediction_output(self):
        """Garantir que a previsão retorna o formato correto para o Streamlit."""
        payload = {
            'chuva_acumulada_30d': 50, 
            'chuva_acumulada_60d': 100, 
            'chuva_acumulada_90d': 150, 
            'GDA_mensal': 300
        }
        res = get_prediction(payload)
        
        self.assertIsNotNone(res)
        self.assertIn("ndvi_previsto", res)
        self.assertTrue(isinstance(res["ndvi_previsto"], float))

if __name__ == '__main__':
    unittest.main()
