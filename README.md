# OmniCrop AI - O Satélite Virtual do Agronegócio (SaaS B2B)

🚀 **Aplicação em Produção (Nuvem):** [Acesse o OmniCrop AI (Web App)](https://omnicrop.streamlit.app)

Um **Sistema de Suporte à Decisão (DSS)** de ponta a ponta focado na previsão do vigor vegetativo (NDVI) da cana-de-açúcar. Desenvolvido para atuar como um **Satélite Virtual**, o sistema permite o monitoramento contínuo de múltiplos talhões utilizando dados climáticos em tempo real, contornando a limitação física dos satélites ópticos (que ficam cegos em dias nublados).

Criado com uma **Arquitetura Monolítica no Streamlit** e integrado nativamente com o **Supabase (PostgreSQL + Auth)**, é um produto desenhado para ser comercializado no modelo SaaS B2B.

---

## O Desafio no Agronegócio (Por que criamos isso?)

Satélites ópticos (como o Sentinel-2) são maravilhosos para ler o vigor da planta (NDVI). O problema? **Eles têm uma janela de revisita de até 16 dias e não conseguem ver através das nuvens.** 
Curiosamente, a época em que a cana-de-açúcar mais cresce é exatamente no verão tropical, quando chove todo dia e o céu está sempre nublado. O produtor ficava "cego" durante os meses mais cruciais da safra.

**A Solução:** Um modelo de Machine Learning que "prevê" qual é o NDVI atual com base no que a planta sentiu nos últimos 90 dias (temperatura, radiação e chuva acumulada), garantindo 100% de visibilidade, 365 dias por ano.

---

## Principais Funcionalidades

* **SaaS Multi-Tenant & Multi-Fazenda:** Sistema de autenticação JWT com Supabase e Row Level Security (RLS). O usuário gerencia toda a sua carteira de fazendas isoladas e alterna entre os talhões rapidamente usando um Dropdown global no menu lateral.
* **Mapeamento Interativo (Folium/Leaflet):** Onboarding moderno com mapas de satélite (Esri), Geocoding (OpenStreetMap) e captura automática do GPS para fixar a fazenda no mapa.
* **Ingestão de Dados ao Vivo:** O backend bate na API Open-Meteo em tempo real, agrupando dados meteorológicos da localização exata nos últimos 90 dias e nos próximos 15 dias de previsão.
* **Dashboard Analytics Profissional:** Uma suíte de gráficos robustos feitos com Plotly (Histogramas, Áreas, Eixos Duplos e Séries Temporais) que cruzam o clima real com a projeção do modelo de IA.
* **DSS (Matriz de Decisão Agronômica):** O sistema entende a biologia (Crescimento vs Maturação) e gera Checklists de ação automáticos (ex: Liberar colheita, aplicar maturador químico, alertar brigada de incêndio).
* **Simulador de Intervenções (What-If):** O agrônomo projeta cenários hipotéticos ("E se eu irrigar 40mm hoje?"). O sistema calcula o **Custo de Energia (ROI)** e projeta a melhora na curva de vigor.
* **Relatórios Automatizados (PDF):** Módulo gerador embarcado no Dashboard (via `fpdf2`) que compila a saúde atual da fazenda, KPIs e Alertas em um arquivo executivo pronto para reuniões.
* **Motor de Alertas Ativos (CRON):** Um operador robótico (`scripts/daily_alerts.py`) que varre as fazendas durante a madrugada e dispara e-mails de alerta se houver risco extremo na operação diária (Configurável por usuário).

---

## Arquitetura do Modelo de IA (XGBoost)

O motor do sistema utiliza um modelo de **Gradient Boosting (XGBoost)**. Por que essa arquitetura e não Redes Neurais?

1. **Relacionamentos Não-Lineares:** Chuva demais afoga a raiz (waterlogging), chuva de menos trava o crescimento. O XGBoost mapeia perfeitamente essas "quebras" de limite biológico.
2. **Performance em Séries Temporais Tabulares:** Extremamente veloz para inferência no servidor SaaS, superando Deep Learning em tarefas tabulares com features agregadas (ex: *Graus-Dia Acumulados*).
3. **Explicabilidade (Caixa Branca):** Produtores não confiam em "magia". O algoritmo nos permite expor o *Feature Importance* (ex: Chuva de 30 dias pesa 45% na decisão), dando tranquilidade técnica ao agrônomo.

---


## De onde vêm os Dados?

O ecossistema de dados do OmniCrop AI opera em duas frentes distintas:

1. **Os Dados de Treinamento (Offline / Passado):**
   O modelo de Machine Learning (`.pkl`) foi forjado com mais de **10 anos de histórico climático e leituras de satélite** em centenas de fazendas de cana-de-açúcar. A matemática aprendeu como o acúmulo de energia térmica (Graus-Dia) e a umidade do solo impactam a biologia da planta.

2. **Os Dados em Tempo Real (Cloud / Presente e Futuro):**
   * **Open-Meteo (Clima):** Sem a necessidade de instalar uma estação meteorológica física caríssima na fazenda, a nossa aplicação se conecta ao Open-Meteo (um hub de satélites meteorológicos) para extrair, em tempo real, as condições exatas da Latitude/Longitude do usuário. Nós capturamos a curva dos últimos 90 dias e projetamos os próximos 15 dias de chuva e temperatura.
   * **OpenStreetMap Geocoding:** Mapeia endereços textuais digitados pelo produtor rural e converte em coordenadas geográficas precisas para "ancorar" o talhão no globo.

---

## Camadas de Segurança (B2B SaaS)

No setor agroindustrial, dados de produtividade e localização de lavouras valem milhões e são alvo constante de espionagem. Nossa arquitetura adota a metodologia de Defesa em Profundidade:

1. **Identity & Auth (JWT):** Nenhum acesso é anônimo. O cadastro, autenticação e renovação de sessões são orquestrados pelo Supabase (GoTrue Auth) via tokens JWT de curta duração.
2. **Row Level Security (RLS) no Banco de Dados:** Essa é a "jóia da coroa". As tabelas no banco PostgreSQL (Supabase) possuem políticas matemáticas. Mesmo que um atacante burle a interface do Streamlit ou crie um script malicioso, **o próprio banco de dados bloqueia** qualquer tentativa de ler uma fazenda em que a coluna `user_id` não seja exatamente igual ao ID do token JWT de quem está pedindo. É isolamento multilocatário à prova de falhas.
3. **Ponte Zero-Trust (db.py):** Nossa comunicação interna entre o Streamlit e o banco injeta o Header de Autorização do usuário logado em cada requisição. O backend não roda como "Superadmin" global para buscar dados, ele age estritamente sob as credenciais do usuário requisitante.
4. **Cofres de Chaves:** As credenciais e URLs vitais nunca sobem para o repositório. Em desenvolvimento local, ficam restritas ao `.streamlit/secrets.toml`, e em produção, ficam em variáveis de ambiente criptografadas do host.

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
