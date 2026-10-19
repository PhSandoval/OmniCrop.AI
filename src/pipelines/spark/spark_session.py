"""
Fábrica de Sessões Spark (SparkSession Builder) Otimizada para Big Data Agronômico.
Configurada com Adaptive Query Execution (AQE), serializador Kryo e compressão Snappy.
"""
from __future__ import annotations
import os
from typing import Any


def get_spark_session(
    app_name: str = "OmniCrop-BigData-Lakehouse",
    master: str | None = None,
    extra_configs: dict[str, str] | None = None,
    enable_delta: bool = False,
) -> Any:
    """
    Cria ou recupera uma SparkSession industrial configurada para alta performance.

    Configurações Críticas de Engenharia:
    - spark.sql.adaptive.enabled: Ativa Adaptive Query Execution (AQE) para otimizar planos de execução em runtime.
    - spark.sql.adaptive.coalescePartitions.enabled: Mescla partições pequenas para evitar o problema de 'small files'.
    - spark.sql.adaptive.skewJoin.enabled: Divide partições desbalanceadas para evitar gargalos em joins de talhões.
    - spark.serializer: Usa KryoSerializer para serialização binária ultra-rápida entre workers.
    - spark.sql.parquet.compression.codec: Snappy para equilíbrio ideal entre velocidade de descompressão e tamanho em disco.
    """
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise ImportError(
            "PySpark não está instalado neste ambiente. "
            "Para executar pipelines de Big Data distribuídos, instale com: pip install -r src/pipelines/spark/requirements-spark.txt"
        ) from exc

    builder = SparkSession.builder.appName(app_name)

    # Master: se não fornecido, usa variável de ambiente ou default local[*]
    spark_master = master or os.getenv("SPARK_MASTER", "local[*]")
    # Se já estiver rodando em cluster gerenciado (ex: Databricks/Dataproc), o master já é injetado pelo cluster manager
    if "DATABRICKS_RUNTIME_VERSION" not in os.environ:
        builder = builder.master(spark_master)

    # Configurações de performance para Data Lakehouse
    configs = {
        # Adaptive Query Execution (AQE)
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled": "true",
        "spark.sql.adaptive.localShuffleReader.enabled": "true",
        # Serialização e Memória
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        "spark.sql.execution.arrow.pyspark.enabled": "true",
        # Otimização de Arquivos Parquet
        "spark.sql.parquet.compression.codec": "snappy",
        "spark.sql.parquet.filterPushdown": "true",
        # Fuso Horário de Negócio
        "spark.sql.session.timeZone": "America/Sao_Paulo",
    }

    if enable_delta:
        configs.update({
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        })

    if extra_configs:
        configs.update(extra_configs)

    for k, v in configs.items():
        builder = builder.config(k, v)

    return builder.getOrCreate()
