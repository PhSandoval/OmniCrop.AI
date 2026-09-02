# SugarCane Copilot - NDVI Predictor & DSS (SaaS B2B)

**Um Sistema de Suporte à Decisão (DSS) Multi-Tenant** de ponta a ponta (End-to-End) focado na previsão do vigor vegetativo (NDVI) da cana-de-açúcar. Desenvolvido para atuar como um**Satélite Virtual**, o sistema permite o monitoramento contínuo de múltiplos talhões utilizando dados climáticos, mesmo em dias nublados onde satélites ópticos falhariam.

Criado inteiramente com uma**Arquitetura Monolítica no Streamlit**, integrado com**Supabase (PostgreSQL + Auth)**, ideal para deploy em nuvem (SaaS B2B) com foco no setor AgTech.

---

## Principais Funcionalidades

*** Arquitetura SaaS Multi-Tenant:** Sistema de autenticação JWT via Supabase com Row Level Security (RLS). O usuário gerencia sua própria carteira de fazendas com total isolamento e segurança de dados.
*** Mapeamento Interativo (Folium/Leaflet):** Cadastro Onboarding moderno com mapas de satélite (Esri), ferramenta de Smart Search (Geocoding - OpenStreetMap) e captura automática do GPS do usuário para fixar os limites da fazenda.
*** Ingestão de Dados em Tempo Real:** Conectado à API Open-Meteo, o sistema processa automaticamente dados meteorológicos da localização exata (Latitude/Longitude) cadastrada no banco de dados.
*** Inteligência Artificial (XGBoost/Gradient Boosting):** Modelo de Machine Learning treinado com histórico climático e imagens de satélite. Preve o NDVI com altíssima precisão utilizando*Graus-Dia Acumulados (GDA)* e chuvas agrupadas em janelas temporais.
*** Matriz de Decisão Agronômica Dinâmica:** O sistema cruza a previsão de vigor da IA com regras biológicas, gerando*Checklists* de ação contextuais (ex: "Liberar frente de corte mecanizado com 0mm de chuva" vs "Acionar irrigação de salvamento").
*** Simulador Interativo com Inteligência Financeira:** Uma ferramenta de "What-If Analysis" onde o agrônomo testa cenários hipotéticos de clima (ex: El Niño). O simulador projeta o impacto no desenvolvimento da lavoura e calcula instantaneamente o**Custo Financeiro de Energia (ROI)** e dispara alertas agronômicos críticos (ex:*Asfixia Radicular por Alagamento*).


## Por que XGBoost? (Arquitetura do Modelo de IA)

O motor de previsao de vigor (NDVI) da aplicacao e alimentado por um modelo de **Gradient Boosting (XGBoost)**. A escolha deste algoritmo para o ecossistema AgTech se deu por motivos fundamentais:

1. **Captura de Relacionamentos Nao-Lineares:** Na biologia da cana-de-acucar, a relacao entre chuva e desenvolvimento nao e linear. Pouca chuva trava o crescimento, chuva moderada acelera, mas chuva excessiva causa asfixia radicular (waterlogging), diminuindo o vigor. Modelos lineares falham ao tentar prever essas quedas, enquanto as arvores de decisao do XGBoost mapeiam essas "quebras" perfeitamente.
2. **Alta Performance em Dados Tabulares:** Para lidar com engenharia de features baseadas em series temporais (como Graus-Dia Acumulados nos ultimos 30/60/90 dias), o XGBoost historicamente supera redes neurais profundas (Deep Learning) com a vantagem de ser extremamente mais rapido para treinar e mais leve para realizar inferencia em producao (SaaS).
3. **Explicabilidade (Feature Importance):** No agronegocio, algoritmos "caixa-preta" nao geram confianca no produtor. O XGBoost permite a extracao clara da importancia de cada feature, provando para o agronomo de forma matematica que o modelo esta, de fato, considerando a "Chuva dos ultimos 30 dias" como o fator principal para a emissao de novas folhas.

## Arquitetura do Projeto


O sistema é dividido conceitualmente em**Ambiente Local (A Fábrica)** e**Ambiente Cloud (O SaaS)**:

```text
Sugarcane_NDVI_Predictor/
 data/            # Dados
 models/           # O Cérebro da aplicação
  ndvi_xgb_model.pkl   # Modelo treinado exportado (scikit-learn).
 src/            # A Fábrica (Pipelines locais de ETL e Treino ML)
 pages/           # Telas do SaaS (Simulador, Análise, Configurações, Minha Conta)
 components/         # Componentes modulares
  auth.py         # Interface de Login/Registro.
  db.py          # Ponte Zero-Trust com o Supabase (Injeção de JWT headers).
  live_data.py      # API client (Open-Meteo & Geocoding).
  ... 
 .streamlit/         
  secrets.toml      # Cofre local para as chaves do Supabase.
 app.py           # O Produto Final (Ponto de entrada do SaaS / Onboarding)
 requirements.txt      # Dependências essenciais para deploy na nuvem.
```

## Como rodar localmente

Clone o repositório e rode os seguintes comandos no terminal:

```bash
# 1. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate # No Windows use: .venv\Scripts\activate

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
