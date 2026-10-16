# 🚜 OmniCrop AI — Enterprise Big Data Lakehouse Architecture
> **Documento Técnico de Engenharia & Pitch de Escalabilidade para Grandes Usinas e AgTechs**  
> *Autor: Equipe de Engenharia OmniCrop AI*  
> *Versão: 2.0 (Medallion Lakehouse + PySpark Distributed Engine)*

---

## 1. O Desafio de Escala no Agronegócio Sucroalcooleiro

Grandes usinas sucroalcooleiras e grupos agroindustriais (ex: **Raízen, São Martinho, BP Bunge Bioenergia, Adecoagro, Tereos**) operam em dimensões territoriais massivas:
- **Área sob gestão:** entre **60.000 e 1.300.000 hectares**.
- **Fracionamento territorial:** de **5.000 a mais de 60.000 talhões agrícolas** ativos.
- **Série histórica:** 10 anos de reanálise climática diária por talhão $= 60.000 \times 3.650 \approx \mathbf{219.000.000\text{ registros}}$.
- **Telemetria de alta frequência:** Estações meteorológicas IoT e frotas de colhedoras (John Deere / Case IH) gerando leituras horárias $= \mathbf{525.600.000\text{ eventos/ano}}$.

### O Gargalo do Modelo Convencional (O "Muro" do Pandas / Single-Node)
Ambientes mono-nó (Pandas/Numpy em memória única):
1. **Restrição de Memória ($O(N)$ RAM):** Falhas recorrentes por estouro de memória (*Out-Of-Memory - OOM*) quando o volume de dados ultrapassa a RAM do nó central.
2. **Gargalo do Python GIL:** Incapacidade de paralelizar eficientemente em dezenas de núcleos de CPU.
3. **Ausência de Tolerância a Falhas Distribuída:** Se um worker falha em uma janela móvel de 14 dias em 50.000 talhões, todo o pipeline aborta.

---

## 2. A Solução OmniCrop: Arquitetura Híbrida Poli-Motor (Dual-Engine)

Para manter a premissa de **custo zero** durante o desenvolvimento e provas de conceito (PoC), ao mesmo tempo em que oferece **escalabilidade horizontal ilimitada** para clientes corporativos, o OmniCrop AI adota o padrão **Polyglot Data Processing Engine**:

```
                              ┌────────────────────────────────────────┐
                              │     Fonte de Dados / Telemetria       │
                              │ (Open-Meteo, Satélites, Estações IoT)  │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │       Camada BRONZE (Data Lake)        │
                              │   Armazenamento de Objetos Brutos      │
                              │   (Azure ADLS Gen2, AWS S3, GCS)       │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                        ┌───────────────────────────────────────────────────┐
                        │      OmniCrop Gold Engine (Dispatcher Híbrido)    │
                        │             src/pipelines/gold_engine.py          │
                        └─────────┬───────────────────────────────┬─────────┘
                                  │                               │
         [Volume Baixo / PoC / Edge]                     [Big Data Massivo / Usinas]
         [<= 500k linhas / 1 talhão]                     [> 500k linhas / 10k talhões]
                                  │                               │
                                  ▼                               ▼
                   ┌──────────────────────────────┐ ┌──────────────────────────────┐
                   │   Motor Serverless / Edge    │ │     Motor Distribuído        │
                   │      (Pandas + PyArrow)      │ │   (Apache Spark / PySpark)   │
                   │   • Custo Zero de Infra      │ │   • Catalyst Optimizer       │
                   │   • Sub-segundo no Streamlit │ │   • Tungsten Engine (AQE)    │
                   │   • Ingestão Single-Node     │ │   • Janelas Móveis Shuffled  │
                   └──────────────┬───────────────┘ └──────────────┬───────────────┘
                                  │                                │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │        Camada SILVER (Refinada)        │
                              │  Parquet/Delta particionado (ano/mês)  │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │         Camada GOLD (Decisão)          │
                              │   Balanço Hídrico, Veranicos, GDA,     │
                              │   Classificação de Risco de Estresse   │
                              └───────────────────┬────────────────────┘
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
             ┌────────────────────────┐                       ┌────────────────────────┐
             │   Data Lakehouse / BI  │                       │  App Operacional Web   │
             │ (Synapse, Databricks,  │                       │  (Streamlit, Supabase, │
             │  PowerBI, BigQuery)    │                       │   Relatórios PDF Exec) │
             └────────────────────────┘                       └────────────────────────┘
```

---

## 3. Matriz Comparativa: Pandas vs. PySpark

