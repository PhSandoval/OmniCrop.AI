# OmniCrop AI - ML Engineering & Data Science Blueprint (v2.0)

Este documento estabelece as diretrizes estratégicas para a transição do OmniCrop AI de um protótipo regressor simples para uma **plataforma preditiva de inteligência agronômica de nível empresarial**. O foco principal é a mitigação de riscos climáticos extremos (ex: El Niño/La Niña) e a garantia de alta confiança por parte do usuário final.

---

## 1. Feature Engineering: Ensinando o Oceano ao Modelo (XGBoost)

O clima extremo quebra as médias históricas. Para prever safras e riscos com precisão, o modelo deve "entender" o estado macroclimático do planeta.

* **Ingestão do Índice ONI (Oceanic Niño Index):** 
  * A variável ENSO (El Niño-Southern Oscillation) deve ser ingerida continuamente da NOAA.
  * O índice numérico (ex: `+1.8` para El Niño forte, `-1.0` para La Niña) entra como uma feature direta no modelo (XGBoost).
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
   * Gráfico (Plotly via `st.plotly_chart`) cruzando as duas linhas dos últimos 12 meses: *"Saúde Real (Satélite)"* vs *"Saúde Prevista (XGBoost)"*.
   * Prova definitiva e visual de que o *Walk-Forward Validation* funciona e de que a IA não está sofrendo alucinações.
