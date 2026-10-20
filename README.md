# 🌱 OmniCrop AI

[![CI Status](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/pytest-190%20passed-brightgreen?logo=pytest&logoColor=white)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Core Coverage](https://img.shields.io/badge/coverage-100%25%20core-brightgreen?logo=codecov&logoColor=white)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Cloud](https://img.shields.io/badge/Azure-Data%20Lake%20Medallion-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-informational)](https://blog.cleancoder.com/)

OmniCrop AI é um **Sistema de Suporte à Decisão (DSS)** voltado para a gestão inteligente de culturas agrícolas. Suporta múltiplas culturas (Cana-de-Açúcar, Soja, Milho, Café e Pastagem), funcionando como um agrônomo virtual que monitora lavouras e fornece recomendações preditivas para operações de campo.

A aplicação consolida dados climáticos em tempo real, modelos de Machine Learning (`HistGradientBoostingRegressor`) para estimativa de vigor vegetativo (NDVI), Inteligência Artificial Generativa (Google Gemini) para gerar pareceres executivos e Engenharia de Dados Serverless na nuvem com **Arquitetura Medalhão no Azure Blob Storage** (Bronze, Silver e Gold).

---

## 🏗️ Arquitetura do Sistema e MLOps

O repositório está estruturado no padrão **Clean Architecture**, isolando totalmente a interface visual da lógica pesada de machine learning e engenharia de dados, garantindo ao mesmo tempo compatibilidade nativa com o **Streamlit Community Cloud**:

```text
OmniCrop/
│
├── 📂 .github/workflows/        # ☁️ Orquestração Serverless (CI/CD)
│   ├── ci.yml                   # Pipeline de CI com Gate estrito de 100% de Cobertura
│   └── ingest_weather_azure.yml # Ingestão Diária Medallion na Azure e MLOps
│
├── 📄 app.py                    # 🎨 A VITRINE (Ponto de entrada Streamlit & Painel Geral)
├── 📂 pages/                    # Telas navegáveis (Simulador, Análise, Fazenda, Assistente)
├── 📂 components/               # Blocos visuais reutilizáveis (Auth, Header, Gráficos, PDF, Landing)
├── 📂 assets/                   # Identidade visual, logotipos e temas
│
├── 📂 src/                      # ⚙️ O MOTOR (Core de Regras de Negócio e Engenharia)
│   ├── 📂 api/                  # 🚀 Camada REST Headless (FastAPI + Pydantic v2 + Swagger)
│   │   ├── main.py              # Aplicação principal, CORS e Exception Handlers
│   │   ├── dependencies.py      # Injeção de dependência e autenticação JWT RLS
│   │   ├── 📂 routers/          # Endpoints (/health, /predict, /farms, /copilot, /telemetry, /reports, /mlops, /audit, /jobs)
│   │   └── 📂 schemas/          # Schemas Pydantic v2 estritos de I/O (Copilot, Farm, Predict, Jobs, etc.)
│   ├── 📂 core/                 # Dicionário Biológico, Structured Logging, Cache e Background Jobs
│   │   ├── cache.py             # Caching Centralizado (Redis + Fallback Resiliente em Memória TTL)
│   │   ├── jobs.py              # Gerenciador de Background Jobs Assíncronos e Filas em Lote
│   │   ├── crop_config.py       # Registro biológico (Cana, Soja, Milho, Café, Pecuária)
│   │   ├── logger.py            # Structured Logging (JSON) com trace_id e latência
│   │   └── resilience.py        # Circuit Breakers (pybreaker) para Open-Meteo, Gemini e Azure
│   ├── 📂 data/                 # Conexões (Supabase DB/RLS, Ingestão Azure Medallion, Schemas Pydantic)
│   ├── 📂 features/             # Engenharia de Features Agronômicas (GDA dinâmico, Balanço Hídrico)
│   ├── 📂 models/               # Model Routing por cultura, Inferência, Modelos .pkl e Explicabilidade XAI
│   ├── 📂 mlops/                # Monitoramento de Data Drift e Hugging Face Model Registry
│   │   ├── data_drift.py        # Pop. Stability Index e Kolmogorov-Smirnov
│   │   └── hf_registry.py       # Distribuição de Modelos no Hugging Face Hub com Fallback Local
│   ├── 📂 pipelines/            # Motor Híbrido Polyglot (Pandas Edge & Apache Spark Distribuído)
│   │   └── 📂 spark/            # Jobs de cluster (Silver, Gold Batch e requirements-spark.txt)
│   ├── 📂 reports/              # Emissor de Laudos e Pareceres Agronômicos em PDF (FPDF2)
│   └── 📂 utils/                # Configurações de fazenda, geolocalização PostGIS e alertas diários
│
├── 📂 scripts/                  # 🛠️ Automações Operacionais e Simuladores
│   ├── simulate_iot_sensors.py  # Simulador de Telemetria de Sensores de Campo (Solo e Folha)
│   └── 📂 sql/                  # DDL de Banco de Dados (Supabase PostgreSQL + PostGIS + RLS + Audit)
│
├── 📂 docs/                     # 📚 Documentação Técnica de Arquitetura
│   └── BIG_DATA_ARCHITECTURE.md # Blueprint Corporativo de Big Data Lakehouse & PySpark
│
├── 📂 tests/                    # 🛡️ Pirâmide de Testes Automatizados (190 Testes / 100% Cobertura)
│   ├── conftest.py              # Fixtures, mocks e payloads de teste
│   ├── 📂 unit/                 # Testes unitários (Features, Modelos, XAI, DSS, Drift, IoT, Geo, HF Registry)
│   ├── 📂 integration/          # Testes de integração (Contratos Pydantic, Azure Blob Storage, DB RLS, REST API)
│   └── 📂 e2e/                  # Testes End-to-End da interface via Streamlit AppTest
│
├── 🐳 Dockerfile                # 📦 Containerização de Produção Multi-Serviço
├── 🐙 docker-compose.yml        # 🚀 Orquestração de Containers (API, Streamlit e Redis)
├── 📄 pyproject.toml            # ⚙️ Configuração unificada do projeto (Build, Pytest e Coverage 100%)
└── 📄 requirements.txt          # 📦 Dependências de produção
```

### 🛠 Stack Tecnológica
- **A Vitrine (Frontend) & GenAI:** Streamlit (UI), Supabase (PostgreSQL + RLS), Google Gemini Pro.
- **Engenharia de Dados (A Fábrica Medalhão):** 
  - **Azure Blob Storage:** Contêineres `omnicrop-data-lake-bronze` (JSON bruto particionado), `omnicrop-data-lake-silver` (Parquet enriquecido) e `omnicrop-data-lake-gold` (KPIs executivos agregados).
  - **Orquestração Serverless:** GitHub Actions (Pipelines automatizados de CI/CD e ingestão climática diária).
  - **Processamento Colunar:** `pandas` e `pyarrow`.
- **Inteligência Preditiva & XAI:** `HistGradientBoostingRegressor` (Scikit-Learn), Decomposição Marginal e Gráficos Waterfall para Explicabilidade de Decisão. 
- **Garantia de Qualidade & MLOps:** `pytest` (135/135 testes passando, 100% de cobertura no Core), `Pydantic` (Contratos de Dados na camada Bronze), `unittest.mock` (Resiliência contra falhas de I/O e rede).


---

## ☁️ Arquitetura de Dados em Nuvem (Medallion Data Lake)

O OmniCrop AI adota a **Arquitetura Medalhão** corporativa na nuvem Azure:

```text
  [ Open-Meteo API ]
          │
          ▼ (Validação de Contrato Pydantic)
  ┌──────────────────────────────────────────────┐
  │ 📦 Camada BRONZE                             │
  │ Contêiner: omnicrop-data-lake-bronze         │
  │ Formato: JSON particionado por ano/mês       │
  │ Finalidade: Dados brutos, auditoria e backup │
  └──────────────────────────────────────────────┘
          │
          ▼ (Limpeza & Feature Engineering)
  ┌──────────────────────────────────────────────┐
  │ ⚙️ Camada SILVER                             │
  │ Contêiner: omnicrop-data-lake-silver         │
  │ Formato: Apache Parquet (colunar compactado) │
  │ Features: GDA (Graus-Dia), Chuva 7d, Nulos   │
  │ Finalidade: Treinamento e consumo analítico  │
  └──────────────────────────────────────────────┘
          │
          ▼ (Agregação Executiva & Regras DSS)
  ┌──────────────────────────────────────────────┐
  │ 🏆 Camada GOLD                               │
  │ Contêiner: omnicrop-data-lake-gold           │
  │ Formato: Apache Parquet (KPIs sumarizados)   │
  │ Features: Balanço Hídrico, Veranicos, Alertas│
  │ Finalidade: Dashboards Executivos & BI       │
  └──────────────────────────────────────────────┘
```

---

## 🛡️ Pirâmide de Testes MLOps (Qualidade Blindada)

O projeto implementa uma esteira completa de validação com **19 testes automatizados** em 3 camadas independentes:

1. **Testes de Contrato e Qualidade de Dados (`tests/integration/test_data.py`):**
   - Validação estrita de contratos via **Pydantic** (`src/data/schemas.py`) para inspecionar payloads da Open-Meteo antes de gravar na nuvem.
   - Bloqueio automático de payloads corrompidos ou com chaves faltantes (`precipitation_sum`).
   - Mocks de resiliência HTTP 500 para evitar injeção de dados corrompidos caso APIs externas fiquem fora do ar.
   - Validação da transformação da esteira **Silver** (`test_transform_to_silver_pipeline`).
   - Validação da agregação e regras de decisão da esteira **Gold** (`test_transform_to_gold_pipeline`).
2. **Testes Unitários de Motor (`tests/unit/`):**
   - `test_features.py`: Validação matemática de Graus-Dia Acumulados (GDA) e janelas de chuva (30d, 60d, 90d).
   - `test_model.py`: Testes de stress sintético, integridade do regressor de NDVI e algoritmo de explicabilidade XAI (`test_xai_explain_prediction_delta`).
   - `test_dss.py`: Validação das regras de negócio agronômico e despacho de alertas operacionais (`test_dispatch_operational_alerts`).
3. **Testes End-to-End de Interface (`tests/e2e/test_ui.py`):**
   - Simulação de cliques, rotas e estados de sessão do Streamlit usando o framework nativo `AppTest` sem necessidade de navegador aberto.

---

## 🧠 Design Matemático e Segurança (Blueprint)

O cérebro do OmniCrop AI é alimentado por variáveis agronômicas profundas:

- **Explicabilidade de IA (XAI):** Decomposição gráfica (Waterfall) do impacto isolado de cada atributo climático na projeção do NDVI, quebrando a "caixa preta" do modelo.
- **Feature Engineering Avançado:** Ingestão de Graus-Dia Acumulados (GDA base 18°C para cana) e janelas móveis de chuva de longo prazo (Lags de 30, 60, 90 dias) para simular a "memória hídrica" do solo e da cultura.
- **Time-Series Walk-Forward:** O modelo preditivo evita vazamento de dados (*Data Leakage*) garantindo aderência temporal.
- **Testes de Fronteira Extrema:** A esteira de testes injeta anomalias de "Seca Severa" e "Enchente" para validar a estabilidade das predições do índice NDVI (0 a 1).
- **Zero-Trust (RLS):** Toda comunicação com o banco de dados trafega o token JWT do usuário ativo, garantindo isolamento estrito entre fazendas (Row-Level Security no Supabase com fallback seguro para CI/CD).

---

## 🌾 Funcionalidades (Visão do Usuário)

O que gestores, produtores e engenheiros agrônomos encontram no sistema:

1. **Dashboard de Satélite Virtual (NDVI):** Acompanha o vigor vegetativo atual e futuro da cultura sem depender da passagem de satélites reais (mitigação de nuvens e *delay* temporal).
2. **Simulador "What-if" com Explicabilidade XAI:** Simula cenários operacionais (irrigação, adubação, maturador, plantio e colheita) e exibe o gráfico Waterfall detalhando o impacto exato de cada variável na decisão da IA.
3. **Gerador de Laudos Executivos:** Emite pareceres formais em PDF com recomendações geradas pelo Agrônomo Virtual (GenAI).
4. **Onboarding Georreferenciado:** Criação interativa de fazendas mapeadas por coordenadas de Latitude e Longitude para cruzamento meteorológico em tempo real.
5. **Assistente de Manejo:** Chatbot agronômico inteligente (RAG via Gemini) contextualizado nos dados da fazenda selecionada.
6. **Alertas Operacionais Proativos:** Roteador multicanal para notificações automáticas via Webhook (Discord, Slack, Zapier) e E-mail sempre que riscos críticos forem detectados.

---

## 🗓️ Roadmap de Engenharia

**✅ Fase 1: MVP Streamlit e GenAI (Concluída)**
- Autenticação e Multi-Tenancy com Supabase.
- Renderização de mapas, dashboards analíticos e laudos executivos.
- Integração do modelo de Machine Learning base e Google Gemini.

**✅ Fase 2: Cloud Data Engineering e MLOps (Concluída)**
- Migração para arquitetura **Clean Architecture** e deploy contínuo no Streamlit Cloud.
- Implantação da esteira Medallion completa no **Azure Blob Storage** (`omnicrop-data-lake-bronze`, `silver` e `gold`).
- Pirâmide de Testes automatizada (Unit, Integration, E2E) com 19 testes validados.
- Contratos de dados estritos com **Pydantic** e proteção de resiliência via **Mocks**.
- Implementação de Explicabilidade de Decisão (XAI Waterfall) e Alertas Proativos por Webhook.
- **Camada de API RESTful Headless** em FastAPI (`src/api/`) com Pydantic v2, Swagger UI e 144 testes automatizados com 100% de cobertura.

**⏳ Fase 3: IoT Ground Truth & MLOps Avançado (Planejada)**
- Expansão do Data Lake via orquestração MQTT.
- Coleta primária via Tensiômetros e Termometria Infravermelha no dossel da lavoura.
- Retreinamento contínuo do modelo utilizando dados Ground Truth.

---

## ⚡ Camada de API Headless (FastAPI + Swagger UI)

Além da vitrine web em Streamlit, o OmniCrop AI fornece uma **API RESTful de alta performance**, permitindo que ERPs agrícolas (TOTVS Agro, SAP), aplicativos móveis para técnicos em campo e telemetria de maquinários agrícolas (John Deere, Case IH) consumam o cérebro do sistema:

- **Swagger UI Interativo:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

### 📋 Catálogo de Endpoints Principais:

| Método | Endpoint | Descrição |
| :---: | :--- | :--- |
| `GET` | `/health` | Health Check e versão da API |
| `POST` | `/api/v1/predict/ndvi` | Inferência do Satélite Virtual + Decomposição XAI Waterfall + Decisão DSS |
| `GET` | `/api/v1/farms` | Listagem de fazendas do usuário com polígonos GeoJSON (Multi-Tenant RLS) |
| `POST` | `/api/v1/farms` | Cadastro de nova propriedade com georreferenciamento |
| `PUT` | `/api/v1/farms/{id}` | Atualização cadastral ou espacial de fazenda |
| `DELETE` | `/api/v1/farms/{id}` | Exclusão de fazenda |
| `GET` | `/api/v1/farms/{id}/gold-kpis` | Obter KPIs mais recentes da Camada Ouro (Balanço Hídrico, GDA, Veranico) para consumo BI/ERP |
| `POST` | `/api/v1/copilot/ask` | Assistente de Manejo Agronômico determinístico e generativo (RAG Grounded + Fallback) |
| `POST` | `/api/v1/telemetry/iot` | Ingestão de telemetria horária de solo e folha na Camada Bronze da Azure |
| `POST` | `/api/v1/reports/pdf` | Geração sob demanda do laudo executivo em PDF (stream binário ou Base64) |
| `GET` | `/api/v1/mlops/drift-status` | Auditoria estatística de Data Drift (Population Stability Index e KS) |
| `GET` | `/api/v1/audit/logs` | Trilha de Auditoria LGPD e governança (alterações críticas, laudos e acessos) |
| `POST` | `/api/v1/jobs/batch-kpis` | Disparo assíncrono de cálculo em lote de balanço hídrico para múltiplos talhões (HTTP 202) |
| `POST` | `/api/v1/jobs/batch-reports` | Emissão massiva de laudos técnicos em PDF em background (HTTP 202) |
| `POST` | `/api/v1/jobs/batch-retrain` | Auditoria e calibração de modelos por cultura em background (HTTP 202) |
| `GET` | `/api/v1/jobs/{id}` | Acompanhamento em tempo real de status, progresso e resultados de um job |
| `POST` | `/api/v1/jobs/{id}/cancel` | Cancelamento de tarefa assíncrona em fila ou execução |
| `GET` | `/api/v1/jobs` | Histórico e listagem de jobs com filtro por status |
| `GET` | `/api/v1/cache/stats` | Telemetria do cache centralizado (taxa de acerto, hits, misses e backend) |
| `POST` | `/api/v1/cache/clear` | Invalidação e limpeza total de chaves do cache centralizado |

---

## ⚡ Caching Centralizado (Redis) & Processamento Assíncrono (Background Jobs)

Para operações agrícolas de grande porte (cooperativas com centenas de cooperados e usinas com milhares de talhões), o OmniCrop AI desacopla totalmente requisições de I/O pesado através de dois motores dedicados:

### 1. 🏎️ Cache Centralizado e Resiliente (`src/core/cache.py`)
- **Agrupamento Geoespacial Inteligente:** Cache de predições climáticas por coordenada geocodificada arredondada (`weather:{round(lat, 2)}:{round(lon, 2)}`).
  - Talhões vizinhos ou consultas repetidas no mesmo dia têm tempo de resposta reduzido de **~1.5s para menos de 3ms**.
  - Economia drástica de cota de requisições na API externa da Open-Meteo.
- **Backend Híbrido Pluggable:**
  - Conecta-se automaticamente ao **Redis** em ambientes de produção com cluster distribuído via `REDIS_URL` ou `REDIS_HOST`.
  - Ativa fallback transparente para cache em memória local (`MemoryCacheBackend`) com expiração TTL em ambientes de desenvolvimento ou CI/CD (garantindo zero dependência externa nos testes).
- **Decorador Declarativo `@cached`:** Envolve qualquer função agronômica determinística com caching configurável por TTL.

### 2. 🧵 Fila de Background Jobs Desacoplada (`src/core/jobs.py`)
- **Processamento Assíncrono Não-Bloqueante:** Tarefas pesadas que levariam dezenas de segundos não travam o loop do FastAPI nem o Streamlit.
- **Ciclo de Vida Transparente:** Cada job recebe um UUID imutável e transita pelos estados `pending` ➔ `running` ➔ `completed` / `failed` / `cancelled`, com percentual de progresso dinâmico (0 a 100%) e telemetria sincronizada no cache.
- **Rotinas Agro em Lote Nativas:**
  - `task_batch_kpis`: Processa balanço hídrico, GDA e alertas de déficit para centenas de talhões simultaneamente.
  - `task_batch_reports`: Geração massiva de laudos executivos com download assíncrono.
  - `task_batch_retrain`: Auditoria estatística e calibração de modelos por cultura.

---

## 🛡️ Resiliência, Auditoria e Observabilidade Corporativa

Para garantir confiabilidade de missão crítica em usinas, cooperativas e grandes operações agrícolas, o OmniCrop AI incorpora três pilares de engenharia:

### 1. 📜 Trilha de Auditoria e Governança LGPD (`audit_logs`)
- Registro imutável de todas as ações de impacto operacional no Supabase PostgreSQL:
  - Alterações de limites críticos de alertas (`UPDATE_FARM_ALERT_THRESHOLDS`).
  - Atualizações cadastrais e perimetrais de fazendas (`UPDATE_FARM`).
  - Exportação e download de laudos executivos em PDF (`EXPORT_PDF_REPORT`).
  - Exclusão de propriedades (`DELETE_FARM`).
- **Segurança Multi-Tenant com RLS:** Cada produtor consulta estritamente sua própria trilha de auditoria via `GET /api/v1/audit/logs`.

### 2. ⚡ Circuit Breakers & Proteção contra Lentidão de I/O (`pybreaker`)
- Circuit Breakers dedicados para blindar o sistema contra timeouts ou indisponibilidade em APIs externas:
  - **Open-Meteo Breaker:** Interrompe chamadas climáticas externas em caso de falhas consecutivas, prevenindo travamentos de 15 segundos.
  - **Gemini Breaker:** Ativa fallback heurístico imediato se a API de GenAI estiver instável.
  - **Azure Storage Breaker:** Protege a esteira Medalhão contra lentidão momentânea no Data Lake.
- O estado de cada circuito é exposto em tempo real no endpoint `GET /health`.

### 3. 📊 Structured Logging (JSON) com Rastreabilidade Ponta a Ponta
- Substituição total de prints soltos por logs padronizados em JSON estruturado (compatíveis com Datadog, Grafana Loki, CloudWatch e OpenTelemetry):
  ```json
  {
    "timestamp": "2026-10-19T15:20:00.000Z",
    "level": "INFO",
    "logger": "omnicrop",
    "message": "HTTP POST /api/v1/predict/ndvi -> 200 (12.45ms)",
    "trace_id": "a8f3b4c1-6d92-4e1b-9f7a-2c8b1e4d5a7f",
    "latency_ms": 12.45
  }
  ```
- **Middleware HTTP:** Injeta e propaga automaticamente o header `X-Trace-ID` em cada requisição e cronometra a latência com precisão de microssegundos.

---

## 🐳 Orquestração de Containers (Docker & Docker Compose)

Para rodar todo o ecossistema corporativo (API Headless + Dashboard Streamlit + Caching Redis) em produção com um único comando:

```bash
# 1. Subir todos os serviços conteinerizados em background:
docker compose up -d

# 2. Visualizar logs unificados em tempo real:
docker compose logs -f

# 3. Acessar as portas mapeadas:
# - Headless API REST (FastAPI + Swagger): http://localhost:8000/docs
# - Dashboard Interativo (Streamlit):       http://localhost:8501
# - Redis Centralizado:                   localhost:6379
```

---

## 📦 Hugging Face Hub Model Registry (`src/mlops/hf_registry.py`)

Os 5 modelos preditivos calibrados (`sugarcane`, `soybean`, `corn`, `coffee`, `pasture`) contam com governança e versionamento na nuvem via Hugging Face Model Registry (`phsandoval/omnicrop-ndvi-models`):

- **Download sob Demanda:** Com `USE_HF_HUB=1` ou quando um modelo específico não está presente no disco local, o sistema baixa o artefato serializado `.pkl` diretamente do Hub.
- **Resiliência Offline:** Em caso de oscilação de rede ou execução isolada (air-gapped), o sistema realiza fallback transparente para os artefatos locais.
- **Publicação Automatizada:** O utilitário `publish_models_to_registry()` orquestra a publicação dos artefatos serializados e gera dinamicamente o `MODEL_CARD.md` com metadados e métricas científicas completas.

---

## 📊 Validação Científica & Benchmarks de Modelos (Cross-Validation Temporal 2024–2026)

Métricas reais de acurácia obtidas no conjunto de teste independente (*out-of-time test set*), sem contaminação do passado (*data leakage*), utilizando o algoritmo `HistGradientBoostingRegressor` com calibração fenológica:

| Cultura | Código | Algoritmo | $R^2$ | MAE | RMSE | Comportamento Fisiológico Modelado |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 🌾 **Cana-de-Açúcar** | `sugarcane` | HistGradientBoosting | — | **0.0217** | **0.0315** | Alta precisão no monitoramento do ciclo semi-perene e acúmulo de ATR. |
| 🌿 **Soja** | `soybean` | HistGradientBoosting | **0.8685** | **0.0557** | **0.1122** | Forte correlação no pico vegetativo das fases reprodutivas R1 a R5. |
| 🌽 **Milho** | `corn` | HistGradientBoosting | **0.7053** | **0.1022** | **0.1460** | Robustez frente à alta volatilidade no pendoamento VT-R1. |
| ☕ **Café** | `coffee` | HistGradientBoosting | **0.8801** | **0.0254** | **0.0391** | Estabilidade excelente para dossel contínuo de culturas perenes. |
| 🐄 **Pecuária** | `pasture` | HistGradientBoosting | **0.9674** | **0.0238** | **0.0389** | Precisão superior a 96% na captação do vigor estival da *Brachiaria*. |

> **Nota Metodológica:**
> - **$R^2$ (Coeficiente de Determinação):** Percentual da variação da biomassa fotossinteticamente ativa que o modelo consegue prever (ex: 96,7% na pastagem e 88,0% no café).
> - **MAE (Erro Médio Absoluto):** Erro na escala contínua do NDVI (0 a 1). Um MAE de ~0.02 representa um desvio ínfimo de apenas 2 centésimos em relação ao satélite físico Sentinel-2/MODIS.
> - **Governança Temporal:** Modelos testados rigorosamente em safras subsequentes futuras (2024–2026), garantindo generalização confiável em campo.

---

## 🚀 Como Executar Localmente

```bash
# 1. Clone o repositório
git clone https://github.com/PhSandoval/OmniCrop.AI.git
cd OmniCrop.AI

# 2. Crie e ative um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente (.env ou .streamlit/secrets.toml)
# Requer: SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, AZURE_CONNECTION_STRING

# 5. Execute a suíte completa de testes com gate estrito de 100% de cobertura
pytest --cov=src --cov=scripts --cov-fail-under=100 -v

# 6. Inicie a API RESTful Headless (FastAPI)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Inicie a aplicação Web (Streamlit)
streamlit run app.py
```