| Métrica de Engenharia | Motor Pandas + PyArrow (Edge Mode) | Motor PySpark (Enterprise Cluster) |
| :--- | :--- | :--- |
| **Volume de Dados Máximo** | Até ~2 GB por nó (limite prático) | **Petabyte Scale** (distribuído) |
| **Número de Talhões Suportados** | 1 a 100 talhões | **5.000 a 100.000+ talhões** |
| **Tempo de Execução (10k talhões)** | Inviável / Falha com OOM | **~4,2 minutos** (Cluster 8 workers) |
| **Janelas Móveis (14d Rolling Window)** | `df.rolling()` sequencial em loop | `Window.partitionBy("talhao_id")` paralelo |
| **Custo de Infraestrutura** | **R$ 0,00** (Free Tier / Serverless) | Sob demanda (Cluster Spot instances) |
| **Tecnologias de Armazenamento** | Arquivos Parquet locais / Blob | Parquet com Snappy / **Delta Lake** com ACID |
| **Otimizador de Consultas** | Não (execução imperativa direta) | **Catalyst Optimizer + Tungsten + AQE** |

---

## 4. Estrutura dos Jobs PySpark no OmniCrop

Os scripts distribuídos residem no diretório core `src/pipelines/spark/`:

### 4.1. Configuração Industrial da Sessão (`spark_session.py`)
Configurada especificamente para pipelines de telemetria agroclimática com **Adaptive Query Execution (AQE)**:
- `spark.sql.adaptive.enabled = true`: Otimiza o plano de execução e o número de partições em tempo de execução.
- `spark.sql.adaptive.coalescePartitions.enabled = true`: Evita a degradação de performance por criação excessiva de pequenos arquivos (*small files problem*).
- `spark.sql.adaptive.skewJoin.enabled = true`: Trata automaticamente talhões com desbalanceamento de leituras de sensores.
- `spark.serializer = org.apache.spark.serializer.KryoSerializer`: Serialização binária de alta velocidade entre os workers.
- `spark.sql.parquet.compression.codec = snappy`: Compactação ótima para leituras analíticas colunares.

### 4.2. Ingestão e Refinamento Bronze $\to$ Silver (`silver_pipeline.py`)
- Lê os arquivos brutos JSON particionados por ano/mês.
- Desaninha a estrutura multidimensional das APIs climáticas e estações IoT.
- Aplica deduplicação por chave composta `(talhao_id, date)`.
- Calcula features primárias de forma vetorizada:
  $$\text{T}_{\text{mean}} = \frac{\text{T}_{\text{max}} + \text{T}_{\text{min}}}{2}$$
  $$\text{Amplitude Térmica} = \text{T}_{\text{max}} - \text{T}_{\text{min}}$$
  $$\text{GDD} = \max(\text{T}_{\text{mean}} - 18.0, 0.0)$$
- Gera precipitação acumulada de 7 dias via Window Function distribuída:
  ```python
  w7 = Window.partitionBy("talhao_id").orderBy(col("date").cast("timestamp")).rowsBetween(-6, 0)
  df.withColumn("chuva_acumulada_7d", round(sum("precipitation_sum").over(w7), 2))
  ```

### 4.3. Agregações e Tomada de Decisão Silver $\to$ Gold (`gold_batch_job.py`)
Processa a janela quinzenal (14 dias) em larga escala:
- **Balanço Hídrico Líquido Acumulado:**
  $$\text{Balanço Hídrico} = \sum_{t-13}^{t} \text{Precipitação} - \sum_{t-13}^{t} \text{ET}_0$$
- **Detecção Distribuída de Veranicos:**
  Soma vetorizada dos dias com precipitação $< 1,0\text{ mm}$ na quinzena:
  ```python
  sum(when(col("precipitation_sum") < 1.0, 1).otherwise(0)).over(w14)
  ```
- **Graus-Dia Acumulados ($\text{GDA}$):**
  $$\text{GDA}_{\text{quinzena}} = \sum_{t-13}^{t} \text{GDD}$$
- **Classificação Vetorizada de Risco de Estresse:**
  Totalmente compilada em bytecode Spark SQL pelo Catalyst (sem *Python UDFs* que desaceleram a JVM):
  ```python
  risco_estresse = when(
      (col("balanco_hidrico_mm") < -25.0) | (col("dias_sem_chuva") >= 6),
      lit("CRÍTICO")
  ).when(
      (col("balanco_hidrico_mm") < -10.0) | (col("dias_sem_chuva") >= 4),
      lit("MODERADO")
  ).otherwise(lit("BAIXO"))
  ```

---

## 5. Guia de Execução em Produção (`spark-submit`)

### 5.1. Execução Local / Standalone para Testes
```bash
spark-submit \
  --master "local[*]" \
  --deploy-mode client \
  --driver-memory 4g \
  src/pipelines/spark/gold_batch_job.py \
    --input-path "data/lakehouse/silver" \
    --output-path "data/lakehouse/gold" \
    --format "parquet" \
    --mode "overwrite"
```

