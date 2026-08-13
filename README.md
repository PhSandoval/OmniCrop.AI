# SugarCaneMLE

Projeto de coleta e integração de dados agroclimáticos e de sensoriamento remoto para apoio à gestão de cana-de-açúcar.

A ideia principal é combinar dados de fontes públicas e geoespaciais para gerar um conjunto de indicadores úteis para análise de talhões, como:

- clima e condições atmosféricas;
- umidade e temperatura do solo;
- radiação solar e evapotranspiração;
- índice NDVI obtido via Google Earth Engine (GEE);
- consolidação desses dados em um único arquivo JSON para uso posterior em modelos, dashboards ou análise exploratória.

## Objetivo

Construir uma base de dados para monitoramento agronômico de áreas de cultivo, usando dados de:

- OpenMeteo (variáveis agrometeorológicas);
- OpenWeather (condições atmosféricas em tempo real);
- Google Earth Engine + Sentinel-2 (saúde vegetativa via NDVI).

## Stack principal

- Python 3
- Jupyter Notebook
- `requests`
- `python-dotenv`
- `pandas`, `numpy`, `matplotlib`, `seaborn`
- `earthengine-api`
- `geemap`

## Estrutura do projeto

```text
SugarCaneMLE/
├── .env                       # variáveis de ambiente locais
├── .venv/                     # ambiente virtual do projeto
├── data/                      # arquivos JSON gerados pela coleta
├── Models/                    # modelos e artefatos de ML/analise
├── notebook/
│   └── earthengine_geemap_starter.ipynb
├── src/
│   └── Ingestao/
│       ├── extract_geemap.py
│       ├── extract_openmeteo.py
│       ├── extract_openweather.py
│       └── Ingestão_central.py
├── requirements.txt
├── README.md
├── test/
└── .gitignore
```

## Pré-requisitos

- Python 3.10+ recomendado
- Git
- Conta Google Cloud com acesso ao Google Earth Engine
- Chave de API do OpenWeather

## Configuração do ambiente

1. Clone o projeto e entre na pasta:

```bash
git clone <url-do-repositorio>
cd SugarCaneMLE
```

2. Crie um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Crie um arquivo `.env` na raiz do projeto com as variáveis necessárias:

```env
OPENWEATHER_API_KEY=sua_chave_openweather
GOOGLE_CLOUD_PROJECT=sugarcanemle
```

> Se o projeto GCP for diferente, ajuste o valor de `GOOGLE_CLOUD_PROJECT` para o ID correto do seu projeto no Google Cloud.

## Autenticação Google Earth Engine

Para funcionar corretamente com o Google Earth Engine, é necessário autenticar a conta antes de executar a extração de NDVI.

No terminal:

```bash
earthengine authenticate
```

Em alguns ambientes, também pode ser necessário configurar o projeto do Google Cloud:

```bash
gcloud auth application-default login
gcloud config set project sugarcanemle
export GOOGLE_CLOUD_PROJECT=sugarcanemle
```

## Como executar a coleta

A execução principal está em:

```text
src/Ingestao/Ingestão_central.py
```

Para rodar o pipeline completo:

```bash
python src/Ingestao/Ingestão_central.py
```

Esse script:

1. busca dados meteorológicos da OpenMeteo para a coordenada;
2. busca condições climáticas atuais da OpenWeather;
3. acessa a coleção Sentinel-2 no GEE;
4. calcula um NDVI médio para a área;
5. consolida tudo em um dicionário Python;
6. salva os resultados em JSON na pasta `data/`.

## Exemplo de saída

O resultado final é um objeto como:

```json
{
  "id_coleta": "RP_Talhao_Central_2026-08-13T15",
  "metadados": {
    "talhao": "RP_Talhao_Central",
    "lat": -21.1775,
    "lon": -47.8103,
    "data_hora_extracao": "2026-08-13T15:00:00"
  },
  "atmosfera": {
    "condicao": "clear sky",
    "vento_velocidade_kmh": 12.4,
    "temp_ar_atual": 24.6
  },
  "solo_e_hidrico": {
    "evapotranspiracao_mm": 0.8,
    "temp_solo_18cm": 25.2,
    "umidade_solo_raiz": 0.35,
    "radiacao_solar": 550.1
  },
  "saude_vegetativa": {
    "data_satelite": "2026-08-11",
    "ndvi_medio": 0.6432
  }
}
```

## Notebooks e exploração

Há um notebook inicial em:

```text
notebook/earthengine_geemap_starter.ipynb
```

Ele serve para testar:

- importação das bibliotecas;
- autenticação no GEE;
- renderização de mapa com `geemap`;
- primeiros experimentos visuais com dados geoespaciais.

## Observações importantes

- A coleta de dados e o cálculo de NDVI dependem de internet e de acesso às APIs externas.
- O GEE requer autenticação e um projeto Google Cloud válido.
- A chave da OpenWeather precisa estar configurada no arquivo `.env` antes da execução.
- O projeto está em fase inicial de desenvolvimento, então partes do pipeline podem ser ajustadas conforme novos casos de uso surgirem.

## Próximos passos sugeridos

- parametrizar coordenadas e nomes de talhão via arquivo de configuração;
- salvar dados em CSV/Parquet além de JSON;
- criar dashboards com visualização de séries temporais;
- incorporar modelos preditivos para produtividade ou estresse hídrico;
- automatizar a coleta em intervalos periódicos.

## Licença

Este projeto está em desenvolvimento e pode ser ajustado conforme a necessidade da equipe ou do uso final.
