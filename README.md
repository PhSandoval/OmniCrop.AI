# 🌱 OmniCrop AI

OmniCrop AI é um **Sistema de Suporte à Decisão (DSS)** voltado para a gestão inteligente de culturas agrícolas. Inicialmente focado em Cana-de-Açúcar, o sistema funciona como um agrônomo virtual, ajudando no monitoramento de lavouras e fornecendo recomendações preditivas para operações de campo.

A aplicação consolida dados climáticos em tempo real, modelos de Machine Learning (XGBoost) para estimativa de vigor vegetativo, e Inteligência Artificial Generativa (Google Gemini) para gerar pareceres executivos instantâneos.

---

## 🌍 Resiliência Climática & Feature Engineering (El Niño)

O OmniCrop AI foi construído para operar sob anomalias climáticas severas. Diferente de modelos tradicionais que dependem de médias históricas (que falham durante quebras de clima), nossa arquitetura de Machine Learning incorpora o **Índice ENSO (Oceanic Niño Index - ONI)** como uma *feature* direta no algoritmo (XGBoost). O cálculo de deltas de anomalias e o rigoroso controle de *Walk-Forward Validation* e RMSE garantem que o produtor receba projeções de quebra de safra validadas mesmo durante os extremos do El Niño e La Niña.

---

## 🛠 Stack Tecnológica

### 🚀 Fase 1: Em Produção (Frontend, ML e GenAI)

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Linguagem** | Python | Espinha dorsal de toda a aplicação e modelagem |
| **Frontend** | Streamlit | Interface web com gestão avançada via `session_state` |
| **UI/UX** | Glassmorphism + Dark Mode | Design customizado com efeito de vidro fosco |
| **Backend (BaaS)** | Supabase | Autenticação, API e gestão de dados |
| **Banco de Dados** | PostgreSQL + PostGIS | Relacional com extensão espacial para coordenadas |
| **Segurança** | Row Level Security (RLS) | Isolamento de dados por utilizador |
| **Motor Preditivo** | XGBoost | Cálculo do Vigor Vegetativo (NDVI) |
| **Explainability (XAI)** | SHAP | Justificação matemática de cada previsão |
| **Manipulação de Dados** | Pandas | Tratamento e transformação em memória |
| **Visualização** | Plotly | Gráficos interativos (RMSE, ENSO, Anomalias) |
| **IA Generativa** | Google Gemini 3.6 | Assistente virtual e geração de relatórios PDF |
| **Arquitetura GenAI** | RAG (Retrieval-Augmented Generation) | Injeção de contexto real nos prompts |
| **Dados Meteorológicos** | Open-Meteo | Histórico e previsão climática |
| **Dados Oceânicos** | NOAA (ONI) | Índice ENSO em tempo real |
| **Sensoriamento Remoto** | Copernicus / Rasterio | Imagens de satélite multiespectrais |

### 🏗️ Fase 2: Próximos Passos (Engenharia de Dados & Infraestrutura)

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Containers** | Docker | Isolamento do ambiente local (`docker-compose.yml`) |
| **Orquestração** | Apache Airflow | Agendamento e controle das extrações diárias (ETL/ELT) |
| **Data Lake** | AWS S3 | Armazenamento bruto dos ficheiros JSON e TIFF |
| **Processamento** | PySpark | Processamento distribuído de dados climáticos históricos |
| **Formato Analítico** | Delta Lake | Armazenamento colunar otimizado para o histórico das safras |
| **Feature Store** | Redis + Feast | Servir variáveis de stress hídrico em baixa latência |

### 🌾 Fase 3: Visão Futura (IoT Ground Truth)

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Solo** | Tensiômetro IoT | Tensão da água no solo (kPa) — gatilho definitivo de irrigação |
| **Solo** | Sensor de CE (Condutividade Elétrica) | Proxy para salinidade e absorção de fertilizantes |
| **Solo** | Sensor de pH | Monitoramento da acidez em tempo real |
| **Planta** | Termometria Infravermelha (Dossel) | Detecção de stress hídrico dias antes da queda do NDVI |
| **Planta** | Dendrômetro | Expansão milimétrica diária do colmo |
| **Microclima** | Pluviômetro IoT | Calibração local da precipitação (corrigindo erro da API) |
| **Fitossanidade** | Sensor de Molhamento Foliar | Predição de eclosão de doenças fúngicas (Ferrugem, Carvão) |
| **Protocolo** | MQTT + Airflow Streaming | Ingestão de dados IoT em tempo real |

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [Guia do Desenvolvedor (Design.md)](docs/Design.md) | Arquitetura, estrutura de pastas e detalhes do modelo de ML |
| [Guia do Usuário (User_Guide.md)](docs/User_Guide.md) | Casos de Uso (UCs) da plataforma |
| [ML Engineering Blueprint](docs/ML_Engineering_Blueprint.md) | Estratégia de Feature Engineering, Validação e XAI |
| [Plano de Engenharia](docs/engineering/README.md) | Roadmap de execução das Fases 1, 2 e 3 |

---

## 🚀 Como Executar o Projeto Localmente

```bash
# 1. Clone o repositório
git clone https://github.com/PhSandoval/OmniCrop.AI.git
cd OmniCrop.AI

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente (Crie o arquivo .streamlit/secrets.toml)
# Adicione: SUPABASE_URL, SUPABASE_KEY, e GEMINI_API_KEY

# 5. Inicie o dashboard
streamlit run frontend/app.py
```

### Levantar a Plataforma de Dados (Fase 2)

```bash
cd omnicrop-data-platform
docker compose up -d
# Acesse o Airflow em: http://localhost:8080 (user: airflow / pass: airflow)
```
