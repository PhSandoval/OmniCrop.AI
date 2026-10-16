import argparse
import sys
from pathlib import Path
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

# Adiciona a raiz do projeto ao path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.train_all_crops import train_single_crop_model, train_all_supported_crops


def train_model(crop_id: str = "sugarcane"):
    """
    Treina o modelo preditivo para a cultura informada (ou todas se crop_id='all').
    Garante compatibilidade total com invocações legadas sem argumentos.
    """
    if crop_id == "all":
        return train_all_supported_crops()
    return train_single_crop_model(crop_id)


def main():
    parser = argparse.ArgumentParser(description="Treinamento de Modelo Preditivo OmniCrop AI")
    parser.add_argument("--crop", default="sugarcane", help="Identificador da cultura ('sugarcane', 'soybean', 'corn', 'coffee', 'pasture' ou 'all')")
    args = parser.parse_args()
    train_model(args.crop)


if __name__ == "__main__":
    main()
