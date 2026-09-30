import pytest

@pytest.fixture
def mock_openmeteo_json():
    """Simula o JSON de sucesso retornado pela Open-Meteo."""
    return {
        "latitude": -21.17, 
        "longitude": -47.81, 
        "timezone": "America/Sao_Paulo",
        "daily": {
            "time": ["2026-09-30", "2026-10-01"], 
            "temperature_2m_max": [30.0, 31.0], 
            "temperature_2m_min": [15.0, 16.0], 
            "precipitation_sum": [0.0, 5.0]
        }
    }

@pytest.fixture
def mock_nominatim_json():
    """Simula o JSON de sucesso retornado pelo Nominatim (Geolocalização)."""
    return [
        {
            "display_name": "Ribeirão Preto, São Paulo, Brazil",
            "lat": "-21.17",
            "lon": "-47.81"
        }
    ]

@pytest.fixture
def bad_openmeteo_json():
    """Simula um JSON da Open-Meteo com erro (Precipitação negativa para testar contratos)."""
    return {
        "latitude": -21.17, 
        "longitude": -47.81, 
        "timezone": "America/Sao_Paulo",
        "daily": {
            "time": ["2026-09-30"], 
            "temperature_2m_max": [30.0], 
            "temperature_2m_min": [15.0], 
            "precipitation_sum": [-5.0]  # Erro injetado
        }
    }
