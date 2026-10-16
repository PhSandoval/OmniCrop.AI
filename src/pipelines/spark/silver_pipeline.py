"""
Pipeline Distribuído PySpark: Camada BRONZE -> Camada SILVER (Lakehouse).
Padronização de tipos, deduplicação, cálculo distribuído de GDD e janelas móveis de precipitação.
"""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timezone


def run_silver_pipeline(
    input_path: str,
    output_path: str,
    output_format: str = "parquet",
    write_mode: str = "append",
    master: str | None = None,
) -> None:
    """
    Executa a transformação distribuída da Bronze para a Silver no PySpark.

    Operações Vetorizadas no Spark Catalyst Optimizer:
    1. Ingestão paralela de arquivos JSON/Parquet brutos (Open-Meteo, IoT ou Telemetria de Satélite).
    2. Deduplicação em nível de chave composta (talhao_id, date).
    3. Engenharia de atributos agronômicos:
       - Temperatura média diária
       - Amplitude térmica diária
       - Graus-Dia Acumulados (GDD base 18°C para cana-de-açúcar)
       - Precipitação acumulada de 7 dias via Window Function distribuída
    4. Gravação otimizada particionada por 'ano' e 'mes'.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    from src.pipelines.spark.spark_session import get_spark_session

    print("🚀 Iniciando Job PySpark: Ingestão e Refinamento para Camada SILVER...")
    spark = get_spark_session(app_name="OmniCrop-Silver-Pipeline", master=master)

    # 1. Leitura da Camada Bronze
    print(f"📥 Lendo dados da Bronze em: {input_path}")
    if input_path.endswith(".json") or "/json" in input_path or "weather" in input_path:
        # Suporta tanto arquivos JSON únicos quanto partições de diretórios
        try:
            df_raw = spark.read.json(input_path)
        except Exception:
            df_raw = spark.read.format("json").load(input_path)
    else:
        df_raw = spark.read.format("parquet").load(input_path)

    # Se a estrutura do JSON da Open-Meteo vier aninhada em 'daily', desaninha (explode ou select)
    if "daily" in df_raw.columns:
        # Estrutura aninhada da API Open-Meteo
        df_daily = df_raw.select(
            F.col("latitude"),
            F.col("longitude"),
            F.col("elevation"),
            F.when(F.col("talhao_id").isNotNull(), F.col("talhao_id")).otherwise(F.lit("default_plot")).alias("talhao_id"),
            F.arrays_zip(
                F.col("daily.time").alias("time"),
                F.col("daily.temperature_2m_max").alias("temperature_2m_max"),
                F.col("daily.temperature_2m_min").alias("temperature_2m_min"),
                F.col("daily.precipitation_sum").alias("precipitation_sum"),
                F.col("daily.et0_fao_evapotranspiration").alias("et0_fao_evapotranspiration"),
            ).alias("zipped")
        ).select(
            F.col("talhao_id"),
            F.col("latitude"),
            F.col("longitude"),
            F.col("elevation"),
            F.explode("zipped").alias("col")
        ).select(
            F.col("talhao_id"),
            F.to_date(F.col("col.time")).alias("date"),
            F.col("col.temperature_2m_max").cast("double").alias("temperature_2m_max"),
            F.col("col.temperature_2m_min").cast("double").alias("temperature_2m_min"),
            F.col("col.precipitation_sum").cast("double").alias("precipitation_sum"),
            F.col("col.et0_fao_evapotranspiration").cast("double").alias("et0_fao_evapotranspiration"),
            F.col("latitude").cast("double").alias("latitude"),
            F.col("longitude").cast("double").alias("longitude"),
        )
    else:
        # Estrutura já tabular
        df_daily = df_raw
        if "talhao_id" not in df_daily.columns:
            df_daily = df_daily.withColumn("talhao_id", F.lit("default_plot"))
        if "date" not in df_daily.columns and "time" in df_daily.columns:
            df_daily = df_daily.withColumn("date", F.to_date(F.col("time")))

    # 2. Limpeza e Deduplicação
    df_clean = df_daily.dropDuplicates(["talhao_id", "date"])

    # 3. Engenharia de Features Agronômicas (100% Vectorized / Catalyst)
    df_features = (
        df_clean
        .withColumn("t_mean", (F.col("temperature_2m_max") + F.col("temperature_2m_min")) / 2.0)
        .withColumn("thermal_amplitude", F.col("temperature_2m_max") - F.col("temperature_2m_min"))
        # GDD base 18°C para cana
        .withColumn("gdd", F.when(F.col("t_mean") > 18.0, F.col("t_mean") - 18.0).otherwise(0.0))
    )

    # Janela deslizante de 7 dias para precipitação acumulada recente
    w7 = Window.partitionBy("talhao_id").orderBy(F.col("date").cast("timestamp")).rowsBetween(-6, 0)
    df_silver = (
        df_features
        .withColumn("chuva_acumulada_7d", F.round(F.sum("precipitation_sum").over(w7), 2))
        .withColumn("ano", F.year(F.col("date")))
        .withColumn("mes", F.month(F.col("date")))
        .withColumn("processed_at", F.lit(datetime.now(timezone.utc).isoformat()))
    )

    # 4. Gravação Particionada no Lakehouse
    print(f"💾 Escrevendo dados refinados na Camada SILVER: {output_path} (Modo: {write_mode})")
    (
        df_silver
        .write
        .mode(write_mode)
        .partitionBy("ano", "mes")
        .format(output_format)
        .save(output_path)
    )
    print("✅ Sucesso: Camada SILVER processada e persistida.")


def main():
    parser = argparse.ArgumentParser(description="OmniCrop Big Data - Pipeline Bronze -> Silver (PySpark)")
    parser.add_argument("--input-path", required=True, help="URI de entrada da Bronze (ex: abfss://bronze@... ou s3a://...)")
    parser.add_argument("--output-path", required=True, help="URI de destino da Silver")
    parser.add_argument("--format", default="parquet", choices=["parquet", "delta"], help="Formato de gravação (parquet ou delta)")
    parser.add_argument("--mode", default="append", choices=["append", "overwrite"], help="Modo de gravação")
    parser.add_argument("--master", default=None, help="Endereço do Spark Master (opcional)")

    args = parser.parse_args()
    run_silver_pipeline(
        input_path=args.input_path,
        output_path=args.output_path,
        output_format=args.format,
        write_mode=args.mode,
        master=args.master,
    )


if __name__ == "__main__":
    main()
