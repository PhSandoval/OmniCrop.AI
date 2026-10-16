import sys
from pathlib import Path
import pytest
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.pipelines.gold_engine import is_pyspark_available, run_gold_pipeline_hybrid


@pytest.fixture
def mock_silver_df():
    dates = [datetime(2026, 10, 1) + timedelta(days=i) for i in range(14)]
    return pd.DataFrame({
        "date": dates,
        "talhao_id": ["talhao_01"] * 14,
        "precipitation_sum": [0.0] * 7 + [10.0, 5.0, 0.0, 0.0, 0.0, 12.0, 0.0],
        "et0_fao_evapotranspiration": [3.5] * 14,
        "temperature_2m_max": [31.0] * 14,
        "temperature_2m_min": [19.0] * 14,
        "gdd": [7.0] * 14,
        "latitude": [-21.17] * 14,
        "longitude": [-47.81] * 14,
    })


def test_is_pyspark_available_returns_bool():
    """Valida que a detecção de runtime do PySpark retorna booleano sem levantar exceção."""
    available = is_pyspark_available()
    assert isinstance(available, bool)


def test_gold_engine_hybrid_pandas_mode(mock_silver_df):
    """Valida execução da Camada Ouro via motor leve Pandas (Edge / PoC Mode)."""
    df_gold = run_gold_pipeline_hybrid(
        input_data=mock_silver_df,
        engine="pandas"
    )

    assert df_gold is not None
    assert isinstance(df_gold, pd.DataFrame)
    assert not df_gold.empty
    row = df_gold.iloc[0]

    assert "balanco_hidrico_mm" in row
    assert "dias_sem_chuva" in row
    assert "gda_total_acumulado" in row
    assert "risco_estresse_hidrico" in row
    assert "recomendacao_manejo" in row

    # Verificação de contratos numéricos
    assert row["balanco_hidrico_mm"] == pytest.approx(27.0 - 49.0, 0.1)  # 27mm chuva - 49mm ET0 = -22mm
    assert row["dias_sem_chuva"] == 11
    assert row["risco_estresse_hidrico"] in ["CRÍTICO", "MODERADO", "BAIXO"]


def test_gold_engine_hybrid_auto_mode(mock_silver_df):
    """Valida se o modo 'auto' escolhe o motor correto com base na volumetria."""
    df_gold = run_gold_pipeline_hybrid(
        input_data=mock_silver_df,
        engine="auto"
    )
    assert df_gold is not None
    assert isinstance(df_gold, pd.DataFrame)


def test_gold_engine_raises_informative_error_if_pyspark_missing(mock_silver_df):
    """Se o PySpark não estiver instalado e o usuário forçar engine='pyspark', deve orientar a instalação."""
    if not is_pyspark_available():
        with pytest.raises(ImportError) as exc_info:
            run_gold_pipeline_hybrid(
                input_data="data/silver",
                output_path="data/gold",
                engine="pyspark"
            )
        assert "requirements-spark.txt" in str(exc_info.value)


def test_spark_jobs_module_importable_or_informative():
    """Valida se a estrutura de pacotes spark está coerente e pronta para submissão."""
    from src.pipelines.spark import spark_session, silver_pipeline, gold_batch_job
    assert hasattr(spark_session, "get_spark_session")
    assert hasattr(silver_pipeline, "run_silver_pipeline")
    assert hasattr(gold_batch_job, "run_gold_batch_job")
    assert hasattr(gold_batch_job, "compute_gold_kpis_spark")
