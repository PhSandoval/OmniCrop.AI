"""
Motor Híbrido de Execução da Camada Ouro (Gold Engine Orchestrator).
Implementa o padrão Polyglot Data Engine:
- Modo 'pandas': Execução ultraleve, custo zero, mono-nó para Streamlit, pilotos e talhões individuais.
- Modo 'pyspark': Execução distribuída de alta volumetria para usinas, cooperativas e frotas de milhares de talhões.
- Modo 'auto': Despacho dinâmico baseado no volume de dados ou número de talhões.
"""
from __future__ import annotations
import os
from typing import Any, Literal
import pandas as pd


def is_pyspark_available() -> bool:
    """Verifica se o runtime do PySpark está instalado e acessível no ambiente."""
    try:
        import pyspark
        return True
    except ImportError:
        return False


def run_gold_pipeline_hybrid(
    input_data: pd.DataFrame | str,
    output_path: str | None = None,
    engine: Literal["auto", "pandas", "pyspark"] = "auto",
    **spark_kwargs,
) -> pd.DataFrame | None:
    """
    Executa a transformação da Camada Ouro com despacho inteligente de motor (Engine Dispatcher).

    Parâmetros:
    - input_data: DataFrame Pandas ou URI de armazenamento (string, ex: 'abfss://...', 's3a://...', 'data/silver').
    - output_path: Caminho de saída opcional.
    - engine: 'pandas', 'pyspark' ou 'auto'.
    - spark_kwargs: Parâmetros adicionais repassados ao job PySpark.
    """
    # 1. Resolução do modo de execução no 'auto'
    selected_engine = engine
    if selected_engine == "auto":
        if isinstance(input_data, str) and (input_data.startswith("abfss://") or input_data.startswith("s3a://") or input_data.startswith("gs://")):
            selected_engine = "pyspark" if is_pyspark_available() else "pandas"
        elif isinstance(input_data, pd.DataFrame) and len(input_data) > 500_000:
            selected_engine = "pyspark" if is_pyspark_available() else "pandas"
        else:
            selected_engine = "pandas"

    # 2. Execução via PySpark (Enterprise Big Data Scale)
    if selected_engine == "pyspark":
        if not is_pyspark_available():
            raise ImportError(
                "Motor 'pyspark' selecionado, mas PySpark não está instalado. "
                "Execute: pip install -r src/pipelines/spark/requirements-spark.txt"
            )
        from src.pipelines.spark.gold_batch_job import run_gold_batch_job

        if not isinstance(input_data, str) or not output_path:
            raise ValueError("O motor 'pyspark' requer 'input_data' (URI) e 'output_path' válidos.")

        run_gold_batch_job(
            input_path=input_data,
            output_path=output_path,
            **spark_kwargs
        )
        return None

    # 3. Execução via Pandas / PyArrow (Zero-Cost / Edge Mode)
    elif selected_engine == "pandas":
        from src.data.ingest_azure import transform_to_gold

        if isinstance(input_data, str):
            # Lê arquivo Parquet via PyArrow
            df_in = pd.read_parquet(input_data)
        elif isinstance(input_data, pd.DataFrame):
            df_in = input_data
        else:
            raise TypeError("Entrada inválida para motor Pandas.")

        df_gold = transform_to_gold(df_in)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df_gold.to_parquet(output_path, index=False, engine="pyarrow")

        return df_gold

    else:
        raise ValueError(f"Motor de processamento desconhecido: '{selected_engine}'. Use 'pandas', 'pyspark' ou 'auto'.")
