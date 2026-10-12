# 🌱 OmniCrop AI

OmniCrop AI é um **Sistema de Suporte à Decisão (DSS)** voltado para a gestão inteligente de culturas agrícolas. Inicialmente focado em Cana-de-Açúcar, o sistema funciona como um agrônomo virtual, ajudando no monitoramento de lavouras e fornecendo recomendações preditivas para operações de campo.

A aplicação consolida dados climáticos em tempo real, modelos de Machine Learning (`HistGradientBoostingRegressor`) para estimativa de vigor vegetativo (NDVI), Inteligência Artificial Generativa (Google Gemini) para gerar pareceres executivos e Engenharia de Dados Serverless na nuvem com **Arquitetura Medalhão no Azure Blob Storage** (Bronze e Silver).

---

## 🏗️ Arquitetura do Sistema e MLOps

O repositório está estruturado no padrão **Clean Architecture**, isolando totalmente a interface visual da lógica pesada de machine learning e engenharia de dados, garantindo ao mesmo tempo compatibilidade nativa com o **Streamlit Community Cloud**:

```text
OmniCrop/
│
├── 📂 .github/workflows/        # ☁️ Orquestração Serverless (CI/CD)
│   ├── ci_pipeline.yml          # Integração Contínua (Matriz de testes Pytest)
│   └── ingest_weather_azure.yml # Pipeline diário Medallion (Bronze & Silver)
│
├── 📄 app.py                    # 🎨 A VITRINE (Ponto de entrada do Streamlit)
├── 📂 pages/                    # Telas navegáveis (Simulador, Análise, Fazenda, etc.)
├── 📂 components/               # Blocos visuais reutilizáveis (Auth, Header, Gráficos, PDF)
├── 📂 assets/                   # Estilos visuais e logotipos
│
├── 📂 src/                      # ⚙️ O MOTOR (Core de Regras de Negócio)
│   ├── 📂 data/                 # Conexões (DB/Supabase, Ingestão Azure Medalhão, Schemas Pydantic)
│   ├── 📂 features/             # Feature Engineering (GDA, Acúmulos hídricos)
│   ├── 📂 models/               # Inteligência (Treino, Inferência e serialização .pkl)
│   └── 📂 utils/                # Configurações de fazenda e helpers
│
├── 📂 tests/                    # 🛡️ Pirâmide de Testes MLOps (16 Testes Automatizados)
│   ├── conftest.py              # Fixtures e mocks compartilhados
│   ├── 📂 unit/                 # Testes unitários puros (Cálculos de Features, Modelo e DSS)
│   ├── 📂 integration/          # Testes de Contrato Pydantic, Mocks de API e Pipeline Silver
│   └── 📂 e2e/                  # Testes End-to-End da interface via Streamlit AppTest
│
├── 📂 data/                     # 🗄️ Camadas locais do Data Lake (Raw, Interim, Processed)
└── 📂 notebooks/                # 🔬 Laboratório de experimentação e EDA
```

### 🛠 Stack Tecnológica
- **A Vitrine (Frontend) & GenAI:** Streamlit (UI), Supabase (PostgreSQL + RLS), Google Gemini Pro.
- **Engenharia de Dados (A Fábrica Medalhão):** 
  - **Azure Blob Storage:** Contêineres `omnicrop-data-lake-bronze` (JSON bruto particionado) e `omnicrop-data-lake-silver` (Parquet enriquecido).
  - **Orquestração Serverless:** GitHub Actions (Pipelines automatizados de CI/CD e ingestão climática).
  - **Processamento Colunar:** `pandas` e `pyarrow`.
- **Inteligência Preditiva:** `HistGradientBoostingRegressor` (Scikit-Learn). 
- **Garantia de Qualidade & MLOps:** `pytest` (16/16 testes passando), `Pydantic` (Contratos de Dados na camada Bronze), `unittest.mock` (Resiliência contra falhas de API).

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
          ▼ (Transformação & Feature Engineering)
  ┌──────────────────────────────────────────────┐
  │ ⚙️ Camada SILVER                             │
  │ Contêiner: omnicrop-data-lake-silver         │
  │ Formato: Apache Parquet (colunar compactado) │
  │ Features: GDA (Graus-Dia), Chuva 7d, Nulos   │
  │ Finalidade: Treinamento e consumo veloz      │
  └──────────────────────────────────────────────┘
