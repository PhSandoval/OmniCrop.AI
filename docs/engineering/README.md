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
│   │   Grad. Boosting │──────────▶│   Airflow        │                   │
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
| 4 | **Modelo ignorava anomalias do El Niño** — Previsões falhavam durante eventos ENSO extremos | O modelo recebia apenas variáveis meteorológicas brutas sem contexto macroclimático | Arquitetura de Feature Engineering com ONI, Deltas de Anomalia e Lag Features (60, 90, 120 dias) |
| 5 | **Recrutadores não entendiam o valor técnico** — O projeto parecia "só um dashboard bonito" | Faltava visualização explícita das métricas de validação do modelo | Adição dos painéis de Índice ENSO, RMSE vs MAE e Feature Importance (SHAP) na aba de Análise |

---

## 🏗️ Fase 2: Engenharia de Dados Cloud & MLOps (EM PRODUÇÃO)

### Objetivo
Migrar a ingestão de dados para um pipeline **Serverless, orquestrado e resiliente** usando a nuvem da Azure e automações do GitHub Actions, eliminando a dependência do computador local e infraestruturas pesadas (como Airflow/Docker). Adicionar testes rigorosos para garantir a integridade da inteligência artificial.

### O que já está entregue (Fase 2 - Serverless Data Engineering)

| Módulo | Status | Descrição |
|--------|--------|-----------|
| Data Lake Bronze | ✅ Completo | Criado contêiner na Azure Blob Storage (`omnicrop-data-lake-bronze`). |
| Orquestração | ✅ Completo | Script `ingest_weather_azure.yml` no GitHub Actions orquestra extrações via cron (cronograma diário) e manualmente. |
| Pipeline Ingestão | ✅ Completo | Script `src/data/ingest_azure.py` coleta, particiona e envia dados para a Nuvem de forma segura. |

### Pirâmide de Testes MLOps (Implementada)

Para garantir que o modelo e o Data Lake nunca corrompam por dados sujos ou APIs fora do ar, implementamos uma Pirâmide de Testes (`pytest tests/`) em 4 frentes:
1. **Contratos (Fábrica):** Pydantic (`contracts.py`) filtra JSONs mal formados antes de baterem na nuvem (Azure).
2. **Resiliência (Memória):** Biblioteca `Tenacity` força retentativas com *Exponential Backoff*. O `unittest.mock` simula quedas 500 do servidor.
3. **Cérebro (Unitários):** Pandas cria dataframes sintéticos de *seca extrema* e *enchente*, testando matematicamente o XGBoost para assegurar bounds lógicos (NDVI entre 0 e 1).
4. **Palco (Nativos UI):** `AppTest` executa sessões virtuais no Streamlit para bloquear os famosos bugs de UI.

### Próximos Passos (Evolução da Nuvem)

- [ ] **Integração Prata/Ouro (Databricks/Spark):** Limpeza e normalização dos JSONs da Azure Blob para tabelas Delta Lake.
- [ ] **Feature Store Integrada:** Servir as variáveis matemáticas (GDA, Chuva_Acumulada) via Redis na nuvem.

### Problemas Antecipados (Fase 2)

| Risco | Mitigação |
|-------|-----------|
| API Open-Meteo com rate limit ou falha (HTTP 500) | Retentativas implementadas com o módulo `tenacity` (`@retry`). |
| Injeção de dados negativos (e.g. precipitação) | Pydantic v2 levanta o erro antes da gravação no Data Lake. |

---

## 🌾 Fase 3: IoT Ground Truth (PLANEJADA)

### Objetivo
Introduzir sensores físicos no talhão para validar e calibrar o modelo Gradient Boosting com dados reais de campo (*Ground Truth*), elevando o OmniCrop AI de ferramenta de estimativa para sistema de precisão absoluta.

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
- [ ] Retreinar o Gradient Boosting com as novas features de Ground Truth
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
