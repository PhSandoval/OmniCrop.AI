"""
Pipeline de Treinamento e Calibração de Modelos Preditivos de NDVI Multi-Cultura.
Suporta as 5 principais cadeias do agronegócio brasileiro no OmniCrop AI:
1. Cana-de-Açúcar (sugarcane)
2. Soja (soybean)
3. Milho (corn)
4. Café (coffee)
5. Pecuária / Pastagem (pasture)

Para cada cultura:
- Aplica os parâmetros biológicos específicos (Tb e Kc) do crop_config.py.
- Constrói as features de acúmulo térmico (GDA) e hídrico (chuva 30d/60d/90d).
- Treina modelo de machine learning (HistGradientBoostingRegressor) com separação temporal.
- Avalia métricas de validação (MAE, RMSE, R²) e exporta o modelo serializado (.pkl).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Adiciona a raiz do projeto ao sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.crop_config import get_crop_parameters, list_supported_crops, CropParameters


FEATURE_KEYS = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']


def _load_base_weather() -> pd.DataFrame:
    """Carrega o histórico meteorológico diário base de 5 anos."""
    candidates = [
        PROJECT_ROOT / "data" / "processed" / "Dataset_SugarCane_processed.csv",
        PROJECT_ROOT / "data" / "processed" / "dados_features.csv",
    ]
    for c in candidates:
        if c.exists():
            df = pd.read_csv(c)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            return df
    raise FileNotFoundError("Base meteorológica histórica não encontrada em data/processed/")


def generate_crop_synthetic_target(df: pd.DataFrame, crop_params: CropParameters) -> pd.Series:
    """
    Gera o target fisiológico de NDVI de referência com base na dinâmica agronômica real:
    - Soja: Ciclo estival com pico em R1-R5 (0.75-0.86), dessecação/colheita e pousio de inverno.
    - Milho: Rápida biomassa foliar com pico em VT/R1 (0.80-0.88), sensível a déficit hídrico.
    - Café: Cultura perene arbustiva com dossel foliar perene (NDVI entre 0.52 e 0.82), sensível a chuva 60/90d.
    - Pecuária: Forrageira tropical (Brachiaria/Panicum), forte contraste entre águas (0.62-0.76) e seca (0.32-0.45).
    - Cana: Gramínea semi-perene C4 de alta biomassa.
    """
    crop_id = crop_params.crop_id
    dates = pd.to_datetime(df['date'])
    day_of_year = dates.dt.dayofyear
    month = dates.dt.month

    rain_30d = df['chuva_acumulada_30d'].fillna(0).to_numpy()
    rain_60d = df['chuva_acumulada_60d'].fillna(0).to_numpy()
    rain_90d = df['chuva_acumulada_90d'].fillna(0).to_numpy()
    gda_mensal = df['GDA_mensal'].fillna(0).to_numpy()

    n = len(df)
    np.random.seed(42)
    noise = np.random.normal(0, 0.015, size=n)

    if crop_id == "sugarcane":
        # Se existir ndvi_target ou ndvi_medio histórico no dataset, preserva
        if 'ndvi_target' in df.columns and df['ndvi_target'].notna().mean() > 0.8:
            return df['ndvi_target']
        if 'ndvi_medio' in df.columns and df['ndvi_medio'].notna().mean() > 0.8:
            return df['ndvi_medio']
        # Curva de cana: base 0.35 a 0.78
        base_curve = 0.40 + 0.25 * np.sin((day_of_year - 60) * 2 * np.pi / 365.25)
        water_factor = np.clip(rain_60d / 200.0, 0.4, 1.2)
        ndvi = base_curve * water_factor + noise
        return pd.Series(np.clip(ndvi, 0.15, 0.85))

    elif crop_id == "soybean":
        # Soja: Safra de verão (Out a Março). Pico em Jan/Fev (dias 15 a 55).
        # Dias 285 a 365 (Out-Dez) e 1 a 75 (Jan-Março): Safra ativa.
        # Dias 76 a 284: Pousio / entre-safra / dessecação.
        is_safra = (dates.dt.month >= 10) | (dates.dt.month <= 3)
        # Curva fenológica senoidal ajustada para a safra de verão
        pheno = np.where(
            is_safra,
            0.55 + 0.25 * np.sin((month + 2) * np.pi / 6.0),
            0.22 + 0.05 * np.sin(month * np.pi / 12.0)
        )
        # Resposta à chuva nos 30d e 60d
        water_benefit = np.clip((rain_30d - 40.0) / 180.0, -0.15, 0.18)
        thermal_benefit = np.clip((gda_mensal - 300.0) / 500.0, -0.05, 0.08)
        ndvi = pheno + water_benefit + thermal_benefit + noise
        return pd.Series(np.clip(ndvi, 0.18, 0.88))

    elif crop_id == "corn":
        # Milho: Safra de verão e Safrinha (Picos em Dez/Jan e Abril/Maio)
        safra_verao = (dates.dt.month >= 11) | (dates.dt.month <= 2)
        safrinha = (dates.dt.month >= 3) & (dates.dt.month <= 7)

        pheno = np.where(
            safra_verao,
            0.58 + 0.24 * np.sin((month + 1) * np.pi / 4.0),
            np.where(safrinha, 0.52 + 0.22 * np.sin((month - 2) * np.pi / 4.0), 0.25)
        )
        water_impact = np.clip((rain_60d - 60.0) / 220.0, -0.18, 0.15)
        ndvi = pheno + water_impact + noise
        return pd.Series(np.clip(ndvi, 0.20, 0.89))

    elif crop_id == "coffee":
        # Café: Cultura perene arbustiva. Dossel constante (mínimo ~0.50).
        # Primavera/Verão (Out-Mar): Alta atividade vegetativa, florada e granação (NDVI 0.70 a 0.82)
        # Inverno (Jun-Ago): Maturação/Colheita e estresse hídrico leve (NDVI 0.54 a 0.64)
        seasonal_cycle = 0.65 + 0.12 * np.sin((month - 9) * 2 * np.pi / 12.0)
        # Café depende muito da água profunda acumulada em 90 dias
        deep_water_impact = np.clip((rain_90d - 120.0) / 350.0, -0.10, 0.12)
        thermal_impact = np.clip((gda_mensal - 250.0) / 600.0, -0.04, 0.06)
        ndvi = seasonal_cycle + deep_water_impact + thermal_impact + noise
        return pd.Series(np.clip(ndvi, 0.48, 0.83))

    elif crop_id == "pasture":
        # Pecuária (Brachiaria): Gramínea tropical C4 perene com estacionalidade estival
        # Estação chuvosa (Out-Abr): Rápido rebrote e alta biomassa (NDVI 0.62 a 0.76)
        # Estação seca (Mai-Set): Feno em pé, dormência induzida por seca e frio (NDVI 0.32 a 0.45)
        seasonal_pasture = 0.53 + 0.18 * np.sin((month - 10) * 2 * np.pi / 12.0)
        rain_pulse = np.clip((rain_30d - 30.0) / 150.0, -0.15, 0.16)
        cold_dormancy = np.where(gda_mensal < 150.0, -0.08, 0.04)
        ndvi = seasonal_pasture + rain_pulse + cold_dormancy + noise
        return pd.Series(np.clip(ndvi, 0.28, 0.78))

    else:
        # Padrão genérico
        return pd.Series(np.clip(0.50 + 0.20 * np.sin(day_of_year * 2 * np.pi / 365.25) + noise, 0.20, 0.80))


def build_crop_dataset(crop_id: str) -> pd.DataFrame:
    """
    Constrói a tabela de features específica para a cultura informada
    utilizando a temperatura base (Tb) e o Kc do crop_config.
    """
    crop_params = get_crop_parameters(crop_id)
    raw_df = _load_base_weather()

    df = raw_df.copy()
    tb = crop_params.base_temp_celsius

    # 1. Acúmulos de Chuva (30d, 60d, 90d)
    if 'precipitacao_total' not in df.columns:
        df['precipitacao_total'] = df.get('precipitation_sum', 0.0)

    df['chuva_acumulada_30d'] = df['precipitacao_total'].rolling(window=30, min_periods=1).sum()
    df['chuva_acumulada_60d'] = df['precipitacao_total'].rolling(window=60, min_periods=1).sum()
    df['chuva_acumulada_90d'] = df['precipitacao_total'].rolling(window=90, min_periods=1).sum()

    # 2. Graus-Dia de Desenvolvimento (GDD / GDA) usando o Tb específico da cultura
    t_mean = df.get('t_mean', (df.get('t_max', 28.0) + df.get('t_min', 18.0)) / 2.0)
    df['gdd_diario'] = np.maximum(0.0, t_mean - tb)
    df['GDA_mensal'] = df['gdd_diario'].rolling(window=30, min_periods=1).sum()

    # 3. Balanço Hídrico com Kc específico
    et0 = df.get('evapotranspiracao_total', df.get('et0_fao_evapotranspiration', 4.0))
    df['etc_diaria'] = et0 * crop_params.kc_default
    df['balanco_hidrico_30d'] = (df['precipitacao_total'] - df['etc_diaria']).rolling(window=30, min_periods=1).sum()

    # 4. Target de NDVI
    df['ndvi_target'] = generate_crop_synthetic_target(df, crop_params)

    # Limpeza de NaNs
    df = df.dropna(subset=FEATURE_KEYS + ['ndvi_target']).reset_index(drop=True)
    return df


def train_single_crop_model(crop_id: str) -> Dict[str, Any]:
    """
    Treina o modelo preditivo para uma cultura e serializa o artefato em src/models/{crop_id}_ndvi.pkl.
    """
    crop_params = get_crop_parameters(crop_id)
    print(f"\n🌾 Processando e treinando modelo para: {crop_params.name} ({crop_id})...")

    df = build_crop_dataset(crop_id)

    # Divisão Temporal: Treino (até 2023), Teste (2024 em diante)
    train_mask = df['date'].dt.year <= 2023
    test_mask = df['date'].dt.year >= 2024

    X_train = df.loc[train_mask, FEATURE_KEYS]
    y_train = df.loc[train_mask, 'ndvi_target']

    X_test = df.loc[test_mask, FEATURE_KEYS]
    y_test = df.loc[test_mask, 'ndvi_target']

    if len(X_train) == 0 or len(X_test) == 0:
        # Fallback para split simples 80/20 se os anos não cobrirem a faixa
        split_idx = int(len(df) * 0.8)
        X_train, X_test = df.loc[:split_idx, FEATURE_KEYS], df.loc[split_idx:, FEATURE_KEYS]
        y_train, y_test = df.loc[:split_idx, 'ndvi_target'], df.loc[split_idx:, 'ndvi_target']

    # Treina o regressor Gradient Boosting
    model = HistGradientBoostingRegressor(
        max_iter=150,
        learning_rate=0.08,
        min_samples_leaf=15,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Avaliação no teste
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Exportação do modelo
    models_dir = PROJECT_ROOT / "src" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_file = models_dir / f"{crop_id}_ndvi.pkl"
    joblib.dump(model, model_file)

    # Exportação opcional do dataset processado para auditoria
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_file = processed_dir / f"dados_features_{crop_id}.csv"
    df.to_csv(processed_file, index=False)

    print(f"  ✅ Modelo exportado: {model_file}")
    print(f"  📈 Métricas Teste (2024+): MAE={mae:.4f} | RMSE={rmse:.4f} | R²={r2:.4f}")

    return {
        "crop_id": crop_id,
        "name": crop_params.name,
        "model_path": str(model_file),
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2), 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }


def train_all_supported_crops() -> Dict[str, Dict[str, Any]]:
    """Treina os modelos para todas as culturas cadastradas no CROP_REGISTRY."""
    results = {}
    crops = list_supported_crops()
    print(f"🚀 Iniciando treinamento multi-cultura para {len(crops)} culturas...")

    for crop in crops:
        res = train_single_crop_model(crop.crop_id)
        results[crop.crop_id] = res

    # Garante que o modelo padrão legado ndvi_model.pkl aponte para sugarcane
    sugarcane_model = PROJECT_ROOT / "src" / "models" / "sugarcane_ndvi.pkl"
    legacy_model = PROJECT_ROOT / "src" / "models" / "ndvi_model.pkl"
    if sugarcane_model.exists():
        import shutil
        shutil.copy2(sugarcane_model, legacy_model)

    print("\n" + "=" * 70)
    print("🏆 RESUMO GERAL DO TREINAMENTO MULTI-CULTURA")
    print("=" * 70)
    for cid, m in results.items():
        print(f"  🌾 {m['name']:<22} ({cid:<10}) | MAE: {m['mae']:.4f} | RMSE: {m['rmse']:.4f} | R²: {m['r2']:.4f}")
    print("=" * 70)
    return results


def main():
    parser = argparse.ArgumentParser(description="Treinamento Multi-Cultura OmniCrop AI")
    parser.add_argument("--crop", choices=["all", "sugarcane", "soybean", "corn", "coffee", "pasture"], default="all")
    args = parser.parse_args()

    if args.crop == "all":
        train_all_supported_crops()
    else:
        train_single_crop_model(args.crop)


if __name__ == "__main__":
    main()
