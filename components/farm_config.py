"""Gerencia a configuração salva da fazenda em data/farm_config.json."""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "farm_config.json"


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_config() -> dict | None:
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def is_configured() -> bool:
    return CONFIG_PATH.exists()
