# 🌱 OmniCrop AI

[![CI Status](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/pytest-144%20passed-brightgreen?logo=pytest&logoColor=white)](https://github.com/PhSandoval/OmniCrop.AI/actions/workflows/ci.yml)
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
├── 📂 components/               # Blocos visuais reutilizáveis (Auth, Header, Gráficos, PDF)
├── 📂 assets/                   # Identidade visual, logotipos e temas
│
├── 📂 src/                      # ⚙️ O MOTOR (Core de Regras de Negócio e Engenharia)
│   ├── 📂 api/                  # 🚀 Camada REST Headless (FastAPI + Pydantic v2 + Swagger)
│   │   ├── main.py              # Aplicação principal, CORS e Exception Handlers
│   │   ├── dependencies.py      # Injeção de dependência e autenticação JWT RLS
│   │   ├── 📂 routers/          # Endpoints (/health, /predict, /farms, /telemetry, /reports, /mlops)
│   │   └── 📂 schemas/          # Schemas Pydantic v2 estritos de I/O
│   ├── 📂 core/                 # Dicionário Biológico das 5 Culturas (Cana, Soja, Milho, Café, Pecuária)
│   ├── 📂 data/                 # Conexões (Supabase DB/RLS, Ingestão Azure Medallion, Schemas Pydantic)
│   ├── 📂 features/             # Engenharia de Features Agronômicas (GDA dinâmico, Balanço Hídrico)
│   ├── 📂 models/               # Model Routing por cultura, Inferência, Modelos .pkl e Explicabilidade XAI
│   ├── 📂 mlops/                # Monitoramento de Data Drift (Pop. Stability Index / Kolmogorov-Smirnov)
│   ├── 📂 pipelines/            # Motor Híbrido Polyglot (Pandas Edge & Apache Spark Distribuído)
│   │   └── 📂 spark/            # Jobs de cluster (Silver, Gold Batch e requirements-spark.txt)
│   ├── 📂 reports/              # Emissor de Laudos e Pareceres Agronômicos em PDF (FPDF2)
│   └── 📂 utils/                # Configurações de fazenda, geolocalização PostGIS e alertas diários
│
├── 📂 scripts/                  # 🛠️ Automações Operacionais e Simuladores
│   ├── simulate_iot_sensors.py  # Simulador de Telemetria de Sensores de Campo (Solo e Folha)
│   └── 📂 sql/                  # DDL de Banco de Dados (Supabase PostgreSQL + PostGIS + RLS)
│
├── 📂 docs/                     # 📚 Documentação Técnica de Arquitetura
│   └── BIG_DATA_ARCHITECTURE.md # Blueprint Corporativo de Big Data Lakehouse & PySpark
│
├── 📂 tests/                    # 🛡️ Pirâmide de Testes Automatizados (144 Testes / 100% Cobertura)
│   ├── conftest.py              # Fixtures, mocks e payloads de teste
│   ├── 📂 unit/                 # Testes unitários (Features, Modelos, XAI, DSS, Drift, IoT, Geo)
│   ├── 📂 integration/          # Testes de integração (Contratos Pydantic, Azure Blob Storage, DB RLS)
│   └── 📂 e2e/                  # Testes End-to-End da interface via Streamlit AppTest
│
├── 📂 data/                     # 🗄️ Camadas locais do Data Lake (Raw, Interim, Processed, Bronze)
├── 📂 notebooks/                # 🔬 Cadernos de análise exploratória de dados (EDA)
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
| `POST` | `/api/v1/telemetry/iot` | Ingestão de telemetria horária de solo e folha na Camada Bronze da Azure |
| `POST` | `/api/v1/reports/pdf` | Geração sob demanda do laudo executivo em PDF (stream binário ou Base64) |
| `GET` | `/api/v1/mlops/drift-status` | Auditoria estatística de Data Drift (Population Stability Index e KS) |

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
