import requests
import json
from typing import Dict, Any

def fetch_openmeteo_agro_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Busca dados agrometeorológicos da OpenMeteo para uma coordenada específica,
    focando em variáveis cruciais para o cultivo de cana-de-açúcar.
    """
    # Endpoint base da OpenMeteo
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Parâmetros da requisição montados especificamente para agronomia
    params = {
        "latitude": lat,
        "longitude": lon,
        # Variáveis horárias focadas em balanço hídrico, solo e radiação
        "hourly": [
            "temperature_2m",           # Temperatura do ar
            "precipitation",            # Chuva (mm)
            "evapotranspiration",       # Perda de água (solo + planta)
            "soil_temperature_6cm",     # Temperatura do solo (rasa)
            "soil_temperature_18cm",    # Temperatura do solo (profunda - brotação)
            "soil_moisture_3_to_9cm",   # Umidade do solo (rasa)
            "soil_moisture_9_to_27cm",  # Umidade do solo (profunda - raízes)
            "shortwave_radiation"       # Radiação solar (fotossíntese/ATR)
        ],
        "timezone": "America/Sao_Paulo", # Ajuste para o fuso horário local
        "past_days": 1,                  # Pega o dia anterior para histórico recente
        "forecast_days": 3               # Previsão para os próximos 3 dias
    }
    
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
        print(f"Evapotranspiração: {hourly_data['evapotranspiration'][0]} mm")
        print(f"Umidade do solo (9-27cm): {hourly_data['soil_moisture_9_to_27cm'][0]} m³/m³")
        
        # Dica: Para ver o JSON inteiro formatado, descomente a linha abaixo:
        # print(json.dumps(dados_brutos, indent=2, ensure_ascii=False))