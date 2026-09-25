# OmniCrop AI - ML Engineering & Data Science Blueprint (v3.0)

Este documento estabelece as diretrizes estratégicas para a transição do OmniCrop AI de um protótipo regressor simples para uma **plataforma preditiva de inteligência agronômica de nível empresarial**. O foco principal é a mitigação de riscos climáticos extremos (ex: El Niño/La Niña) e a garantia de alta confiança por parte do usuário final.

---

## 1. Feature Engineering: Ensinando o Oceano ao Modelo (Gradient Boosting)

O clima extremo quebra as médias históricas. Para prever safras e riscos com precisão, o modelo deve "entender" o estado macroclimático do planeta.

* **Ingestão do Índice ONI (Oceanic Niño Index):** 
  * A variável ENSO (El Niño-Southern Oscillation) deve ser ingerida continuamente da NOAA.
  * O índice numérico (ex: `+1.8` para El Niño forte, `-1.0` para La Niña) entra como uma feature direta no modelo (Gradient Boosting / `HistGradientBoostingRegressor`).
  * *Objetivo:* O algoritmo ajusta dinamicamente os pesos de temperatura e precipitação dependendo da fase do oceano, evitando falsos positivos durante secas ou chuvas anômalas.

* **Deltas de Anomalia Histórica:**
  * Em vez de fornecer variáveis absolutas (ex: `chuva_30_dias = 150mm`), o pipeline de dados (PySpark/Airflow) calculará as anomalias relativas ao histórico de 10-15 anos (ex: `chuva_delta = -45%`).
  * *Objetivo:* Ensinar ao modelo quando um dado absoluto é estatisticamente anormal para o mês vigente.

* **Lag Features e Médias Móveis (Memória Fisiológica):**
  * O impacto hídrico e de radiação na planta é cumulativo.
  * O modelo consumirá *Lags* (atrasos) e *Rolling Averages* (médias móveis) de 60, 90 e 120 dias.
  * *Objetivo:* Traduzir a "memória" biológica do estresse da cultura para a matemática do modelo.

---

## 2. Validação e Avaliação de Alta Precisão (Evitando Data Leakage)

Avaliar modelos em agricultura exige rigor extremo devido à natureza temporal dos ciclos de safra.

* **Walk-Forward Validation (Time-Series CV):**
  * **Proibido:** O uso de `train_test_split` aleatório padrão (gera vazamento de dados do futuro para o passado).
  * **Padrão Exigido:** Validação por janelas deslizantes (Sliding Windows).
    * Treino: 2015-2020 ➔ Teste: 2021
    * Treino: 2015-2021 ➔ Teste: 2022
  * *Objetivo:* Simular exatamente o cenário de produção, onde só se conhece o passado para inferir o futuro.

* **Métricas de Punição Quadrática (RMSE):**
  * A métrica de avaliação principal será o **RMSE (Root Mean Squared Error)** em vez do MAE (Mean Absolute Error).
  * *Objetivo:* Na agricultura, errar 0.1 de NDVI todo dia é tolerável, mas errar 0.5 num momento fenológico crítico destrói a produtividade. O RMSE pune erros grandes severamente, forçando o modelo a ser conservador.

---

## 3. Explainable AI (XAI) e Confiança Agronômica

Produtores e Engenheiros Agrônomos não confiam em "caixas pretas" preditivas.

* **Validação Visual de Explicabilidade (SHAP):**
  * A biblioteca **SHAP (SHapley Additive exPlanations)** será integrada ao pipeline de inferência.
  * O painel frontal (Streamlit) renderizará gráficos (ex: *Waterfall Plots* usando `st.pyplot()`) mostrando a contribuição exata de cada feature para a decisão do modelo.
  * *Exemplo prático de UX:* "O NDVI projetado cairá em 12% na próxima semana. O modelo tomou esta decisão impactado em 60% pelas noites excessivamente quentes (GDA) e 40% pela forte anomalia do índice El Niño (ONI)."

---

## 4. Front-End de Decisão (UX/UI Streamlit)

A melhor arquitetura de dados perde seu valor se o produtor rural não conseguir interpretá-la. Para tangibilizar a engenharia pesada do modelo, o OmniCrop AI deverá implementar 4 componentes visuais chave:

