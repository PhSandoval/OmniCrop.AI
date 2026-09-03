# Arquitetura do Sistema (Architecture)

O OmniCrop AI adota o padrão de **Monólito Ágil**, sendo todo desenvolvido em Python. Essa escolha reduz drasticamente a latência e complexidade de DevOps, mantendo a escalabilidade necessária para um SaaS B2B.

## 1. Frontend & Backend (Streamlit)
* **Tecnologia:** Streamlit
* **Papel:** Atua simultaneamente como Backend (roteamento, lógica de negócio) e Frontend (renderização SSR). 
* **Vantagem:** Permite a construção de painéis de dados complexos, renderização de mapas interativos (Folium) e gráficos pesados (Plotly) sem necessidade de manter uma API REST separada.

## 2. Banco de Dados & Autenticação (Supabase)
* **Tecnologia:** Supabase (PostgreSQL) + Auth GoTrue
* **Papel:** Gerencia o Multi-Tenancy. Cada usuário faz login e recebe um token JWT.
* **Segurança:** O banco de dados utiliza **Row Level Security (RLS)**. As queries SQL são protegidas no nível do banco; um usuário não consegue ler a tabela de Fazendas de outro usuário, mesmo que a aplicação tente.

## 3. Ingestão de Dados (Open-Meteo API)
* **Tecnologia:** Requests + Pandas
* **Papel:** Captura clima e geolocalização.
* **Processo:** Quando o usuário cadastra uma fazenda, a Lat/Lon é salva. A aplicação consulta a API *Open-Meteo* em tempo real para baixar os últimos 90 dias de dados horários (Temperatura, Chuva, Radiação, Umidade do Solo) e também os próximos 15 dias de Previsão.
* **Feature Engineering:** Os dados horários são agregados em janelas diárias e mensais (ex: Graus-Dia Acumulados) na camada de negócio.

## 4. Inteligência Artificial (XGBoost)
* **Tecnologia:** Scikit-Learn + XGBoost Regressor
* **Papel:** O Cérebro do Satélite Virtual.
* **Pipeline:** O modelo foi treinado offline com milhares de dados históricos de safras passadas para prever o índice de vigor (NDVI) com base no clima. O modelo final (`.pkl`) é embarcado na aplicação. Durante o uso, os dados meteorológicos (passados e previstos) passam pelo modelo em milissegundos para gerar a curva de vigor da planta.

## 5. Integração Contínua (GitHub Actions)
* **Tecnologia:** GitHub Actions (CI) + Pytest
* **Papel:** Garantia de Qualidade.
* **Processo:** Todo commit na branch `main` dispara pipelines modulares que testam separadamente: 
  1) A ingestão de dados da API.
  2) O motor de regras agronômicas (DSS).
  3) A consistência matemática do modelo de IA (XGBoost).
