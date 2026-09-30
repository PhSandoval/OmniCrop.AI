import pytest
from unittest.mock import patch, MagicMock
import requests
from pydantic import ValidationError
import sys
from pathlib import Path

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.fetch_api import search_location
from src.data.ingest_azure import fetch_weather_data
from src.data.contracts import OpenMeteoResponse

@patch('src.data.fetch_api.requests.get')
def test_search_location_success(mock_get, mock_nominatim_json):
    """Garante que nossa função mastiga o JSON do Nominatim corretamente."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_nominatim_json
    mock_get.return_value = mock_response
    
    resultado = search_location("Ribeirao")
    
    assert len(resultado) == 1
    assert "Ribeirão Preto" in resultado[0]["label"]
    assert resultado[0]["lat"] == -21.17

@patch('src.data.fetch_api.requests.get')
def test_search_location_failure(mock_get):
    """Garante que a função não quebra (Graceful Degradation) se a API cair."""
    mock_get.side_effect = requests.exceptions.Timeout("API is down")
    
    resultado = search_location("Ribeirao")
    assert resultado == []

@patch('src.data.ingest_azure.requests.get')
def test_fetch_weather_retries_on_500(mock_get, mock_openmeteo_json):
    """Teste de Integração com Mocks: Falha 2 vezes com 500, sucesso na 3a."""
    # Erro
    mock_resp_500 = MagicMock()
    mock_resp_500.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    
    # Sucesso
    mock_resp_ok = MagicMock()
    mock_resp_ok.json.return_value = mock_openmeteo_json
    
    # falha, falha, sucesso
    mock_get.side_effect = [mock_resp_500, mock_resp_500, mock_resp_ok]
    
    resultado = fetch_weather_data()
    
    assert mock_get.call_count == 3
    assert "daily" in resultado

def test_pydantic_contract_fails_on_negative_precipitation(bad_openmeteo_json):
    """Teste de Contrato: Garante que Pydantic bloqueia precipitação negativa."""
    with pytest.raises(ValidationError) as exc_info:
        OpenMeteoResponse(**bad_openmeteo_json)
        
    assert "Precipitação não pode ser negativa" in str(exc_info.value)
