# 🌱 OmniCrop AI

OmniCrop AI é um **Sistema de Suporte à Decisão (DSS)** voltado para a gestão inteligente de culturas agrícolas. Inicialmente focado em Cana-de-Açúcar, o sistema funciona como um agrônomo virtual, ajudando no monitoramento de lavouras e fornecendo recomendações preditivas para operações de campo.

A aplicação consolida dados climáticos em tempo real, modelos de Machine Learning (Gradient Boosting) para estimativa de vigor vegetativo, Inteligência Artificial Generativa (Google Gemini) para gerar pareceres executivos e Data Engineering Serverless na nuvem (Azure).

---

## 🏗️ Arquitetura do Sistema e MLOps

O repositório está estruturado no padrão **Clean Architecture**, isolando totalmente a interface visual da lógica pesada de machine learning e engenharia de dados.

```text
OmniCrop/
│
├── 📂 .github/workflows/        # ☁️ Orquestração Serverless
│   ├── ci_pipeline.yml          # Integração Contínua (Matrix Strategy Pytest)
│   └── ingest_weather_azure.yml # Pipeline de Ingestão Diária programada
│
├── 📂 app/                      # 🎨 A VITRINE (Interface Visual isolada)
│   ├── 📂 pages/                # Telas do Streamlit
│   ├── 📂 components/           # Componentes modulares (UI, PDFs, Gráficos)
│   └── main.py                  # Ponto de entrada (antigo app.py)
│
├── 📂 src/                      # ⚙️ O MOTOR (Core de Regras de Negócio)
│   ├── 📂 data/                 # Conexões (DB, Ingestão Azure, Pydantic Contracts)
│   ├── 📂 features/             # Feature Engineering (Limpeza e Matemática)
│   ├── 📂 models/               # Inteligência (Treino, Inferência Gradient Boosting)
│   └── 📂 utils/                # Utilitários globais
│
└── 📂 tests/                    # 🛡️ Pirâmide de Testes MLOps
    ├── 📂 unit/                 # Testes unitários puros (Cálculos e Modelo)
    ├── 📂 integration/          # Testes com Mocks (Simulando nuvem e APIs)
    └── 📂 e2e/                  # Testes End-to-End da interface via AppTest
```

### 🛠 Stack Tecnológica
- **A Vitrine (Frontend) e IA:** Streamlit (UI), Supabase (PostgreSQL + RLS), Google Gemini Pro.
- **Engenharia de Dados (A Fábrica):** Azure Blob Storage (Data Lake Bronze), GitHub Actions (Orquestração Serverless), Open-Meteo.
- **Inteligência Preditiva:** `HistGradientBoostingRegressor` (Scikit-Learn). 
- **Garantia de Qualidade:** `pytest`, `tenacity` (resiliência), `Pydantic` (contratos).

---

## 🧠 Design Matemático e Segurança (Blueprint)

O cérebro do OmniCrop AI não usa médias históricas simples, ele é alimentado por variáveis agronômicas profundas (Oceano e Planta):

- **Feature Engineering Avançado:** Ingestão de Graus-Dia Acumulados (GDA) e janelas móveis de chuva de longo prazo (Lags de 30, 60, 90 dias) para simular a "memória hídrica" da cultura.
- **Time-Series Walk-Forward:** O modelo preditivo foi testado via validação de janela deslizante para evitar vazamento de dados (*Data Leakage*), simulando o mundo real.
- **Testes de Fronteira Extrema:** A esteira de testes injeta anomalias de "Seca Severa" e "Enchente" para forçar e validar os limites estritos da predição matemática do índice NDVI (0 a 1).
- **Zero-Trust (RLS):** Toda comunicação com o banco de dados trafega o token JWT do usuário ativo, impossibilitando o acesso cruzado de dados entre fazendas concorrentes na plataforma (Row-Level Security).

---

## 🌾 Funcionalidades (Visão do Usuário)

O que gestores, produtores e engenheiros agrônomos podem fazer no sistema:

1. **Dashboard de Satélite Virtual (NDVI):** Acompanha o vigor vegetativo atual e futuro da cultura sem depender da passagem de satélites reais (mitigação de nuvens e *delay* temporal).
2. **Simulador "What-if" de Intervenção:** Simula gastos (ex: ligar o pivô de irrigação) ou cenários de desastre climático, observando a reação matemática da produtividade antes de tomar a decisão no mundo real.
3. **Gerador de Laudos Executivos:** Emite pareceres formais formatados em PDF redigidos pelo Agrônomo Virtual (GenAI).
4. **Onboarding Georreferenciado:** Criação interativa de fazendas mapeadas fisicamente por coordenadas de Latitude e Longitude para cruzar dados climáticos precisos.
5. **Assistente de Manejo:** Chatbot agronômico inteligente (RAG via Gemini) isolado para discussão do contexto da fazenda selecionada.

---

## 🗓️ Roadmap de Engenharia

**✅ Fase 1: MVP Streamlit e GenAI (Concluída)**
- Autenticação e Multi-Tenancy (Supabase).
- Renderização do mapa de lavouras e dashboards analíticos dinâmicos.
- Integração do modelo Gradient Boosting base e Google Gemini.

**✅ Fase 2: Cloud Data Engineering e MLOps (Concluída)**
- Migração de infraestrutura pesada (Airflow/Docker local) para **Cloud Serverless**.
- Implantação do Data Lake Bronze no **Azure Blob Storage**.
- Implantação da Pirâmide de Testes nativa usando matrizes independentes no GitHub Actions.
- Implementação de defesa defensiva contra rate limit e lixo de API (`Tenacity` + `Pydantic`).

**⏳ Fase 3: IoT Ground Truth (Planejada)**
- Expansão do Data Lake via orquestração MQTT.
- Coleta primária via Tensiômetros (Força de água) e Termometria Infravermelha no dossel (Folha).
- Retreinamento do Gradient Boosting usando Ground Truth para precisão milimétrica.

---

## 🚀 Como Executar Localmente

```bash
# 1. Clone o repositório
git clone https://github.com/PhSandoval/OmniCrop.AI.git
cd OmniCrop.AI

# 2. Ative um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis (.env ou .streamlit/secrets.toml)
# Requer: SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY, AZURE_CONNECTION_STRING

# 5. Rode a suíte de testes (Garantia de Qualidade)
pytest tests/

# 6. Inicie o dashboard
streamlit run app/main.py
```
