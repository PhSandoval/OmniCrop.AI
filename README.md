# 🌾 SugarCane Copilot - NDVI Predictor & DSS

Um **Sistema de Suporte à Decisão (DSS)** de ponta a ponta (End-to-End) focado na previsão do vigor vegetativo (NDVI) da cana-de-açúcar. Desenvolvido para atuar como um **Satélite Virtual**, o sistema permite o monitoramento contínuo da lavoura utilizando dados climáticos, mesmo em dias nublados onde satélites ópticos falhariam.

Criado inteiramente com uma **Arquitetura Monolítica no Streamlit**, ideal para deploy em nuvem (SaaS) com foco no setor AgTech.

---

## 🌟 Principais Funcionalidades

* **📡 Ingestão de Dados em Tempo Real:** Conectado à API Open-Meteo, o sistema processa automaticamente dados meteorológicos da localização exata (Latitude/Longitude) fornecida pelo usuário na aba de configurações.
* **🧠 Inteligência Artificial (XGBoost/Gradient Boosting):** Modelo de Machine Learning treinado com uma década de histórico climático e imagens de satélite. Preve o NDVI com altíssima precisão (MAE: 0.02) utilizando *Graus-Dia Acumulados (GDA)* e chuvas agrupadas em janelas temporais (30/60/90 dias).
* **🎯 Matriz de Decisão Agronômica (DSS):** O sistema não entrega apenas números brutos. Ele cruza a previsão de vigor da IA com a biologia da planta (Fase de Crescimento vs. Maturação/Corte) gerando alertas automáticos e planos de ação (ex: "Acionar irrigação de salvamento" ou "Avaliar aplicação de maturador").
* **🔬 Simulador Interativo:** Uma ferramenta de "What-If Analysis" onde o agrônomo pode testar cenários hipotéticos de clima (simular ausência de chuva ou aumento de temperatura) e ver como a IA projeta o impacto no desenvolvimento da lavoura.

## 🏗 Arquitetura do Projeto

O sistema é dividido conceitualmente em **Ambiente Local (A Fábrica)** e **Ambiente Cloud (O Produto)**:

```text
Sugarcane_NDVI_Predictor/
├── data/                       # 🗄️ Dados (Gerenciado via .gitignore)
│   └── processed/              # Métricas históricas leves para a Aba Analytics.
├── models/                     # 🧠 O Cérebro da aplicação
│   └── ndvi_xgb_model.pkl      # Modelo treinado exportado via Joblib.
├── src/                        # ⚙️ A Fábrica (Pipelines locais de ETL e Treino)
│   ├── 01_fetch_data.py        # Ingestão de 10 anos de histórico.
│   ├── 02_clean_data.py        # Tratamento e higienização.
│   ├── 03_features.py          # Feature engineering (GDA, rolling sums de chuva).
│   └── 04_train.py             # Treinamento do Gradient Boosting.
├── pages/                      # 📑 Telas do SaaS (Simulator, Analytics, Settings)
├── components/                 # 🧩 Componentes modulares (UI, Estilos, API)
├── app.py                      # 🚀 O Produto Final (Ponto de entrada do Streamlit)
└── requirements.txt            # 📦 Dependências essenciais para nuvem.
```

## 🚀 Como rodar localmente

Clone o repositório e rode os seguintes comandos no terminal:

```bash
# 1. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows use: .venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o Dashboard
streamlit run app.py
```

---
*Construído com Python, Scikit-Learn, Pandas e Streamlit.*
