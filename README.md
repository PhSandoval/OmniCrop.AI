# 🌱 OmniCrop AI

OmniCrop AI é um **Sistema de Suporte à Decisão (DSS)** voltado para a gestão inteligente de culturas agrícolas. Inicialmente focado em Cana-de-Açúcar, o sistema funciona como um agrônomo virtual, ajudando no monitoramento de lavouras e fornecendo recomendações preditivas para operações de campo.

A aplicação consolida dados climáticos em tempo real, modelos de Machine Learning (Gradient Boosting) para estimativa de vigor vegetativo, Inteligência Artificial Generativa (Google Gemini) para gerar pareceres executivos e Data Engineering Serverless na nuvem (Azure).

---

## 🏗️ Clean Architecture

O repositório foi reestruturado seguindo o padrão de **Clean Architecture** para isolar a interface visual da lógica pesada, garantindo escalabilidade total:

```text
OmniCrop/
│
├── 📂 .github/workflows/        # Orquestração Serverless (Substitui Airflow)
│   ├── ci_pipeline.yml          # Integração Contínua (Pytest)
│   └── ingest_weather_azure.yml # Pipeline de Ingestão Diária
│
├── 📂 app/                      # 🎨 A VITRINE (Interface Visual isolada)
│   ├── 📂 pages/                # Telas do Streamlit
│   ├── 📂 components/           # Componentes modulares (UI, PDFs, Gráficos)
│   └── main.py                  # Ponto de entrada (antigo app.py)
│
├── 📂 src/                      # ⚙️ O MOTOR (Core de Regras de Negócio)
│   ├── 📂 data/                 # Conexões (DB, Ingestão Azure, Pydantic Contracts)
│   ├── 📂 features/             # Feature Engineering (Limpeza e Matemática)
│   ├── 📂 models/               # Inteligência (Treino, Inferência XGBoost)
│   └── 📂 utils/                # Utilitários globais
│
└── 📂 tests/                    # 🛡️ Pirâmide de Testes MLOps (Data, Model, UI)
```

---

## 🛠 Stack Tecnológica Atualizada

### 🚀 A Vitrine (Frontend) e IA
- **Frontend Web**: Streamlit (Executado via `app/main.py`)
- **Autenticação e API**: Supabase com Row Level Security (RLS)
- **Generative AI**: Google Gemini Pro (Assistente Virtual e RAG)

### ⚙️ Engenharia de Dados (A Fábrica)
Em vez de depender do computador local ou infraestruturas monolíticas, migramos para a **Nuvem (Azure)** usando fluxos **Serverless**:
- **Data Lake (Bronze)**: Azure Blob Storage (`omnicrop-data-lake-bronze`)
- **Orquestração de Dados**: GitHub Actions (`ingest_weather_azure.yml`) executado automaticamente via cron.
- **Extração**: Open-Meteo API.

### 🛡️ Pirâmide de Testes e MLOps
Temos **100% de cobertura** nas camadas críticas de falha:
1. **Contrato de Dados (Fábrica):** Validação rígida com `Pydantic` (impede anomalias como chuva negativa no Data Lake).
2. **Integração e Mocks (Memória):** O `Tenacity` assegura retentativas progressivas (Exponential Backoff) e o `unittest.mock` simula quedas e erros 500 das APIs.
3. **Unidade do Modelo (Cérebro):** Testes de estresse com `Pandas` e `pytest` jogando matrizes sintéticas (seca/enchente) extremas contra o XGBoost, garantindo o limite estrito do NDVI (0 a 1).
4. **Interface Nativa (Palco):** `AppTest` (Framework oficial do Streamlit) testa a árvore de estado (`session_state`) virtualmente, impedindo bugs de cliques desordenados.

---

## 📚 Documentação

- [Guia do Desenvolvedor (Design.md)](docs/Design.md) - Detalhes profundos da modelagem matemática.
- [Guia do Usuário (User_Guide.md)](docs/User_Guide.md) - Telas e Fluxos.

---

## 🚀 Como Executar o Projeto Localmente

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