```

---

## 🛡️ Pirâmide de Testes MLOps (Qualidade Blindada)

O projeto implementa uma esteira completa de validação com **16 testes automatizados** em 3 camadas independentes:

1. **Testes de Contrato e Qualidade de Dados (`tests/integration/test_data.py`):**
   - Validação estrita de contratos via **Pydantic** (`src/data/schemas.py`) para inspecionar payloads da Open-Meteo antes de gravar na nuvem.
   - Bloqueio automático de payloads corrompidos ou com chaves faltantes (`precipitation_sum`).
   - Mocks de resiliência HTTP 500 para evitar injeção de dados corrompidos caso APIs externas fiquem fora do ar.
   - Validação da transformação e cálculo da esteira **Silver** (`test_transform_to_silver_pipeline`).
2. **Testes Unitários de Motor (`tests/unit/`):**
   - `test_features.py`: Validação matemática de Graus-Dia Acumulados (GDA) e janelas de chuva (30d, 60d, 90d).
   - `test_model.py`: Testes de stress sintético e integridade do regressor de NDVI.
   - `test_dss.py`: Validação das regras de negócio e tomada de decisão agronômica.
3. **Testes End-to-End de Interface (`tests/e2e/test_ui.py`):**
   - Simulação de cliques, rotas e estados de sessão do Streamlit usando o framework nativo `AppTest` sem necessidade de navegador aberto.

---

## 🧠 Design Matemático e Segurança (Blueprint)

O cérebro do OmniCrop AI é alimentado por variáveis agronômicas profundas:

- **Feature Engineering Avançado:** Ingestão de Graus-Dia Acumulados (GDA base 18°C para cana) e janelas móveis de chuva de longo prazo (Lags de 30, 60, 90 dias) para simular a "memória hídrica" do solo e da cultura.
- **Time-Series Walk-Forward:** O modelo preditivo evita vazamento de dados (*Data Leakage*) garantindo aderência temporal.
- **Testes de Fronteira Extrema:** A esteira de testes injeta anomalias de "Seca Severa" e "Enchente" para validar a estabilidade das predições do índice NDVI (0 a 1).
- **Zero-Trust (RLS):** Toda comunicação com o banco de dados trafega o token JWT do usuário ativo, garantindo isolamento estrito entre fazendas (Row-Level Security no Supabase com fallback seguro para CI/CD).

---

## 🌾 Funcionalidades (Visão do Usuário)

O que gestores, produtores e engenheiros agrônomos encontram no sistema:

1. **Dashboard de Satélite Virtual (NDVI):** Acompanha o vigor vegetativo atual e futuro da cultura sem depender da passagem de satélites reais (mitigação de nuvens e *delay* temporal).
2. **Simulador "What-if" de Intervenção:** Simula gastos (ex: ligar o pivô de irrigação) ou cenários de estresse hídrico, calculando o impacto na produtividade antes da decisão no campo.
3. **Gerador de Laudos Executivos:** Emite pareceres formais em PDF com recomendações geradas pelo Agrônomo Virtual (GenAI).
4. **Onboarding Georreferenciado:** Criação interativa de fazendas mapeadas por coordenadas de Latitude e Longitude para cruzamento meteorológico em tempo real.
5. **Assistente de Manejo:** Chatbot agronômico inteligente (RAG via Gemini) contextualizado nos dados da fazenda selecionada.

---

## 🗓️ Roadmap de Engenharia

**✅ Fase 1: MVP Streamlit e GenAI (Concluída)**
- Autenticação e Multi-Tenancy com Supabase.
- Renderização de mapas, dashboards analíticos e laudos executivos.
- Integração do modelo de Machine Learning base e Google Gemini.

**✅ Fase 2: Cloud Data Engineering e MLOps (Concluída)**
- Migração para arquitetura **Clean Architecture** e deploy contínuo no Streamlit Cloud.
- Implantação da esteira Medallion completa no **Azure Blob Storage** (`omnicrop-data-lake-bronze` em JSON e `omnicrop-data-lake-silver` em Parquet).
- Pirâmide de Testes automatizada (Unit, Integration, E2E) com 16 testes validados.
- Contratos de dados estritos com **Pydantic** e proteção de resiliência via **Mocks**.

**⏳ Fase 3: IoT Ground Truth & MLOps Avançado (Planejada)**
- Expansão do Data Lake via orquestração MQTT.
- Coleta primária via Tensiômetros e Termometria Infravermelha no dossel da lavoura.
- Retreinamento contínuo do modelo utilizando dados Ground Truth.

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

# 5. Execute a suíte de testes (Garantia de Qualidade MLOps)
pytest tests/ -v

# 6. Inicie a aplicação
streamlit run app.py
```
