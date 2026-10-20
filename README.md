# 🌱 OmniCrop AI

[![CI Status](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/pytest-193%20passed-brightgreen?logo=pytest&logoColor=white)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Core Coverage](https://img.shields.io/badge/coverage-100%25%20core-brightgreen?logo=codecov&logoColor=white)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Security Policy](https://img.shields.io/badge/security-policy-blue?logo=shield&logoColor=white)](docs/SECURITY.md)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Cloud](https://img.shields.io/badge/Azure-Data%20Lake%20Medallion-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?logo=streamlit&logoColor=white)](https://omnicropai.streamlit.app)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-informational)](https://blog.cleancoder.com/)

OmniCrop AI é um **SaaS de Inteligência Agronômica e Sistema de Suporte à Decisão (DSS)** voltado para o agronegócio de precisão. Suporta 5 culturas agrícolas com calibração biofísica e modelos dedicados (**Cana-de-Açúcar, Soja, Milho, Café e Pecuária/Pastagem**), funcionando como um agrônomo virtual que monitora lavouras e fornece recomendações preditivas operacionais em tempo real.

A plataforma unifica:
- **Satélite Virtual Preditivo:** Modelos de Machine Learning (`HistGradientBoostingRegressor`) para projeção do vigor vegetativo (NDVI) sem depender de passagens orbitais sujeitas a nuvens;
- **Arquitetura Medalhão no Azure Blob Storage:** Ingestão climática contínua e telemetria particionada em camadas Bronze, Silver e Gold;
- **Explicabilidade Matemática (XAI Waterfall):** Decomposição marginal do impacto isolado de cada variável meteorológica na tomada de decisão;
- **Copilot Agronômico Generativo:** RAG Grounded em dados da Camada Ouro com Google Gemini e fallback heurístico offline;
- **Headless REST API (FastAPI):** Microsserviços assíncronos com documentação Swagger interativa para integração com ERPs (TOTVS, SAP) e telemetria de máquinas agrícolas;
- **Segurança Defensiva em Camadas:** Validação estrita de contratos com Pydantic v2, mitigação de SSRF em webhooks, proteção contra Stored XSS e isolamento Multi-Tenant com Row-Level Security (RLS).

👉 **Acesse a aplicação em produção:** [omnicropai.streamlit.app](https://omnicropai.streamlit.app)

---

## 🏗️ Arquitetura do Sistema e MLOps

O repositório está estruturado no padrão **Clean Architecture**, isolando totalmente a interface visual da lógica pesada de machine learning e engenharia de dados, garantindo ao mesmo tempo compatibilidade nativa com o **Streamlit Community Cloud**:

```text
OmniCrop/
│
├── 📂 .github/workflows/        # ☁️ Orquestração Serverless & CI/CD
│   ├── ci.yml                   # Pipeline de CI com Gate estrito de 100% de Cobertura e SCA pip-audit
│   └── ingest_weather_azure.yml # Ingestão Diária Medallion na Azure e MLOps
│
├── 📂 deploy/                   # 🐳 Configurações de Containerização e Infraestrutura
│   ├── Dockerfile               # Imagem de Produção Multi-Serviço (API FastAPI e Streamlit)
│   └── docker-compose.yml       # Orquestração local de containers (API, Streamlit e Redis)
│
├── 📂 requirements/             # 📦 Gestão Modular de Dependências
│   └── dev.txt                  # Dependências completas de desenvolvimento, API e testes
│
├── 📄 app.py                    # 🎨 A VITRINE (Ponto de entrada Streamlit & Painel Geral)
├── 📂 pages/                    # Telas navegáveis (Simulador, Análise, Minha Fazenda, Configurações, Assistente)
├── 📂 components/               # Blocos visuais reutilizáveis (Auth, Header, Gráficos, PDF, Landing, Styles)
├── 📂 assets/                   # Identidade visual, logotipos e temas
│
├── 📂 src/                      # ⚙️ O MOTOR (Core de Regras de Negócio e Engenharia)
│   ├── 📂 api/                  # 🚀 Camada REST Headless (FastAPI + Pydantic v2 + Swagger)
│   │   ├── main.py              # Aplicação principal, CORS restrito e Structured Logging
│   │   ├── dependencies.py      # Injeção de dependência e autenticação JWT RLS
│   │   ├── 📂 routers/          # Endpoints (/health, /predict, /farms, /copilot, /telemetry, /reports, /mlops, /audit, /jobs)
│   │   └── 📂 schemas/          # Schemas Pydantic v2 estritos de I/O com limites de plausibilidade física
│   ├── 📂 core/                 # Dicionário Biológico, Structured Logging, Cache e Background Jobs
│   │   ├── cache.py             # Caching Centralizado (Redis + Fallback Resiliente em Memória TTL)
│   │   ├── jobs.py              # Gerenciador de Background Jobs Assíncronos e Filas em Lote
│   │   ├── crop_config.py       # Registro biológico (Cana, Soja, Milho, Café, Pecuária)
│   │   ├── logger.py            # Structured Logging (JSON) com mascaramento de segredos e trace_id
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
├── 📂 docs/                     # 📚 Documentação Técnica de Arquitetura e Governança
│   ├── BIG_DATA_ARCHITECTURE.md # Blueprint Corporativo de Big Data Lakehouse & PySpark
│   ├── SECURITY.md              # Política de Segurança e Reporte Responsável
│   └── 📂 notebooks/            # Notebooks de pesquisa e exploração de dados (Linguist Vendored)
│
├── 📂 tests/                    # 🛡️ Pirâmide de Testes Automatizados (193 Testes / 100% Cobertura)
│   ├── conftest.py              # Fixtures, mocks e payloads de teste
│   ├── 📂 unit/                 # Testes unitários (Features, Modelos, XAI, DSS, Drift, IoT, Geo, HF Registry)
│   ├── 📂 integration/          # Testes de integração (Contratos Pydantic, Azure Blob Storage, DB RLS, REST API)
│   └── 📂 e2e/                  # Testes End-to-End da interface via Streamlit AppTest
│
├── 📄 .gitattributes            # ⚙️ Configuração do Git & GitHub Linguist (99.8% Python)
├── 📄 .gitignore                # ⚙️ Filtros de arquivos ignorados pelo Git
├── 📄 pyproject.toml            # ⚙️ Configuração unificada do projeto (Build, Pytest e Coverage 100%)
├── 📄 requirements.txt          # 📦 Dependências enxutas de produção (exigido na raiz pelo Streamlit Cloud)
└── 📄 README.md                 # 📖 Documentação do repositório
```

### 🛠 Stack Tecnológica
- **A Vitrine (Frontend) & GenAI:** Streamlit 1.64 (UI), Supabase (PostgreSQL + PostGIS + RLS), Google Gemini 1.5/2.5/3.6 Flash.
- **Engenharia de Dados (A Fábrica Medalhão):** 
  - **Azure Blob Storage:** Contêineres `omnicrop-data-lake-bronze` (JSON bruto particionado), `omnicrop-data-lake-silver` (Parquet enriquecido) e `omnicrop-data-lake-gold` (KPIs executivos agregados).
  - **Orquestração Serverless:** GitHub Actions (Pipelines automatizados de CI/CD e ingestão climática diária).
  - **Processamento Colunar:** `pandas` e `pyarrow`.
- **Inteligência Preditiva & XAI:** `HistGradientBoostingRegressor` (Scikit-Learn), Decomposição Marginal e Gráficos Waterfall para Explicabilidade de Decisão. 
- **Garantia de Qualidade & MLOps:** `pytest` (**193/193 testes passando, 100.0% de cobertura estrita**), `pip-audit` (SCA contra CVEs), `Pydantic v2` (Contratos de Dados na camada Bronze e Telemetria IoT), `unittest.mock` (Resiliência contra falhas de I/O e rede).


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

## 🛡️ Pirâmide de Testes MLOps (Qualidade Blindada - 193 Testes / 100% Cobertura)

O projeto implementa uma esteira completa de validação contínua com **193 testes automatizados** e **100.0% de cobertura estrita de código** (`--cov-fail-under=100`) em todas as camadas de lógica de negócio (`src/`) e utilitários (`scripts/`):

1. **Testes Unitários de Motor (`tests/unit/` - 14 suítes / ~130 testes):**
   - `test_model.py`: Testes de stress sintético, integridade dos 5 regressores de NDVI e algoritmo de explicabilidade XAI Waterfall (`test_xai_explain_prediction_delta`).
   - `test_features.py`: Validação matemática de Graus-Dia Acumulados (GDA dinâmico por cultura) e janelas de chuva acumulada (30d, 60d, 90d).
   - `test_dss.py`: Regras de negócio agronômico, zoneamento agroclimático e despacho seguro de alertas operacionais (`test_dispatch_operational_alerts`).
   - `test_cache_and_jobs.py`: Cache híbrido geocodificado (Redis + Memória TTL) e orquestração de background jobs assíncronos.
   - `test_resilience_and_logging.py`: Circuit breakers (`pybreaker`), Structured Logging em JSON com mascaramento de segredos e trace_id.
   - `test_data_drift.py`: Monitoramento estatístico de drift populacional (PSI e Kolmogorov-Smirnov) com alertas de degradação de modelo.
   - `test_hf_registry.py`: Versionamento, download sob demanda e fallback offline com Hugging Face Hub Model Registry.
   - `test_geo.py` & `test_farm_config.py`: Validação de georreferenciamento, centroides espaciais, polígonos GeoJSON e sanitização anti-XSS.
   - `test_iot_simulator.py`: Ingestão sintética de solo/folha e validação física anti-tampering (ISA-62443 FR 3).
   - `test_pdf_generator.py`: Compilação binária de laudos executivos com gráficos e parecer técnico.
2. **Testes de Integração e Contrato (`tests/integration/` - ~60 testes):**
   - `test_data.py`: Contratos Pydantic de dados climáticos da Open-Meteo, bloqueio de payloads corrompidos e esteiras Azure Medallion (Silver Parquet e Gold KPIs).
   - `test_db.py`: Persistência relacional no Supabase PostgreSQL, controle Multi-Tenant com RLS (Row-Level Security) e trilha de auditoria LGPD/GDPR.
   - `test_api.py`: Cobertura completa de todos os endpoints RESTful FastAPI (Health, Predict, Farms, Copilot, Telemetry, Reports, MLOps, Audit, Jobs, Cache) com autenticação JWT e validação de schemas Pydantic v2.
3. **Testes End-to-End e Interface (`tests/e2e/test_ui.py`):**
   - Simulação de cliques, rotas, persistência de cookies e ciclos de vida do Streamlit usando o framework nativo `AppTest` sem necessidade de abrir navegador.

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

**✅ Fase 2: Cloud Data Engineering, MLOps & Arquitetura Segura (Concluída)**
- Migração para arquitetura **Clean Architecture** e deploy contínuo no Streamlit Cloud.
- Implantação da esteira Medallion completa no **Azure Blob Storage** (`omnicrop-data-lake-bronze`, `silver` e `gold`).
- **Pirâmide de Testes Automatizada:** **193 testes validados com 100.0% de cobertura estrita**.
- Contratos de dados estritos com **Pydantic v2** e proteção de resiliência via **Mocks**.
- Implementação de Explicabilidade de Decisão (XAI Waterfall) e Alertas Proativos por Webhook com mitigação de SSRF.
- **Camada de API RESTful Headless** em FastAPI (`src/api/`) com Pydantic v2, Swagger UI, JWT RLS e background jobs assíncronos.
- **Segurança da Informação e Boas Práticas:**
  - Auditoria automatizada de dependências com `pip-audit` no pipeline de CI;
  - Política de Segurança transparente e reporte responsável em [`docs/SECURITY.md`](docs/SECURITY.md);
  - Validação estrita de limites físicos e integridade na telemetria IoT via Pydantic v2;
  - Trilha de auditoria operacional em `audit_logs` e registro de incidentes;
  - Proteção contra Stored XSS com sanitização HTML em cabeçalhos e configurações.

**⏳ Fase 3: IoT Ground Truth & MLOps em Escala Industrial (Planejada)**
- Expansão do Data Lake via orquestração MQTT em tempo real.
- Ingestão contínua de tensiômetros e termometria infravermelha no dossel da lavoura.
- Pipeline de retreinamento contínuo automatizado com dados Ground Truth coletados no campo.

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

## 🔒 Cibersegurança & Proteção em Camadas (Defense-in-Depth)

O OmniCrop AI adota práticas defensivas em código para garantir a integridade da aplicação, proteção contra manipulação de dados e isolamento entre usuários:

### 1. 🛡️ Gestão de Dependências e Vulnerabilidades Conhecidas (SCA)
- **Auditoria Automatizada:** Pipeline de CI com `pip-audit`, bloqueando bibliotecas com vulnerabilidades conhecidas (CVEs) antes de qualquer deploy em produção.
- **Política de Segurança Transparente:** Diretrizes de reporte responsável de vulnerabilidades disponíveis em [`docs/SECURITY.md`](docs/SECURITY.md).

### 2. 🧱 Validação Estrita e Integridade de Dados
- **Validação de Limites Físicos:** Regras estritas nos schemas Pydantic (`TelemetryPayload`) para telemetria de campo, rejeitando injeções de dados sintéticos forjados fora de limites termodinâmicos e elétricos plausíveis (temperatura do solo de -20°C a 70°C, bateria de 0 a 24V, RSSI de -140 a 0 dBm, lote máximo de 1.000 leituras).
- **Mitigação Estrita de SSRF (Server-Side Request Forgery):** Resolução prévia de DNS e bloqueio determinístico de endereços IP privados, de loopback e link-local (`ipaddress.is_private`) nos despachos de webhooks de alerta (`src/utils/daily_alerts.py`).
- **Defesa contra Injeção & Stored XSS:** Sanitização com `html.escape()` na exibição de dados de fazendas e nomes de usuários, isolamento criptográfico via Row-Level Security (RLS) no PostgreSQL e validação regex de formatos de entrada.
- **Mascaramento de Segredos em Logs:** O formatador estruturado `StructuredJsonFormatter` ofusca chaves sensíveis (`password`, `token`, `secret`, `api_key`) com hashes `***REDACTED***` automaticamente.

---

## 🐳 Orquestração de Containers (Docker & Docker Compose)

Para rodar todo o ecossistema corporativo (API Headless + Dashboard Streamlit + Caching Redis) em produção com um único comando a partir da pasta `deploy/`:

```bash
# 1. Subir todos os serviços conteinerizados em background:
docker compose -f deploy/docker-compose.yml up -d

# 2. Visualizar logs unificados em tempo real:
docker compose -f deploy/docker-compose.yml logs -f

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
# Para execução da vitrine em produção (Streamlit Cloud):
pip install -r requirements.txt

# Para desenvolvimento completo (API FastAPI, suíte de 193 testes com 100% de cobertura e auditoria SCA):
pip install -r requirements/dev.txt

# 4. Configure as variáveis de ambiente (.env ou .streamlit/secrets.toml)
# Requer: SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, AZURE_CONNECTION_STRING

# 5. Auditoria de vulnerabilidades em dependências (SCA)
pip-audit -r requirements.txt --desc

# 6. Execute a suíte completa de testes com gate estrito de 100% de cobertura (193 testes)
pytest --cov=src --cov=scripts --cov-fail-under=100 -v

# 7. Inicie a API RESTful Headless (FastAPI)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 8. Inicie a aplicação Web (Streamlit)
streamlit run app.py
```
