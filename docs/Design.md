# 🏗️ OmniCrop AI — Guia do Desenvolvedor & Design Architecture

Este documento descreve as decisões de arquitetura e a separação de responsabilidades da aplicação **OmniCrop AI**.

## 1. Arquitetura do Sistema

A aplicação foi desenhada em 3 camadas principais (Arquitetura Monolítica Streamlit com organização limpa). Embora não tenhamos "endpoints de backend customizados" servindo um frontend SPA tradicional (como FastAPI + React), nós separamos logicamente as responsabilidades:

```text
OmniCrop/
├── frontend/             # Interface do Usuário (Streamlit UI)
│   ├── app.py            # Ponto de entrada (Roteador principal)
│   ├── pages/            # Telas adicionais
│   ├── components/       # UI Widgets (Gráficos, Autenticação UI, Botões)
│   └── assets/           # Imagens, backgrounds e logos
│
├── backend/              # Lógica de Negócio e Serviços Externos
│   ├── api_client.py     # Inferência de IA e motor DSS (Decisão Agronômica)
│   ├── db.py             # Ponte Zero-Trust com Supabase + JWT Security
│   ├── live_data.py      # Integração com APIs externas (Open-Meteo, Nominatim)
│   └── farm_config.py    # Tratamento de dados e sincronização de cache de sessão
│
├── data_science/         # Modelos Treinados
│   └── models/
│       └── ndvi_xgb_model.pkl  # Binário XGBoost para predição
│
└── docs/                 # Documentação
```

### Por que não usamos Endpoints (FastAPI, Flask)?
Atualmente, a plataforma OmniCrop AI é desenvolvida inteiramente no **Streamlit**. Isso permite iteração ultrarrápida (Fullstack Python). O frontend (UI) chama as funções do backend (arquivos do diretório `backend/`) localmente, na mesma thread. O único "Endpoint" consumido é o da nossa BaaS (Backend as a Service) — o **Supabase** — e APIs meteorológicas externas.

## 2. Diagrama de Fluxo e Roteamento

O `frontend/app.py` orquestra a lógica de estado global (`session_state`):

```text
Requisição chegou
        │
        ├─ Usuário não logado?       → /frontend/components/auth.py (Tela de Login)
        │
        ├─ show_onboarding=True?     → Inicia onboarding (Mapa Nominatim)
        │
        ├─ active_farm = None?       → /frontend/components/header.py (Selector de Fazendas)
        │
        └─ Autenticado & Talhão OK?  → Renderiza o Dashboard Principal
```

## 3. Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|---|---|---|
| **Frontend / Roteamento** | Streamlit | Iteração rápida para protótipos de Data Apps e IA. |
| **Gráficos** | Plotly + Folium | Componentes altamente interativos (mapas e dashboards de clima). |
| **Modelagem Preditiva** | XGBoost | Alta performance em dados tabulares com relação não linear. |
| **Inteligência Generativa** | Google Gemini (3.6) | Geração de parecer executivo interpretando dados climáticos em tempo real. |
| **Banco de Dados** | Supabase (PostgreSQL) | Fornece DB relacional potente e Row-Level-Security (RLS) out-of-the-box. |
| **Autenticação** | Supabase GoTrue | Tokens JWT seguros validados diretamente no DB. |
| **Geolocalização** | Nominatim (OSM) | Busca de endereços e CEPs grátis e open-source. |

## 4. Segurança — Defesa em Profundidade

O sistema garante proteção aos dados agronômicos através de múltiplas etapas:
1. **Ponte Zero-Trust:** O `backend/db.py` sempre utiliza o token JWT da sessão atual do usuário, não uma chave global.
2. **PostgreSQL RLS:** As políticas de Row-Level Security no Supabase bloqueiam (no nível do banco) qualquer leitura ou escrita onde a coluna `user_id` não seja exatamente igual ao ID do token JWT atual. 
3. **Cofre:** `secrets.toml` retém chaves criptográficas que nunca vão para o `.git`.
