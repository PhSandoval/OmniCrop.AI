import requests
import json
from typing import Dict, Any


def fetch_openmeteo_agro_data(
    lat: float,
    lon: float,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Dict[str, Any]:
    """
    Busca dados agrometeorológicos da OpenMeteo para uma coordenada específica,
    focando em variáveis cruciais para o cultivo de cana-de-açúcar.
    """
    # Endpoint base da OpenMeteo
    url = "https://archive-api.open-meteo.com/v1/archive"

    # Parâmetros da requisição montados especificamente para agronomia
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join([
            "temperature_2m",           # Temperatura do ar
            "relative_humidity_2m",     # Umidade relativa do ar
            "precipitation",            # Chuva (mm)
            "et0_fao_evapotranspiration", # Evapotranspiração de referência
            "soil_temperature_7_to_28cm", # Temperatura do solo (profundidade próxima de 18 cm)
            "soil_moisture_7_to_28cm",   # Umidade do solo (profundidade próxima de 9-27 cm)
            "shortwave_radiation",      # Radiação solar (fotossíntese/ATR)
            "wind_speed_10m",           # Vento histórico para EDA
            "wind_gusts_10m"            # Rajada de vento histórica
        ]),
        "timezone": "America/Sao_Paulo",
    }

    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    try:
        # Fazendo a requisição GET
        print(f"Fazendo fetch dos dados para Lat: {lat}, Lon: {lon}...")
        response = requests.get(url, params=params)
        
        # Levanta um erro se o status code não for 200 (OK)
        response.raise_for_status()
        
        # Converte a resposta bruta para um dicionário Python
        data = response.json()
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados na OpenMeteo: {e}")
        return {}


def fetch_openmeteo_forecast_data(lat: float, lon: float, forecast_days: int = 3) -> Dict[str, Any]:
    """Busca previsão horária da OpenMeteo para a camada de tempo real."""
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_gusts_10m",
            "shortwave_radiation",
        ]),
        "forecast_days": forecast_days,
        "timezone": "America/Sao_Paulo",
    }

    try:
        print(f"Buscando previsão de {forecast_days} dias para Lat: {lat}, Lon: {lon}...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar previsão na OpenMeteo: {e}")
        return {}

# ==========================================
# Bloco de Execução (Teste Local)
# ==========================================
if __name__ == "__main__":
    # Coordenadas de Ribeirão Preto (Centro-polo da cana-de-açúcar)
    LAT_RP = -21.1775
    LON_RP = -47.8103
    
    # Executa a função
    dados_brutos = fetch_openmeteo_agro_data(lat=LAT_RP, lon=LON_RP)
    
    if dados_brutos:
        # Imprime os metadados da requisição para confirmar
        print("\n--- Sucesso! ---")
        print(f"Fuso Horário retornado: {dados_brutos.get('timezone')}")
        print(f"Elevação: {dados_brutos.get('elevation')} metros")
        
        # Acessando o array gigante de dados horários
        hourly_data = dados_brutos.get('hourly', {})
        
        # Imprimindo apenas a primeira hora da lista como amostra para não poluir o terminal
        print("\n--- Amostra do primeiro registro horário ---")
        print(f"Horário: {hourly_data['time'][0]}")
        print(f"Temperatura do ar: {hourly_data['temperature_2m'][0]} °C")
        print(f"Precipitação: {hourly_data['precipitation'][0]} mm")
        print(f"Evapotranspiração ET0: {hourly_data['et0_fao_evapotranspiration'][0]} mm")
        print(f"Umidade do solo (7-28cm): {hourly_data['soil_moisture_7_to_28cm'][0]} m³/m³")
        
        # Dica: Para ver o JSON inteiro formatado, descomente a linha abaixo:
        # print(json.dumps(dados_brutos, indent=2, ensure_ascii=False))