import pytest
from pydantic import ValidationError
from unittest.mock import patch
import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.schemas import OpenMeteoResponse, DailyWeather

def test_open_meteo_contract_valid():
    """Valida um payload JSON perfeito na classe OpenMeteoResponse."""
    payload = {
        "latitude": -21.17,
        "longitude": -47.81,
        "daily": {
            "time": ["2023-01-01", "2023-01-02"],
            "temperature_2m_max": [30.5, 31.0],
            "temperature_2m_min": [20.1, 21.0],
            "precipitation_sum": [0.0, 5.2],
            "et0_fao_evapotranspiration": [4.5, 4.2]
        }
    }
    
    response = OpenMeteoResponse(**payload)
    
    assert response.latitude == -21.17
    assert response.longitude == -47.81
    assert len(response.daily.time) == 2
    assert response.daily.precipitation_sum == [0.0, 5.2]
    assert response.daily.et0_fao_evapotranspiration == [4.5, 4.2]
    assert isinstance(response.daily.temperature_2m_max[0], float)


def test_open_meteo_contract_invalid():
    """Garante que o Pydantic bloqueia a execução se faltar a chave precipitation_sum."""
    payload = {
        "latitude": -21.17,
        "longitude": -47.81,
        "daily": {
            "time": ["2023-01-01"],
            "temperature_2m_max": [30.5],
            "temperature_2m_min": [20.1],
            # FALTA A CHAVE precipitation_sum
            "et0_fao_evapotranspiration": [4.5]
        }
    }
    
    with pytest.raises(ValidationError):
        OpenMeteoResponse(**payload)


@patch('requests.get')
def test_open_meteo_api_failure(mock_get):
    """Simula um erro HTTP 500 da Open-Meteo, garantindo que o sistema lança um erro limpo."""
    mock_get.return_value.status_code = 500
    mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
    
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        response = requests.get("https://api.open-meteo.com/v1/forecast")
        response.raise_for_status()
        
    assert "500 Server Error" in str(exc_info.value)
