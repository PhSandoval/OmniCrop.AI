# 🗺️ OmniCrop AI — Roadmap de Engenharia

Este documento detalha o plano de execução prático para cada fase do OmniCrop AI, incluindo o que já foi entregue, os problemas que enfrentámos e como os resolvemos, e os próximos passos concretos.

---

## Visão Geral das Fases

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   FASE 1 (Em Produção)          FASE 2 (Em Construção)                 │
│   ┌─────────────────┐           ┌─────────────────┐                    │
│   │   Streamlit      │           │   Docker         │                   │
│   │   XGBoost        │──────────▶│   Airflow        │                   │
│   │   Gemini RAG     │           │   AWS S3         │                   │
│   │   Supabase       │           │   PySpark        │                   │
│   └─────────────────┘           └────────┬────────┘                    │
│                                          │                              │
│                                          ▼                              │
│                                 FASE 3 (Planejada)                      │
│                                 ┌─────────────────┐                    │
│                                 │   IoT Sensors    │                    │
│                                 │   MQTT Streaming │                    │
│                                 │   Ground Truth   │                    │
│                                 └─────────────────┘                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✅ Fase 1: Frontend, ML e GenAI (EM PRODUÇÃO)

### O que já está entregue

| Módulo | Status | Descrição |
|--------|--------|-----------|
| Landing Page | ✅ Completo | Design Glassmorphism, banner de El Niño, seção "Como Funciona" |
| Autenticação | ✅ Completo | Login/Registro via Supabase Auth com RLS |
| Painel Geral | ✅ Completo | Dashboard com KPIs, mapa interativo (PostGIS), clima em tempo real |
| Simulador | ✅ Completo | Módulo de irrigação com sliders interativos via `session_state` |
| Análise (Analytics) | ✅ Completo | 6 gráficos: Filme da Safra, Anomalia de Chuva, Real vs Previsto, Feature Importance, Índice ENSO (ONI), RMSE vs MAE |
| Minha Fazenda | ✅ Completo | CRUD de fazendas, configuração de coordenadas, mapa por talhão |
| Configurações | ✅ Completo | Toggle de alertas (desligado por padrão), preferências do usuário |
| Assistente GenAI | ✅ Completo | Agrônomo virtual com RAG (contexto climático injetado no Gemini 3.6) |
| Relatório PDF | ✅ Completo | Geração de parecer executivo via Gemini com download instantâneo |

### Problemas Enfrentados e Soluções (Fase 1)

| # | Problema | Causa Raiz | Solução Aplicada |
|---|----------|-----------|------------------|
| 1 | **Bug do "Ghost Routing"** — Logout e criação de fazenda redirecionavam sempre para a fazenda "Boa Vista" | `farm_config.py` sobrescrevia o estado com `active_farm = farms[0]`, que era a primeira fazenda em ordem alfabética | Removida a mutação automática; o estado `None` agora é preservado até o usuário escolher explicitamente |
| 2 | **Página em branco ao gerar PDF** — A dashboard inteira desaparecia quando a API do Gemini retornava erro 429 (quota) | `pdf_generator.py` chamava `st.stop()` no bloco de exceção, matando toda a árvore de renderização do Streamlit | Substituído `st.stop()` por `return None`; o `app.py` trata o `None` graciosamente sem chamar `st.rerun()` |
| 3 | **Toggle de alertas vinha ligado** — Usuários novos recebiam alertas sem ter ativado | O valor padrão do `st.toggle()` era `True` | Alterado para `value=cfg.get("receber_alertas", False)` |
| 4 | **Modelo ignorava anomalias do El Niño** — Previsões falhavam durante eventos ENSO extremos | O XGBoost recebia apenas variáveis meteorológicas brutas sem contexto macroclimático | Arquitetura de Feature Engineering com ONI, Deltas de Anomalia e Lag Features (60, 90, 120 dias) |
| 5 | **Recrutadores não entendiam o valor técnico** — O projeto parecia "só um dashboard bonito" | Faltava visualização explícita das métricas de validação do modelo | Adição dos painéis de Índice ENSO, RMSE vs MAE e Feature Importance (SHAP) na aba de Análise |

---

## 🏗️ Fase 2: Engenharia de Dados & Infraestrutura (EM CONSTRUÇÃO)

### Objetivo
Migrar a ingestão de dados de "on-the-fly" (que é lenta e não escala) para um pipeline **orquestrado, agendado e resiliente** usando containers Docker e armazenamento em nuvem.

### Checklist de Execução

#### Etapa 2.1 — Infraestrutura Base (Docker + Airflow)
- [x] Criar a pasta `omnicrop-data-platform/`
- [x] Gerar `docker-compose.yml` com Airflow 2.7.1 + Postgres 13
- [x] Configurar rede interna `airflow-tier`
- [x] Auto-instalação do `apache-airflow-providers-amazon` via `_PIP_ADDITIONAL_REQUIREMENTS`
- [x] Mapear volumes locais (`./dags`, `./logs`, `./plugins`)
- [ ] Validar deploy local com `docker compose up -d`
- [ ] Confirmar acesso ao Airflow UI em `http://localhost:8080`

