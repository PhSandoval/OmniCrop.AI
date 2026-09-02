# 🌾 SugarCane Copilot - NDVI Predictor & DSS (SaaS B2B)

Um **Sistema de Suporte à Decisão (DSS) Multi-Tenant** de ponta a ponta (End-to-End) focado na previsão do vigor vegetativo (NDVI) da cana-de-açúcar. Desenvolvido para atuar como um **Satélite Virtual**, o sistema permite o monitoramento contínuo de múltiplos talhões utilizando dados climáticos, mesmo em dias nublados onde satélites ópticos falhariam.

Criado inteiramente com uma **Arquitetura Monolítica no Streamlit**, integrado com **Supabase (PostgreSQL + Auth)**, ideal para deploy em nuvem (SaaS B2B) com foco no setor AgTech.

---

## 🌟 Principais Funcionalidades

* **🔐 Arquitetura SaaS Multi-Tenant:** Sistema de autenticação JWT via Supabase com Row Level Security (RLS). O usuário gerencia sua própria carteira de fazendas com total isolamento e segurança de dados.
* **🗺️ Mapeamento Interativo (Folium/Leaflet):** Cadastro Onboarding moderno com mapas de satélite (Esri), ferramenta de Smart Search (Geocoding - OpenStreetMap) e captura automática do GPS do usuário para fixar os limites da fazenda.
* **📡 Ingestão de Dados em Tempo Real:** Conectado à API Open-Meteo, o sistema processa automaticamente dados meteorológicos da localização exata (Latitude/Longitude) cadastrada no banco de dados.
* **🧠 Inteligência Artificial (XGBoost/Gradient Boosting):** Modelo de Machine Learning treinado com histórico climático e imagens de satélite. Preve o NDVI com altíssima precisão utilizando *Graus-Dia Acumulados (GDA)* e chuvas agrupadas em janelas temporais.
* **🎯 Matriz de Decisão Agronômica Dinâmica:** O sistema cruza a previsão de vigor da IA com regras biológicas, gerando *Checklists* de ação contextuais (ex: "Liberar frente de corte mecanizado com 0mm de chuva" vs "Acionar irrigação de salvamento").
* **🔬 Simulador Interativo com Inteligência Financeira:** Uma ferramenta de "What-If Analysis" onde o agrônomo testa cenários hipotéticos de clima (ex: El Niño). O simulador projeta o impacto no desenvolvimento da lavoura e calcula instantaneamente o **Custo Financeiro de Energia (ROI)** e dispara alertas agronômicos críticos (ex: *Asfixia Radicular por Alagamento*).

## 🏗 Arquitetura do Projeto

O sistema é dividido conceitualmente em **Ambiente Local (A Fábrica)** e **Ambiente Cloud (O SaaS)**:

```text
Sugarcane_NDVI_Predictor/
├── data/                       # 🗄️ Dados
├── models/                     # 🧠 O Cérebro da aplicação
│   └── ndvi_xgb_model.pkl      # Modelo treinado exportado (scikit-learn).
├── src/                        # ⚙️ A Fábrica (Pipelines locais de ETL e Treino ML)
├── pages/                      # 📑 Telas do SaaS (Simulador, Análise, Configurações, Minha Conta)
├── components/                 # 🧩 Componentes modulares
│   ├── auth.py                 # Interface de Login/Registro.
│   ├── db.py                   # Ponte Zero-Trust com o Supabase (Injeção de JWT headers).
│   ├── live_data.py            # API client (Open-Meteo & Geocoding).
│   └── ... 
├── .streamlit/                 
│   └── secrets.toml            # 🔒 Cofre local para as chaves do Supabase.
├── app.py                      # 🚀 O Produto Final (Ponto de entrada do SaaS / Onboarding)
└── requirements.txt            # 📦 Dependências essenciais para deploy na nuvem.
```

## 🚀 Como rodar localmente

Clone o repositório e rode os seguintes comandos no terminal:

```bash
# 1. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows use: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente (Supabase)
mkdir -p .streamlit
echo "SUPABASE_URL = 'sua-url-aqui'" > .streamlit/secrets.toml
echo "SUPABASE_KEY = 'sua-anon-key-aqui'" >> .streamlit/secrets.toml

# 4. Inicie o Dashboard
streamlit run app.py
```

---
*Construído com Python, Scikit-Learn, Pandas, Folium, Supabase e Streamlit.*
