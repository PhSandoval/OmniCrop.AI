# 🏗️ OmniCrop AI — Guia do Desenvolvedor & Design Architecture

Este documento descreve as decisões de arquitetura, separação de responsabilidades e fluxos de dados (MLOps) da aplicação **OmniCrop AI**.

## 1. Arquitetura do Sistema (Clean Architecture)

A aplicação foi migrada de um monolito tradicional em Streamlit para uma **Clean Architecture**. O objetivo principal foi isolar totalmente a Interface do Usuário (UI) das complexas lógicas de negócio, cálculos matemáticos, integrações com o Data Lake e chamadas para Machine Learning.

```text
OmniCrop/
│
├── .github/workflows/    # ☁️ Orquestração Serverless
│   ├── ci_pipeline.yml          # Integração Contínua (Pytest executado a cada push)
│   └── ingest_weather_azure.yml # Ingestão Diária programada (cron) na Azure
│
├── app/                  # 🎨 A Vitrine (Frontend UI isolado)
│   ├── main.py           # Ponto de entrada (Roteador principal - antigo app.py)
│   ├── pages/            # Módulos de telas do Streamlit (Simulador, Análise, etc.)
│   ├── components/       # UI Widgets (Gráficos, Autenticação, Botões)
│   └── assets/           # Imagens, backgrounds e logos
│
├── src/                  # ⚙️ O Motor (Backend, Dados e Lógica de Negócio)
│   ├── data/             # Camada de Acesso a Dados 
│   │   ├── db.py           # Conexão Zero-Trust (Supabase + RLS)
│   │   ├── ingest_azure.py # Ingestão Serverless (Gravação Azure Blob Storage)
│   │   ├── fetch_api.py    # Integrações externas em tempo real (Open-Meteo)
│   │   └── contracts.py    # Contratos de Dados (Quality Assurance via Pydantic)
│   ├── features/         # Preparação de Dados
│   │   └── build_features.py # Feature Engineering e cálculos numéricos
│   ├── models/           # Inteligência Artificial
│   │   ├── train_model.py  # Script de treinamento do Scikit-Learn
│   │   ├── predict.py      # Lógica de Inferência do motor DSS e IA Generativa (Gemini)
│   │   └── ndvi_xgb.pkl    # Binário do Modelo Preditivo Treinado
│   └── utils/            # Ferramentas Transversais
│       ├── farm_config.py  # Manipulação de estado e limites da fazenda
│       └── daily_alerts.py # Lógica de alertas diários
│
├── tests/                # 🛡️ Pirâmide de Testes MLOps
│   ├── test_data.py      # Testes de Contrato Pydantic e Mocks (Tenacity/requests)
│   ├── test_features.py  # Validação unitária das engenharias de variáveis
│   ├── test_model.py     # Limites e fronteiras do modelo (SHAP e xgboost bounds)
│   ├── test_dss.py       # Regras do sistema de suporte a decisão
│   └── test_ui.py        # Streamlit AppTest para navegação nativa e bugs de estado
│
└── docs/                 # Documentação do Repositório
```

### Por que separamos `app/` de `src/`?
Quando o OmniCrop era focado puramente em Streamlit, qualquer re-execução da interface rodava novamente chamadas de modelos, transformações massivas e chamadas de API. Ao isolar o `src/`, garantimos que os dados (APIs e DB) e a matemática dos DataFrames e do Machine Learning rodem de forma modular. O Streamlit (em `app/`) agora age apenas como um renderizador (View). 

## 2. Diagrama de Fluxo e Roteamento

O `app/main.py` orquestra a lógica de estado global (`session_state`):

```text
Requisição chegou
        │
        ├─ Usuário não logado?       → /app/components/auth.py (Tela de Login)
        │
        ├─ show_onboarding=True?     → Inicia onboarding (Mapa Nominatim)
        │
        ├─ active_farm = None?       → /app/components/header.py (Selector de Fazendas)
        │
        └─ Autenticado & Talhão OK?  → Renderiza o Dashboard Principal
```

## 3. Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|---|---|---|
| **Frontend Web** | Streamlit | Iteração rápida para Data Apps. |
| **Modelagem Preditiva** | Gradient Boosting (scikit-learn) | Equivalente nativo ao XGBoost, mas roda nativamente no Mac/Linux sem a dependência pesada de `libomp`. |
| **Generative AI** | Google Gemini (Pro) | Geração de pareceres técnicos cruzando anomalias climáticas. |
| **Banco de Dados (Live)** | Supabase (PostgreSQL) | Fornece DB relacional potente e Autenticação GoTrue com tokens JWT. |
| **Data Lake** | Azure Blob Storage | Abordagem Serverless de Big Data, armazenando JSONs particionados de clima. |
| **Pipeline MLOps** | GitHub Actions + Pydantic | Ingestão agendada na Nuvem validando a qualidade de dados através de contratos estritos (`contracts.py`). |
| **Pirâmide de Testes** | Pytest, Tenacity, AppTest | Testes de unidade e E2E, mockando conexões falhas e interface gráfica simulada. |

## 4. Segurança — Defesa em Profundidade

O sistema garante proteção aos dados agronômicos através de múltiplas etapas:
1. **Ponte Zero-Trust:** O `src/data/db.py` sempre utiliza o token JWT da sessão atual do usuário, não uma chave global.
2. **PostgreSQL RLS (Row-Level Security):** As políticas bloqueiam no banco qualquer leitura onde a coluna `user_id` não seja exatamente igual ao ID do JWT.
3. **Contratos e Tolerância a Falhas:** Antes da nuvem gravar os dados no Data Lake, o **Pydantic** valida a estrutura (e.g., Chuva > 0). O **Tenacity** gerencia bloqueios de APIs externas, tentando as requisições 3 vezes com *Exponential Backoff*.
