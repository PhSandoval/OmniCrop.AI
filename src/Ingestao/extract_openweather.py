import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_openweather(lat: float, lon: float):
    """Busca o tempo atual no OpenWeather para as coordenadas fornecidas.
    Retorna o JSON da API como dicionário ou None em caso de erro."""
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        print("Erro: A chave da API não foi encontrada no arquivo .env!")
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": float(lat),
        "lon": float(lon),
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data
    except requests.exceptions.RequestException as error:
        print(f"Erro na requisição OpenWeather: {error}")
        return None
    except ValueError:
        print("Erro: a resposta da API não é um JSON válido.")
        return None


if __name__ == "__main__":
    # Teste rápido com coordenadas de Ribeirão Preto
    result = fetch_openweather(-21.1775, -47.8103)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))