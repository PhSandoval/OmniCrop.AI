import json
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from extract_openmeteo import fetch_openmeteo_forecast_data
from extract_openweather import fetch_openweather

load_dotenv()


def coletar_dados_tempo_real(lat: float, lon: float, nome_talhao: str):
    """Camada quente: coleta snapshot atual + previsao curta para inferencia."""
    print(f"\n=== Coleta tempo real para {nome_talhao} ===")

    weather_data = fetch_openweather(lat, lon)
    forecast_data = fetch_openmeteo_forecast_data(lat, lon, forecast_days=3)

    weather_main = weather_data.get("main", {}) if isinstance(weather_data, dict) else {}
    weather_wind = weather_data.get("wind", {}) if isinstance(weather_data, dict) else {}
    weather_condition = weather_data.get("weather", [{}])[0] if isinstance(weather_data, dict) else {}

    snapshot = {
        "talhao": nome_talhao,
        "lat": lat,
        "lon": lon,
        "data_hora_coleta": datetime.now().isoformat(timespec="seconds"),
        "openweather": {
            "condicao": weather_condition.get("description"),
            "temperatura_atual_c": weather_main.get("temp"),
            "temperatura_min_c": weather_main.get("temp_min"),
            "temperatura_max_c": weather_main.get("temp_max"),
            "umidade_relativa_pct": weather_main.get("humidity"),
            "vento_velocidade_ms": weather_wind.get("speed"),
            "vento_rajada_ms": weather_wind.get("gust"),
        },
        "previsao_openmeteo_3dias": forecast_data,
    }

    return snapshot


def salvar_snapshot_sqlite(snapshot: dict):
    """Persistencia leve para operacao diaria em SQLite."""
    project_root = Path(__file__).resolve().parents[2]
    hot_dir = project_root / "data" / "Hot"
    hot_dir.mkdir(parents=True, exist_ok=True)

    db_path = hot_dir / "tempo_real_operacao.db"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS medicoes_tempo_real (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora_coleta TEXT NOT NULL,
            talhao TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            condicao TEXT,
            temperatura_atual_c REAL,
            umidade_relativa_pct REAL,
            vento_velocidade_ms REAL,
            vento_rajada_ms REAL,
            previsao_json TEXT NOT NULL
        )
        """
    )

    ow = snapshot.get("openweather", {})
    cur.execute(
        """
        INSERT INTO medicoes_tempo_real (
            data_hora_coleta,
            talhao,
            lat,
            lon,
            condicao,
            temperatura_atual_c,
            umidade_relativa_pct,
            vento_velocidade_ms,
            vento_rajada_ms,
            previsao_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot.get("data_hora_coleta"),
            snapshot.get("talhao"),
            snapshot.get("lat"),
            snapshot.get("lon"),
            ow.get("condicao"),
            ow.get("temperatura_atual_c"),
            ow.get("umidade_relativa_pct"),
            ow.get("vento_velocidade_ms"),
            ow.get("vento_rajada_ms"),
            json.dumps(snapshot.get("previsao_openmeteo_3dias", {}), ensure_ascii=False),
        ),
    )

    conn.commit()
    conn.close()

    print(f"\n✅ Snapshot tempo real salvo em SQLite: {db_path}")
    return db_path


if __name__ == "__main__":
    snapshot = coletar_dados_tempo_real(
        lat=-21.1775,
        lon=-47.8103,
        nome_talhao="RP_Talhao_Central",
    )

    print(json.dumps(snapshot.get("openweather", {}), ensure_ascii=False, indent=2))
    salvar_snapshot_sqlite(snapshot)
