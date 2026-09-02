# SugarCane Copilot - O Satélite Virtual do Agronegócio (SaaS B2B)

Um **Sistema de Suporte à Decisão (DSS)** de ponta a ponta focado na previsão do vigor vegetativo (NDVI) da cana-de-açúcar. Desenvolvido para atuar como um **Satélite Virtual**, o sistema permite o monitoramento contínuo de múltiplos talhões utilizando dados climáticos em tempo real, contornando a limitação física dos satélites ópticos (que ficam cegos em dias nublados).

Criado com uma **Arquitetura Monolítica no Streamlit** e integrado nativamente com o **Supabase (PostgreSQL + Auth)**, é um produto desenhado para ser comercializado no modelo SaaS B2B.

---

## O Desafio no Agronegócio (Por que criamos isso?)

Satélites ópticos (como o Sentinel-2) são maravilhosos para ler o vigor da planta (NDVI). O problema? **Eles têm uma janela de revisita de até 16 dias e não conseguem ver através das nuvens.** 
Curiosamente, a época em que a cana-de-açúcar mais cresce é exatamente no verão tropical, quando chove todo dia e o céu está sempre nublado. O produtor ficava "cego" durante os meses mais cruciais da safra.

**A Solução:** Um modelo de Machine Learning que "prevê" qual é o NDVI atual com base no que a planta sentiu nos últimos 90 dias (temperatura, radiação e chuva acumulada), garantindo 100% de visibilidade, 365 dias por ano.

---

## Principais Funcionalidades

* **SaaS Multi-Tenant:** Sistema de autenticação JWT via Supabase com Row Level Security (RLS). Cada usuário acessa apenas a sua própria carteira de fazendas com total isolamento e segurança de dados.
* **Mapeamento Interativo (Folium/Leaflet):** Onboarding moderno com mapas de satélite (Esri), Geocoding (OpenStreetMap) e captura automática do GPS para fixar a fazenda no mapa.
* **Ingestão de Dados ao Vivo:** O backend bate na API Open-Meteo em tempo real, agrupando dados meteorológicos da localização exata nos últimos 90 dias e nos próximos 15 dias de previsão.
* **Dashboard Analytics Profissional:** Uma suíte de gráficos robustos feitos com Plotly (Histogramas, Áreas, Eixos Duplos e Séries Temporais) que cruzam o clima real com a projeção do modelo de IA.
* **DSS (Matriz de Decisão Agronômica):** O sistema entende a biologia (Crescimento vs Maturação) e gera Checklists de ação automáticos (ex: Liberar colheita, aplicar maturador químico, alertar brigada de incêndio).
* **Simulador de Intervenções (What-If):** O agrônomo projeta cenários hipotéticos ("E se eu irrigar 40mm hoje?"). O sistema calcula o **Custo de Energia (ROI)** e projeta a melhora na curva de vigor.

---

## Arquitetura do Modelo de IA (XGBoost)

O motor do sistema utiliza um modelo de **Gradient Boosting (XGBoost)**. Por que essa arquitetura e não Redes Neurais?

1. **Relacionamentos Não-Lineares:** Chuva demais afoga a raiz (waterlogging), chuva de menos trava o crescimento. O XGBoost mapeia perfeitamente essas "quebras" de limite biológico.
2. **Performance em Séries Temporais Tabulares:** Extremamente veloz para inferência no servidor SaaS, superando Deep Learning em tarefas tabulares com features agregadas (ex: *Graus-Dia Acumulados*).
3. **Explicabilidade (Caixa Branca):** Produtores não confiam em "magia". O algoritmo nos permite expor o *Feature Importance* (ex: Chuva de 30 dias pesa 45% na decisão), dando tranquilidade técnica ao agrônomo.

---

## Arquitetura do Projeto

```text
Sugarcane_NDVI_Predictor/
├── data/                    # Bases de dados brutas e tratadas
├── models/                  # O Cérebro da aplicação
│   └── ndvi_xgb_model.pkl   # Modelo treinado exportado
├── src/                     # A Fábrica (Pipelines locais de ETL e Treino ML)
├── pages/                   # Telas do SaaS (Simulador, Análise, Config, Conta)
├── components/              # Componentes modulares
│   ├── auth.py              # Interface de Login/Registro
│   ├── db.py                # Ponte Zero-Trust com o Supabase (JWT headers)
│   ├── live_data.py         # API client (Open-Meteo & Geocoding)
│   └── charts.py            # Suite de gráficos Plotly
├── .streamlit/         
│   └── secrets.toml         # Cofre local de chaves de API
├── .github/workflows/       # Integração Contínua (CI)
│   └── ci_pipeline.yml      # Jobs modulares (Dados, DSS, IA)
├── app.py                   # O Produto Final (Ponto de entrada do SaaS)
└── requirements.txt         # Dependências essenciais para deploy
```

## Como rodar localmente

Clone o repositório e rode os seguintes comandos no terminal:

```bash
# 1. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows use: .venv\Scriptsctivate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente (Supabase)
mkdir -p .streamlit
echo "SUPABASE_URL = 'sua-url-aqui'" > .streamlit/secrets.toml
echo "SUPABASE_KEY = 'sua-anon-key-aqui'" >> .streamlit/secrets.toml

# 4. Inicie o Dashboard
streamlit run app.py
```
