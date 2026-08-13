import os
from datetime import date

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


def _adicionar_meses(data_base, quantidade_meses):
    ano = data_base.year + (data_base.month - 1 + quantidade_meses) // 12
    mes = (data_base.month - 1 + quantidade_meses) % 12 + 1
    dia = min(data_base.day, [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return date(ano, mes, dia)


def extrair_ndvi_historico(lat: float, lon: float, start_date: str, end_date: str, cloud_cover_max: int = 70):
    """Retorna uma série mensal de NDVI entre start_date e end_date."""
    try:
        project = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('EE_PROJECT') or 'sugarcanemle'
        ee.Initialize(project=project)
    except Exception as e:
        print("Erro de inicialização. Rode 'earthengine authenticate' no terminal.")
        print(str(e))
        return []

    ponto = ee.Geometry.Point([float(lon), float(lat)])
    area_fazenda = ponto.buffer(2000)

    inicio = date.fromisoformat(start_date)
    fim = date.fromisoformat(end_date)

    meses = []
    mes_atual = date(inicio.year, inicio.month, 1)
    mes_final = date(fim.year, fim.month, 1)
    while mes_atual <= mes_final:
        proximo_mes = _adicionar_meses(mes_atual, 1)
        colecao = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(area_fazenda)
            .filterDate(mes_atual.isoformat(), proximo_mes.isoformat())
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max))
            .sort('system:time_start', False)
        )

        quantidade = colecao.size().getInfo()
        if quantidade > 0:
            imagem = colecao.median()
            ndvi = imagem.normalizedDifference(['B8', 'B4']).rename('NDVI')
            estatistica = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=area_fazenda,
                scale=10,
                maxPixels=1e9,
            )
            valor_ndvi = estatistica.get('NDVI').getInfo()
        else:
            valor_ndvi = None

        meses.append({
            "periodo": mes_atual.strftime('%Y-%m'),
            "data_referencia": mes_atual.isoformat(),
            "ndvi_medio": valor_ndvi,
            "quantidade_imagens": quantidade,
        })

        mes_atual = proximo_mes

    return meses

# Executa o pipeline
if __name__ == "__main__":
    # Teste rápido com Ribeirão Preto
    resultado = extrair_ndvi_ribeirao(-21.1775, -47.8103)
    print(resultado)