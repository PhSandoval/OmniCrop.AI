import os
import json
from datetime import datetime
# Importando as funções que criamos anteriormente
from extract_openmeteo import fetch_openmeteo_agro_data
from extract_openweather import fetch_openweather
from extract_geemap import extrair_ndvi_ribeirao
from dotenv import load_dotenv

# Carrega as chaves de API (OpenWeather)
load_dotenv()

class AgroDataAggregator:
    def __init__(self, lat: float, lon: float, nome_talhao: str):
        self.lat = lat
        self.lon = lon
        self.nome_talhao = nome_talhao
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.pasta_dados = "../SugarCaneMLE/data" # Define onde os arquivos serão salvos
        
        # Cria a pasta 'dados' automaticamente se ela não existir
        if not os.path.exists(self.pasta_dados):
            os.makedirs(self.pasta_dados)

    def coletar_e_unificar(self):
        """O Maestro: Chama todas as APIs, extrai o suco e junta tudo."""
        print(f"Iniciando coleta para o talhão: {self.nome_talhao}...\n")
        
        # 1. Busca os Dados (O processamento pode levar alguns segundos devido ao satélite)
        meteo_data = fetch_openmeteo_agro_data(self.lat, self.lon)
        weather_data = fetch_openweather()
        ndvi_data = extrair_ndvi_ribeirao(self.lat, self.lon) # Adapte a função GEE para receber lat/lon
        
        # 2. A Transformação (Filtragem e Limpeza)
        
        # OpenMeteo: Como ele retorna arrays por hora, pegamos o índice [0] (a hora mais recente)
        dados_solo = {}
        if meteo_data and 'hourly' in meteo_data:
            hourly = meteo_data['hourly']
            dados_solo = {
                "evapotranspiracao_mm": hourly['evapotranspiration'][0],
                "temp_solo_18cm": hourly['soil_temperature_18cm'][0],
                "umidade_solo_raiz": hourly['soil_moisture_9_to_27cm'][0],
                "radiacao_solar": hourly['shortwave_radiation'][0]
            }

        # OpenWeather: Focado na atmosfera imediata e ventos
        dados_atmosfera = {}
        if weather_data:
            vento = weather_data.get('wind', {})
            clima = weather_data.get('weather', [{}])[0]
            dados_atmosfera = {
                "condicao": clima.get('description'),
                "vento_velocidade_kmh": round(vento.get('speed', 0) * 3.6, 1),
                "vento_rajada_kmh": round(vento.get('gust', 0) * 3.6, 1),
                "temp_ar_atual": weather_data.get('main', {}).get('temp')
            }

        # 3. O Modelo Unificado (O "Frankenstein" do bem)
        horario_atual = datetime.now().isoformat()
        
        modelo_final = {
            "id_coleta": f"{self.nome_talhao}_{horario_atual[:13]}", # Gera um ID único
            "metadados": {
                "talhao": self.nome_talhao,
                "lat": self.lat,
                "lon": self.lon,
                "data_hora_extracao": horario_atual
            },
            "atmosfera": dados_atmosfera,
            "solo_e_hidrico": dados_solo,
            "saude_vegetativa": ndvi_data if ndvi_data else {"ndvi_medio": None, "data_satelite": None}
        }
        
        return modelo_final

    def salvar_na_pasta(self, dados_unificados):
        """Salva o dicionário final como um arquivo .json na pasta de dados."""
        # Cria um nome de arquivo seguro (ex: RP_Talhao_01_2026-08-11.json)
        data_simples = datetime.now().strftime("%Y-%m-%d_%H%M")
        nome_arquivo = f"{self.nome_talhao.replace(' ', '_')}_{data_simples}.json"
        
        caminho_completo = os.path.join(self.pasta_dados, nome_arquivo)
        
        # Escreve o arquivo no disco
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(dados_unificados, f, indent=4, ensure_ascii=False)
            
        print(f"\n✅ SUCESSO! Dados unificados salvos em: {caminho_completo}")

# ==========================================
# Execução
# ==========================================
if __name__ == "__main__":
    # Instancia o adaptador para um talhão específico em Ribeirão Preto
    orquestrador = AgroDataAggregator(
        lat=-21.1775,
        lon=-47.8103,
        nome_talhao="RP_Talhao_Central"
    )
    
    # 1. Roda a máquina (Extrai e Unifica)
    dados_limpos = orquestrador.coletar_e_unificar()
    
    # 2. Mostra no console para você validar se ficou bom
    print(json.dumps(dados_limpos, indent=2, ensure_ascii=False))
    
    # 3. Salva na sua pasta /dados
    orquestrador.salvar_na_pasta(dados_limpos)