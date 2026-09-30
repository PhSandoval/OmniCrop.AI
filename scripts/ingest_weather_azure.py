import os
import json
import requests
from datetime import datetime
from azure.storage.blob import BlobServiceClient

# Configurações da Fazenda Boa Vista
LATITUDE = -21.1704
LONGITUDE = -47.8103
CONTAINER_NAME = "omnicrop-data-lake-bronze"

def main():
    # A Connection String será injetada com segurança pelo GitHub Secrets
    azure_conn_str = os.getenv("AZURE_CONNECTION_STRING")
    if not azure_conn_str:
        raise ValueError("ERRO: Variável de ambiente AZURE_CONNECTION_STRING não encontrada.")

    print("☁️ Iniciando ingestão de dados para o Azure Blob Storage...")
    
    # 1. Extração (API Open-Meteo)
    print("📥 Baixando dados climáticos...")
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America/Sao_Paulo&past_days=7"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    execution_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Adicionando metadados ao JSON cru
    data['_metadata'] = {
        'ingestion_timestamp': datetime.utcnow().isoformat(),
        'source': 'open-meteo',
        'pipeline': 'github-actions-azure'
    }

    # 2. Conexão com a Azure
    print("🔗 Conectando à conta da Azure...")
    blob_service_client = BlobServiceClient.from_connection_string(azure_conn_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Cria o contêiner (equivalente ao bucket) se ele não existir
    if not container_client.exists():
        print(f"📦 Contêiner '{CONTAINER_NAME}' não existe. Criando agora...")
        container_client.create_container()

    # 3. Particionamento e Carga
    year, month, _ = execution_date.split('-')
    blob_name = f"weather/year={year}/month={month}/{execution_date}.json"
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)

    json_data = json.dumps(data, indent=2)
    blob_client.upload_blob(json_data, overwrite=True)

    print(f"✅ SUCESSO! Arquivo salvo em Azure Blob Storage: {CONTAINER_NAME}/{blob_name}")

if __name__ == "__main__":
    main()