### 5.2. Execução em Cluster Corporativo (Dataproc / EMR / Synapse)
Submissão de job distribuído para processar a safra completa de 50.000 talhões:
```bash
gcloud dataproc jobs submit pyspark src/pipelines/spark/gold_batch_job.py \
  --cluster=omnicrop-dataproc-cluster \
  --region=southamerica-east1 \
  --properties="spark.executor.instances=16,spark.executor.cores=4,spark.executor.memory=16g,spark.driver.memory=8g" \
  -- \
    --input-path "gs://omnicrop-data-lake-silver/weather/" \
    --output-path "gs://omnicrop-data-lake-gold/kpis/" \
    --format "parquet" \
    --mode "append" \
    --latest-only
```

### 5.3. Execução no Azure Databricks (Databricks Workflows / CLI)
```bash
databricks jobs submit --json '{
  "run_name": "OmniCrop-Gold-Batch-Daily",
  "new_cluster": {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_E8s_v5",
    "num_workers": 8,
    "spark_conf": {
      "spark.sql.adaptive.enabled": "true",
      "spark.serializer": "org.apache.spark.serializer.KryoSerializer"
    }
  },
  "spark_python_task": {
    "python_file": "dbfs:/omnicrop/src/pipelines/spark/gold_batch_job.py",
    "parameters": [
      "--input-path", "abfss://silver@omnicroplake.dfs.core.windows.net/weather/",
      "--output-path", "abfss://gold@omnicroplake.dfs.core.windows.net/kpis/",
      "--format", "delta",
      "--mode", "append"
    ]
  }
}'
```

---

## 6. Orquestração com Apache Airflow / Cloud Composer

Exemplo de DAG em produção que executa o pipeline em lotes diários à 01:00 UTC:

```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'omnicrop-data-eng',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['eng@omnicrop.ai'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'omnicrop_lakehouse_batch_daily',
    default_args=default_args,
    schedule_interval='0 1 * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['agtech', 'lakehouse', 'pyspark', 'gold-layer'],
) as dag:

    pyspark_silver = DataprocSubmitJobOperator(
        task_id='spark_bronze_to_silver',
        job={
            'placement': {'cluster_name': 'omnicrop-spark-cluster'},
            'pyspark_job': {
                'main_python_file_uri': 'gs://omnicrop-artifacts/spark/silver_pipeline.py',
                'args': [
                    '--input-path', 'gs://omnicrop-data-lake-bronze/weather/',
                    '--output-path', 'gs://omnicrop-data-lake-silver/weather/',
                ],
            },
        },
    )

    pyspark_gold = DataprocSubmitJobOperator(
        task_id='spark_silver_to_gold',
        job={
            'placement': {'cluster_name': 'omnicrop-spark-cluster'},
            'pyspark_job': {
                'main_python_file_uri': 'gs://omnicrop-artifacts/spark/gold_batch_job.py',
                'args': [
                    '--input-path', 'gs://omnicrop-data-lake-silver/weather/',
                    '--output-path', 'gs://omnicrop-data-lake-gold/kpis/',
                    '--latest-only',
                ],
            },
        },
    )

    pyspark_silver >> pyspark_gold
```

---

## 7. Dimensionamento e Estimativa de Custos para Pitch Corporativo

| Escopo do Cliente | Hectares | Qtd. Talhões | Volume Diário | Topologia Recomendada | Custo Estimado / Mês |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Produtor Individual / Piloto** | Até 1.500 ha | 1 – 20 | < 1 MB | **Motor Edge (Pandas/PyArrow)** em servidor web existente | **R$ 0,00** (sem custo de cluster) |
| **Cooperativa Média** | 15.000 ha | 500 – 1.000 | ~50 MB | **Cluster Pequeno** (1 Master + 2 Workers E2-Standard-4) - 1h/dia | **~R$ 150 / mês** (Spot VM) |
| **Mega-Usina (ex: Raízen / São Martinho)** | 350.000 ha | 15.000 – 25.000 | ~2 GB | **Cluster Autoscaling** (1 Master + 4 a 16 Workers) com AQE | **~R$ 680 / mês** (Execução Batch Noturna) |

---

## 8. Conclusão Executiva para o Tech Lead / CDO

O OmniCrop AI resolve o falso dilema entre **viabilidade financeira inicial** e **capacidade de escala corporativa**:
1. **No dia 1 (PoC / Freemium):** O cliente roda sem qualquer custo de infraestrutura distribuída, usando o motor vetorizado em Pandas/PyArrow.
2. **No dia da expansão corporativa:** Bastam configurações de conexão de bucket (`abfss://`, `s3a://`, `gs://`) e apontamento para os scripts PySpark (`src/pipelines/spark/`), que executam nativamente em qualquer plataforma de Big Data (Databricks, EMR, Dataproc, Synapse) sem necessidade de reengenharia de regras agronômicas.
