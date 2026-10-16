"""
Job Distribuído de Alta Performance em PySpark: Camada SILVER -> Camada GOLD (Lakehouse).
Processamento em lote (Batch) de KPIs executivos agronômicos para usinas de grande porte (50.000 a 1.500.000 hectares).
Calcula balanço hídrico acumulado, veranicos, GDA e classificação de estresse hídrico via Window Functions vetorizadas.
"""
from __future__ import annotations
import argparse
import sys
from datetime import datetime, timezone


def compute_gold_kpis_spark(df_silver):
    """
    Núcleo de transformação distribuída da Camada Gold em PySpark.
    Executado 100% pelo Tungsten Execution Engine sem gargalos de Python GIL ou UDFs.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window

    # Garante presença de talhao_id
    if "talhao_id" not in df_silver.columns:
        df_silver = df_silver.withColumn("talhao_id", F.lit("default_plot"))

    # Compatibilidade de nomes de colunas
    precip_col = "precipitation_sum" if "precipitation_sum" in df_silver.columns else "precipitacao_total"
    et0_col = "et0_fao_evapotranspiration" if "et0_fao_evapotranspiration" in df_silver.columns else "evapotranspiracao_total"
    tmax_col = "temperature_2m_max" if "temperature_2m_max" in df_silver.columns else "t_max"
    tmin_col = "temperature_2m_min" if "temperature_2m_min" in df_silver.columns else "t_min"

    # Garante presença de amplitude e gdd
    if "thermal_amplitude" not in df_silver.columns:
        df_silver = df_silver.withColumn("thermal_amplitude", F.col(tmax_col) - F.col(tmin_col))

    if "gdd" not in df_silver.columns:
        t_mean = (F.col(tmax_col) + F.col(tmin_col)) / 2.0
        df_silver = df_silver.withColumn("gdd", F.when(t_mean > 18.0, t_mean - 18.0).otherwise(0.0))

    # Janela Deslizante de 14 dias (Quinzena Agronômica) particionada por talhão
    w14 = (
        Window
        .partitionBy("talhao_id")
        .orderBy(F.col("date").cast("timestamp"))
        .rowsBetween(-13, 0)
    )

    # 1. Agregações Vetorizadas da Quinzena
    df_windowed = (
        df_silver
        .withColumn("chuva_total_mm", F.round(F.sum(precip_col).over(w14), 2))
        .withColumn("et0_total_mm", F.round(F.sum(et0_col).over(w14), 2))
        .withColumn(
            "balanco_hidrico_mm",
            F.round(F.col("chuva_total_mm") - F.col("et0_total_mm"), 2)
        )
        .withColumn(
            "dias_sem_chuva",
            F.sum(F.when(F.col(precip_col) < 1.0, 1).otherwise(0)).over(w14)
        )
        .withColumn("gda_total_acumulado", F.round(F.sum("gdd").over(w14), 2))
        .withColumn("temp_max_media_c", F.round(F.avg(tmax_col).over(w14), 2))
        .withColumn("temp_min_media_c", F.round(F.avg(tmin_col).over(w14), 2))
        .withColumn("amplitude_termica_media_c", F.round(F.avg("thermal_amplitude").over(w14), 2))
    )

    # 2. Classificação Agronômica Vetorizada de Risco de Estresse Hídrico
    df_gold = (
        df_windowed
        .withColumn(
            "risco_estresse_hidrico",
            F.when(
                (F.col("balanco_hidrico_mm") < -25.0) | (F.col("dias_sem_chuva") >= 6),
                F.lit("CRÍTICO")
            ).when(
                (F.col("balanco_hidrico_mm") < -10.0) | (F.col("dias_sem_chuva") >= 4),
                F.lit("MODERADO")
            ).otherwise(F.lit("BAIXO"))
        )
        .withColumn(
            "recomendacao_manejo",
            F.when(
                F.col("risco_estresse_hidrico") == F.lit("CRÍTICO"),
                F.lit("Alerta de Estresse Hídrico: avaliar irrigação suplementar imediata.")
            ).when(
                F.col("risco_estresse_hidrico") == F.lit("MODERADO"),
                F.lit("Atenção Operacional: monitorar umidade do solo e previsão climática.")
            ).otherwise(
                F.lit("Condições Hídricas Favoráveis para o desenvolvimento vegetativo.")
            )
        )
        .withColumn("ano", F.year(F.col("date")))
        .withColumn("mes", F.month(F.col("date")))
        .withColumn("processed_at", F.lit(datetime.now(timezone.utc).isoformat()))
    )

    return df_gold


def run_gold_batch_job(
    input_path: str,
    output_path: str,
    output_format: str = "parquet",
    write_mode: str = "append",
    latest_only: bool = False,
    master: str | None = None,
    jdbc_url: str | None = None,
    jdbc_table: str = "kpis_gold_batch",
    jdbc_properties: dict | None = None,
) -> None:
    """
    Executa o Job PySpark completo da Camada Gold.

    Suporta saída dupla:
    1. Lakehouse Object Storage (Parquet / Delta particionado por ano/mes).
    2. Banco Relacional / Supabase / Postgres via JDBC (opcional).
    """
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    from src.pipelines.spark.spark_session import get_spark_session

    print("🌾 Iniciando Job PySpark: Camada GOLD - KPIs Agronômicos em Big Data...")
    spark = get_spark_session(
        app_name="OmniCrop-Gold-Batch-Processing",
        master=master,
        enable_delta=(output_format == "delta"),
    )

    # 1. Leitura da Camada Silver
    print(f"📥 Lendo Camada SILVER de: {input_path}")
    df_silver = spark.read.format(output_format if output_format == "delta" else "parquet").load(input_path)

    # 2. Computação Distribuída dos KPIs da Camada Ouro
    df_gold = compute_gold_kpis_spark(df_silver)

    # 3. Filtragem para Snapshot Mais Recente por Talhão (se solicitado)
    if latest_only:
        print("🔍 Filtrando apenas o snapshot mais recente por talhão...")
        w_latest = Window.partitionBy("talhao_id").orderBy(F.col("date").desc())
        df_gold = (
            df_gold
            .withColumn("rk", F.row_number().over(w_latest))
            .filter(F.col("rk") == 1)
            .drop("rk")
        )

    # 4. Gravação no Data Lakehouse (Parquet ou Delta)
    print(f"🏆 Gravando Camada GOLD em: {output_path} (Formato: {output_format}, Modo: {write_mode})")
    writer = df_gold.write.mode(write_mode)
    if not latest_only:
        writer = writer.partitionBy("ano", "mes")

    writer.format(output_format).save(output_path)
    print("✅ Sucesso: Camada GOLD gravada no Data Lakehouse com particionamento otimizado.")

    # 5. Carga JDBC Opcional (PostgreSQL / Supabase / Enterprise Data Warehouse)
    if jdbc_url and jdbc_properties:
        print(f"🗄️ Inserindo registros em lote no Banco de Dados ({jdbc_table})...")
        (
            df_gold
            .write
            .mode(write_mode)
            .jdbc(url=jdbc_url, table=jdbc_table, properties=jdbc_properties)
        )
        print("✅ Sucesso: Inserção JDBC concluída.")


def main():
    parser = argparse.ArgumentParser(description="OmniCrop Big Data - Job Batch da Camada Ouro (PySpark)")
    parser.add_argument("--input-path", required=True, help="URI de entrada da Silver (ex: abfss://silver@... ou s3a://...)")
    parser.add_argument("--output-path", required=True, help="URI de destino da Gold")
    parser.add_argument("--format", default="parquet", choices=["parquet", "delta"], help="Formato de gravação (parquet ou delta)")
    parser.add_argument("--mode", default="append", choices=["append", "overwrite"], help="Modo de gravação")
    parser.add_argument("--latest-only", action="store_true", help="Gera apenas o snapshot mais recente de cada talhão")
    parser.add_argument("--master", default=None, help="Endereço do Spark Master (opcional)")
    parser.add_argument("--jdbc-url", default=None, help="String de conexão JDBC (opcional)")
    parser.add_argument("--jdbc-table", default="kpis_gold_batch", help="Tabela de destino JDBC")

    args = parser.parse_args()
    run_gold_batch_job(
        input_path=args.input_path,
        output_path=args.output_path,
        output_format=args.format,
        write_mode=args.mode,
        latest_only=args.latest_only,
        master=args.master,
        jdbc_url=args.jdbc_url,
        jdbc_table=args.jdbc_table,
    )


if __name__ == "__main__":
    main()
