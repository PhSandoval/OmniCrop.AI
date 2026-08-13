import os
import ee
import geemap

def extrair_ndvi_ribeirao(lat: float, lon: float):
    """
    Autentica no GEE, busca imagens recentes do Sentinel-2 sem nuvens,
    calcula o NDVI e retorna a média do índice para a região.
    """
    # 1. Inicializa a conexão com o Google Earth Engine
    # Substitua pelo ID do projeto criado no passo de cadastro
    try:
        project = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('EE_PROJECT') or 'sugarcanemle'
        ee.Initialize(project=project)
    except Exception as e:
        print("Erro de inicialização. Rode 'earthengine authenticate' no terminal.")
        print(str(e))
        return

    # 2. Definir a Área de Interesse (AoI)
    # No GEE, a ordem é sempre [Longitude, Latitude]!
    ponto = ee.Geometry.Point([float(lon), float(lat)])

    # Criamos um "buffer" de 2 km ao redor do ponto para simular o tamanho de uma fazenda
    area_fazenda = ponto.buffer(2000)

    print("Buscando imagens de satélite processadas no Google Cloud...")

    # 3. Filtrar a coleção do Sentinel-2 (Superfície Refletida)
    colecao = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(area_fazenda)           # Filtra pelo polígono da fazenda
        .filterDate('2026-07-01', '2026-08-11') # Últimos ~40 dias
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) # Máximo de 10% de nuvens
        .sort('system:time_start', False))    # Pega a mais recente primeiro

    # Verifica se encontrou alguma imagem sem nuvens no período
    quantidade = colecao.size().getInfo()
    if quantidade == 0:
        print("Nenhuma imagem limpa encontrada neste período. Nuvens atrapalharam!")
        return
        
    imagem_recente = colecao.first()
    data_imagem = ee.Date(imagem_recente.get('system:time_start')).format('YYYY-MM-dd').getInfo()
    print(f"Imagem capturada em: {data_imagem}")

    # 4. A Matemática do NDVI
    # O GEE faz o cálculo pixel a pixel diretamente nos servidores deles
    ndvi = imagem_recente.normalizedDifference(['B8', 'B4']).rename('NDVI')

    # 5. Extrair o dado numérico para o seu Banco de Dados
    # Reduzimos a imagem inteira da fazenda para um único número (a média)
    estatistica = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=area_fazenda,
        scale=10, # Resolução do Sentinel é de 10x10 metros
        maxPixels=1e9
    )
    
    valor_ndvi = estatistica.get('NDVI').getInfo()
    print(f"Média do NDVI na Fazenda simulada: {valor_ndvi:.4f}")
    
    return {
        "data_satelite": data_imagem,
        "ndvi_medio": valor_ndvi
    }

# Executa o pipeline
if __name__ == "__main__":
    # Teste rápido com Ribeirão Preto
    resultado = extrair_ndvi_ribeirao(-21.1775, -47.8103)
    print(resultado)