1. **Raio-X da Decisão (SHAP Waterfall):** 
   * Um bloco expansível *"Entenda o Cálculo da IA"* onde o `st.pyplot(fig)` renderiza o impacto de cada variável. 
   * Exemplo: NDVI Base (0.80) - Falta de Chuva (-0.05) - Anomalia de Temperatura (-0.10) = Previsão (0.65).
2. **Badge Dinâmico de Anomalia & Score de Confiança:** 
   * Alerta visual no topo do dashboard ativado automaticamente se a Feature Store apontar um El Niño intenso.
   * Acompanhado pela incerteza estatística (ex: *"Confiança da previsão: 88%"*).
3. **Simulador "What-If" (Análise de Cenários):** 
   * Um ambiente de estresse (`st.slider()`) onde o agricultor aumenta a temperatura ou zera a chuva manualmente e vê o modelo matemático reagir com previsões na mesma hora, sem recarregar a página (via `st.session_state`).
4. **Auditoria da IA (Backtesting Visual):** 
   * Gráfico (Plotly via `st.plotly_chart`) cruzando as duas linhas dos últimos 12 meses: *"Saúde Real (Satélite)"* vs *"Saúde Prevista (Gradient Boosting)"*.
   * Prova definitiva e visual de que o *Walk-Forward Validation* funciona e de que a IA não está sofrendo alucinações.

---

## 5. IoT Ground Truth: Sensores Físicos (Fase 3)

O dataset atual (`Dataset_SugarCane_historico`) é um excelente repositório de dados meteorológicos globais via APIs e satélite. A introdução de sensores físicos IoT instalados diretamente no talhão elevará o OmniCrop AI de uma ferramenta de **estimativa** para um sistema de **Ground Truth (verdade absoluta)**.

### 5.1 Sensores de Solo e Nutrição

* **Tensão da Água no Solo (Tensiômetro):**
  * O dataset atual mede umidade volumétrica (`umidade_solo_9_27cm`). O tensiômetro mede a **força (em kPa)** que a raiz precisa fazer para extrair a água.
  * *Impacto:* Gatilho definitivo e preciso para acionar o pivô no Simulador de Irrigação.

* **Condutividade Elétrica do Solo (CE):**
  * Proxy direto para salinidade e presença de macronutrientes (fertilizantes dissolvidos).
  * *Impacto:* O Agrônomo GenAI poderá auditar se a ureia aplicada foi absorvida ou lixiviada.

* **pH do Solo em Tempo Real:**
  * pH baixo "trava" a absorção de fósforo e potássio na cana-de-açúcar, tornando a adubação inútil.
  * *Impacto:* Alertas automáticos de correção de calagem.

### 5.2 Sensores Fisiológicos da Planta (Canopy)

* **Temperatura do Dossel (Termometria Infravermelha):**
  * Quando a planta entra em stress hídrico, fecha os estômatos e para de transpirar, aquecendo a folha.
  * *Impacto:* Detecção de stress hídrico **dias antes** do NDVI cair nas imagens de satélite. Transforma o alerta de "reativo" para "preventivo".

* **Crescimento do Colmo (Dendrômetro):**
  * Sensor abraçado ao caule que mede a expansão milimétrica diária.
  * *Impacto:* Cruzamento exato de mm de crescimento por mm de chuva ou irrigação.

### 5.3 Sensores de Microclima e Fitossanidade

* **Pluviometria Física (Pluviômetro IoT):**
  * A `precipitacao_mm` de APIs erra gravemente em chuvas convectivas de verão (chove muito numa fazenda e nada na vizinha).
  * *Impacto:* Calibração do erro da API diretamente no talhão.

* **Molhamento Foliar (Leaf Wetness):**
  * Sensor que simula a superfície de uma folha para detetar presença e duração do orvalho.
  * *Impacto:* Variável matemática mais importante para prever a eclosão de doenças fúngicas graves (Ferrugem Marrom, Carvão). Habilita o módulo futuro de **Fitossanidade Preditiva**.

### 5.4 Integração com a Arquitetura Existente

A ingestão de dados IoT será orquestrada pelo **Apache Airflow** (Fase 2), recebendo *streaming* via protocolo **MQTT** e armazenando os dados brutos no **AWS S3**. O PySpark cruzará esses dados com as leituras diárias da Open-Meteo e as imagens quinzenais do Copernicus, criando um **feedback loop** que valida e melhora continuamente o modelo Gradient Boosting da Fase 1.
