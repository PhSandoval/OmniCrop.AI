import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.live_data import search_location

class TestMockAPI(unittest.TestCase):
    @patch('components.live_data.requests.get')
    def test_search_location_success(self, mock_get):
        """Garante que nossa funcao mastiga o JSON da Open-Meteo corretamente."""
        # Preparar a resposta de mentira (Mock)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "name": "Ribeirão Preto",
                    "admin1": "São Paulo",
                    "country": "Brazil",
                    "latitude": -21.17,
                    "longitude": -47.81,
                    "elevation": 540
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Testar a funcao
        resultado = search_location("Ribeirao")
        
        # Verificacoes
        self.assertEqual(len(resultado), 1)
        self.assertIn("Ribeirão Preto", resultado[0]["label"])
        self.assertEqual(resultado[0]["lat"], -21.17)

    @patch('components.live_data.requests.get')
    def test_search_location_failure(self, mock_get):
        """Garante que a função não quebra (Graceful Degradation) se a API cair."""
        # Simula a API jogando uma excecao de Timeout
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("API is down")
        
        resultado = search_location("Ribeirao")
        self.assertEqual(resultado, []) # Deve retornar lista vazia sem quebrar o app

if __name__ == '__main__':
    unittest.main()
