import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.fetch_api import search_location

class TestMockAPI(unittest.TestCase):
    @patch('src.data.fetch_api.requests.get')
    def test_search_location_success(self, mock_get):
        """Garante que nossa funcao mastiga o JSON da Open-Meteo corretamente."""
        # Preparar a resposta de mentira (Mock)
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "display_name": "Ribeirão Preto, São Paulo, Brazil",
                "lat": "-21.17",
                "lon": "-47.81"
            }
        ]
        mock_get.return_value = mock_response
        
        # Testar a funcao
        resultado = search_location("Ribeirao")
        
        # Verificacoes
        self.assertEqual(len(resultado), 1)
        self.assertIn("Ribeirão Preto", resultado[0]["label"])
        self.assertEqual(resultado[0]["lat"], -21.17)

    @patch('src.data.fetch_api.requests.get')
    def test_search_location_failure(self, mock_get):
        """Garante que a função não quebra (Graceful Degradation) se a API cair."""
        # Simula a API jogando uma excecao de Timeout
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("API is down")
        
        resultado = search_location("Ribeirao")
        self.assertEqual(resultado, []) # Deve retornar lista vazia sem quebrar o app

if __name__ == '__main__':
    unittest.main()

from src.data.ingest_azure import fetch_weather_data
from src.data.contracts import OpenMeteoResponse, OpenMeteoDaily
from pydantic import ValidationError

class TestDataIntegration(unittest.TestCase):
    @patch('src.data.ingest_azure.requests.get')
    def test_fetch_weather_retries_on_500(self, mock_get):
        """Teste de Integração com Mocks: Falha 2 vezes com 500, sucesso na 3a."""
        import requests
        # Configura o mock para disparar erro HTTP nas primeiras 2 vezes
        mock_resp_500 = MagicMock()
        mock_resp_500.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        mock_resp_ok = MagicMock()
        mock_resp_ok.json.return_value = {
            "latitude": -21.17, "longitude": -47.81, "timezone": "America/Sao_Paulo",
            "daily": {"time": ["2026-09-30"], "temperature_2m_max": [30.0], "temperature_2m_min": [15.0], "precipitation_sum": [0.0]}
        }
        
        # Side_effect iterável: falha, falha, sucesso
        mock_get.side_effect = [mock_resp_500, mock_resp_500, mock_resp_ok]
        
        # A tenacity retry logic (retry) vai tentar 3 vezes
        resultado = fetch_weather_data()
        
        self.assertEqual(mock_get.call_count, 3)
        self.assertIn("daily", resultado)
        
    def test_pydantic_contract_fails_on_negative_precipitation(self):
        """Teste de Contrato: Garante que Pydantic bloqueia precipitação negativa."""
        bad_payload = {
            "latitude": -21.17, "longitude": -47.81, "timezone": "America/Sao_Paulo",
            "daily": {"time": ["2026-09-30"], "temperature_2m_max": [30.0], "temperature_2m_min": [15.0], "precipitation_sum": [-5.0]} # ERRO!
        }
        
        with self.assertRaises(ValidationError) as context:
            OpenMeteoResponse(**bad_payload)
            
        self.assertIn("Precipitação não pode ser negativa", str(context.exception))