#### Etapa 2.2 — Conexão com AWS S3 (Data Lake Bronze)
- [ ] Criar bucket S3 na AWS (ex: `omnicrop-data-lake-bronze`)
- [ ] Configurar as credenciais AWS no Airflow (via Admin > Connections)
- [ ] Criar a Connection ID: `aws_s3_conn` (tipo Amazon Web Services)
- [ ] Testar a conectividade com um DAG simples de `S3CreateBucketOperator`

#### Etapa 2.3 — DAGs de Ingestão (ETL)
- [ ] **DAG 1: `ingest_weather_daily`** — Buscar dados diários da Open-Meteo (JSON) → Salvar no S3 particionado por data (`s3://bronze/weather/YYYY-MM-DD/`)
- [ ] **DAG 2: `ingest_oni_monthly`** — Buscar o Índice ONI da NOAA (CSV) → Salvar no S3 (`s3://bronze/enso/`)
- [ ] **DAG 3: `ingest_satellite_biweekly`** — Buscar imagens do Copernicus (TIFF) → Salvar no S3 (`s3://bronze/satellite/`)
- [ ] Configurar schedule: DAG 1 (`@daily`), DAG 2 (`@monthly`), DAG 3 (`0 6 1,15 * *`)

#### Etapa 2.4 — Processamento e Lakehouse (Camada Prata)
- [ ] Configurar ambiente PySpark (local ou EMR Serverless)
- [ ] Script de limpeza e normalização dos JSONs meteorológicos
- [ ] Script de extração de bandas espectrais dos TIFFs (Rasterio)
- [ ] Escrita dos dados tratados em **Delta Lake** no S3 (`s3://silver/weather_cleaned/`)
- [ ] Merge incremental (upsert) para evitar duplicatas

#### Etapa 2.5 — Feature Store e Baixa Latência
- [ ] Deploy do Redis (local via Docker ou ElastiCache)
- [ ] Configuração do Feast (Feature Store)
- [ ] Materialização das features de stress hídrico (GDA, ONI, Lags) para o Redis
- [ ] Endpoint de serving: o Streamlit consulta o Redis em vez de recalcular tudo on-the-fly

### Problemas Antecipados (Fase 2)

| Risco | Mitigação |
|-------|-----------|
| Custos da AWS S3 descontrolados | Usar lifecycle policies: mover dados de Bronze para Glacier após 90 dias |
| Airflow consumir muita RAM local | Manter `LocalExecutor` (não usar CeleryExecutor); limitar paralelismo a 4 |
| API Open-Meteo com rate limit | Implementar retry com backoff exponencial no DAG (`retries=3, retry_delay=timedelta(minutes=5)`) |
| Delta Lake com schema evolution | Ativar `mergeSchema=True` no PySpark para aceitar novas colunas sem quebrar |

---

## 🌾 Fase 3: IoT Ground Truth (PLANEJADA)

### Objetivo
Introduzir sensores físicos no talhão para validar e calibrar o modelo XGBoost com dados reais de campo (*Ground Truth*), elevando o OmniCrop AI de ferramenta de estimativa para sistema de precisão absoluta.

### Sensores Prioritários

| Prioridade | Sensor | Variável | Impacto no Sistema |
|------------|--------|----------|-------------------|
| 🔴 Alta | Tensiômetro | Tensão da Água (kPa) | Gatilho definitivo para o Simulador de Irrigação |
| 🔴 Alta | Termometria IR (Dossel) | Temperatura Foliar (°C) | Detecta stress hídrico dias antes do satélite |
| 🟡 Média | Pluviômetro IoT | Precipitação Local (mm) | Calibra o erro da API Open-Meteo |
| 🟡 Média | Molhamento Foliar | Duração de Orvalho (h) | Previsão de doenças fúngicas (novo módulo) |
| 🟢 Futura | Dendrômetro | Expansão do Colmo (mm) | Correlação crescimento ↔ irrigação |
| 🟢 Futura | Sensor de CE | Condutividade Elétrica (mS/cm) | Auditoria da absorção de fertilizantes |
| 🟢 Futura | Sensor de pH | Acidez do Solo | Alertas automáticos de calagem |

### Checklist de Execução (Fase 3)

- [ ] Definir protocolo de comunicação (MQTT ou LoRaWAN)
- [ ] Configurar broker MQTT (Mosquitto via Docker)
- [ ] Criar DAG no Airflow para consumir tópicos MQTT e persistir no S3
- [ ] Schema unificado no Delta Lake cruzando dados IoT + API + Satélite
- [ ] Retreinar o XGBoost com as novas features de Ground Truth
- [ ] Implementar o módulo de Fitossanidade Preditiva (Molhamento Foliar)

---

## 📊 Métricas de Sucesso por Fase

| Fase | Métrica | Meta |
|------|---------|------|
| 1 | RMSE do NDVI (7 dias) | < 0.05 |
| 1 | Tempo de resposta do dashboard | < 3 segundos |
| 2 | Latência de serving (Redis) | < 100ms |
| 2 | Uptime do pipeline Airflow | > 99% |
| 3 | Redução do RMSE com Ground Truth | -30% vs Fase 1 |
| 3 | Acurácia de alerta de irrigação (Tensiômetro) | > 95% |

---

*Última atualização: Setembro/2026*
