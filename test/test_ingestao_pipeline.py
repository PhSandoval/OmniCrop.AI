import importlib.util
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
INGESTAO_DIR = WORKSPACE_ROOT / "src" / "Ingestao"


def load_module(module_path: Path, module_name: str, fake_modules: dict[str, types.ModuleType]):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo: {module_path}")

    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, fake_modules, clear=False):
        spec.loader.exec_module(module)
    return module


class TestIngestaoHistorica(unittest.TestCase):
    def setUp(self):
        fake_openmeteo = types.ModuleType("extract_openmeteo")
        fake_openmeteo.fetch_openmeteo_agro_data = lambda *args, **kwargs: {}

        fake_geemap = types.ModuleType("extract_geemap")
        fake_geemap.extrair_ndvi_historico = lambda *args, **kwargs: []

        self.mod = load_module(
            INGESTAO_DIR / "Ingestão_central.py",
            "ingestao_central_test",
            {
                "extract_openmeteo": fake_openmeteo,
                "extract_geemap": fake_geemap,
            },
        )

    def test_build_dataset_historico_monta_registros_e_ndvi(self):
        meteo_mock = {
            "timezone": "America/Sao_Paulo",
            "elevation": 500.0,
            "hourly": {
                "time": ["2026-08-01T00:00", "2026-08-01T01:00"],
                "temperature_2m": [20.0, 21.0],
                "relative_humidity_2m": [80, 78],
                "precipitation": [0.0, 0.2],
                "et0_fao_evapotranspiration": [0.01, 0.02],
                "soil_temperature_7_to_28cm": [22.5, 22.6],
                "soil_moisture_7_to_28cm": [0.31, 0.30],
                "shortwave_radiation": [0.0, 15.0],
                "wind_speed_10m": [8.0, 9.0],
                "wind_gusts_10m": [12.0, 14.0],
            },
        }
        ndvi_mock = [
            {
                "periodo": "2026-08",
                "data_referencia": "2026-08-01",
                "ndvi_medio": 0.42,
                "quantidade_imagens": 7,
            }
        ]

        with patch.object(self.mod, "fetch_openmeteo_agro_data", return_value=meteo_mock), patch.object(
            self.mod, "extrair_ndvi_historico", return_value=ndvi_mock
        ):
            dataset = self.mod.build_dataset_historico(-21.1, -47.8, "Talhao Teste")

        self.assertEqual(dataset["talhao"], "Talhao Teste")
        self.assertEqual(dataset["janela_meteo"]["total_horarios"], 2)
        self.assertEqual(len(dataset["registros"]), 2)
        self.assertEqual(dataset["ndvi_historico_resumo"]["periodos_com_ndvi"], 1)

        primeiro = dataset["registros"][0]
        self.assertEqual(primeiro["openmeteo"]["evapotranspiracao_mm"], 0.01)
        self.assertEqual(primeiro["openmeteo"]["temperatura_solo_18cm_c"], 22.5)
        self.assertEqual(primeiro["openmeteo"]["umidade_solo_9_27cm"], 0.31)
        self.assertEqual(primeiro["openmeteo"]["vento_rajada_ms"], 12.0)
        self.assertEqual(primeiro["ndvi_historico"]["ndvi_medio"], 0.42)

    def test_salvar_dataset_historico_gera_csv_com_colunas_esperadas(self):
        dataset = {
            "registros": [
                {
                    "talhao": "Talhao Teste",
                    "lat": -21.1,
                    "lon": -47.8,
                    "timestamp": "2026-08-01T00:00",
                    "openmeteo": {
                        "timezone": "America/Sao_Paulo",
                        "elevation": 500.0,
                        "temperatura_2m": 20.0,
                        "umidade_relativa_2m": 80,
                        "precipitacao_mm": 0.0,
                        "evapotranspiracao_mm": 0.01,
                        "temperatura_solo_18cm_c": 22.5,
                        "umidade_solo_9_27cm": 0.31,
                        "radiacao_solar_wm2": 0.0,
                        "vento_velocidade_ms": 8.0,
                        "vento_rajada_ms": 12.0,
                    },
                    "ndvi_historico": {
                        "periodo": "2026-08",
                        "data_referencia": "2026-08-01",
                        "ndvi_medio": 0.42,
                        "quantidade_imagens": 7,
                    },
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_file = Path(tmp_dir) / "src" / "Ingestao" / "Ingestão_central.py"
            fake_file.parent.mkdir(parents=True, exist_ok=True)

            with patch.object(self.mod, "__file__", str(fake_file)):
                csv_path = self.mod.salvar_dataset_historico(dataset, "Talhao Teste")

            self.assertTrue(csv_path.exists())
            df = pd.read_csv(csv_path)
            self.assertEqual(len(df), 1)
            for coluna in [
                "evapotranspiracao_mm",
                "temperatura_solo_18cm_c",
                "umidade_solo_9_27cm",
                "vento_rajada_ms",
                "ndvi_medio",
            ]:
                self.assertIn(coluna, df.columns)

    def test_build_dataset_historico_quando_api_retorna_vazio(self):
        with patch.object(self.mod, "fetch_openmeteo_agro_data", return_value={}), patch.object(
            self.mod, "extrair_ndvi_historico", return_value=[]
        ):
            dataset = self.mod.build_dataset_historico(-21.1, -47.8, "Talhao Sem Dados")

        self.assertEqual(dataset["talhao"], "Talhao Sem Dados")
        self.assertEqual(dataset["janela_meteo"]["total_horarios"], 0)
        self.assertEqual(dataset["ndvi_historico_resumo"]["periodos_encontrados"], 0)
        self.assertEqual(dataset["ndvi_historico_resumo"]["periodos_com_ndvi"], 0)
        self.assertEqual(dataset["registros"], [])


class TestIngestaoTempoReal(unittest.TestCase):
    def setUp(self):
        fake_openmeteo = types.ModuleType("extract_openmeteo")
        fake_openmeteo.fetch_openmeteo_forecast_data = lambda *args, **kwargs: {}

        fake_openweather = types.ModuleType("extract_openweather")
        fake_openweather.fetch_openweather = lambda *args, **kwargs: {}

        self.mod = load_module(
            INGESTAO_DIR / "Ingestao_tempo_real.py",
            "ingestao_tempo_real_test",
            {
                "extract_openmeteo": fake_openmeteo,
                "extract_openweather": fake_openweather,
            },
        )

    def test_coletar_dados_tempo_real_monta_snapshot(self):
        weather_mock = {
            "main": {"temp": 25.0, "temp_min": 20.0, "temp_max": 27.0, "humidity": 60},
            "wind": {"speed": 5.2, "gust": 9.1},
            "weather": [{"description": "clear sky"}],
        }
        forecast_mock = {"hourly": {"time": ["2026-08-14T00:00"], "temperature_2m": [24.0]}}

        with patch.object(self.mod, "fetch_openweather", return_value=weather_mock), patch.object(
            self.mod, "fetch_openmeteo_forecast_data", return_value=forecast_mock
        ):
            snapshot = self.mod.coletar_dados_tempo_real(-21.1, -47.8, "Talhao Teste")

        self.assertEqual(snapshot["talhao"], "Talhao Teste")
        self.assertEqual(snapshot["openweather"]["temperatura_atual_c"], 25.0)
        self.assertEqual(snapshot["openweather"]["vento_rajada_ms"], 9.1)
        self.assertEqual(snapshot["previsao_openmeteo_3dias"], forecast_mock)

    def test_salvar_snapshot_sqlite_persiste_registro(self):
        snapshot = {
            "data_hora_coleta": "2026-08-14T10:00:00",
            "talhao": "Talhao Teste",
            "lat": -21.1,
            "lon": -47.8,
            "openweather": {
                "condicao": "clear sky",
                "temperatura_atual_c": 25.0,
                "umidade_relativa_pct": 60,
                "vento_velocidade_ms": 5.2,
                "vento_rajada_ms": 9.1,
            },
            "previsao_openmeteo_3dias": {"hourly": {"time": ["2026-08-14T00:00"]}},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_file = Path(tmp_dir) / "src" / "Ingestao" / "Ingestao_tempo_real.py"
            fake_file.parent.mkdir(parents=True, exist_ok=True)

            with patch.object(self.mod, "__file__", str(fake_file)):
                db_path = self.mod.salvar_snapshot_sqlite(snapshot)

            self.assertTrue(db_path.exists())

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM medicoes_tempo_real")
            total = cur.fetchone()[0]
            conn.close()

            self.assertEqual(total, 1)

    def test_coletar_dados_tempo_real_quando_apis_falham(self):
        with patch.object(self.mod, "fetch_openweather", return_value=None), patch.object(
            self.mod, "fetch_openmeteo_forecast_data", return_value={}
        ):
            snapshot = self.mod.coletar_dados_tempo_real(-21.1, -47.8, "Talhao Fallback")

        self.assertEqual(snapshot["talhao"], "Talhao Fallback")
        self.assertEqual(snapshot["previsao_openmeteo_3dias"], {})
        self.assertIsNone(snapshot["openweather"]["temperatura_atual_c"])
        self.assertIsNone(snapshot["openweather"]["vento_rajada_ms"])

    def test_salvar_snapshot_sqlite_sem_bloco_openweather(self):
        snapshot = {
            "data_hora_coleta": "2026-08-14T10:00:00",
            "talhao": "Talhao Sem OW",
            "lat": -21.1,
            "lon": -47.8,
            "previsao_openmeteo_3dias": {},
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_file = Path(tmp_dir) / "src" / "Ingestao" / "Ingestao_tempo_real.py"
            fake_file.parent.mkdir(parents=True, exist_ok=True)

            with patch.object(self.mod, "__file__", str(fake_file)):
                db_path = self.mod.salvar_snapshot_sqlite(snapshot)

            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT condicao, temperatura_atual_c, umidade_relativa_pct, vento_velocidade_ms, vento_rajada_ms "
                "FROM medicoes_tempo_real LIMIT 1"
            )
            row = cur.fetchone()
            conn.close()

        self.assertEqual(row, (None, None, None, None, None))


if __name__ == "__main__":
    unittest.main()
