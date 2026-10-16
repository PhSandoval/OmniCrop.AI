import pandas as pd
from pathlib import Path
import numpy as np
from src.core.crop_config import get_crop_parameters


def clean_data():
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / "data" / "raw" / "Dataset_SugarCane_unified.csv"
    output_file = project_root / "data" / "interim" / "Dataset_SugarCane_interim.csv"

    if not input_file.exists():
        print("No raw data found.")
        return

    df = pd.read_csv(input_file)

    # Padroniza nomes de colunas para lowercase e converte espacos para _
    df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]

    # Garante tipo datetime e dropa duplicatas
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df = df.drop_duplicates(subset=['timestamp', 'talhao'])
        df = df.sort_values(by=['talhao', 'timestamp']).reset_index(drop=True)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"Limpeza concluída. Dados salvos em {output_file}")


def calculate_gdd(t_mean: float, t_base: float | None = None, crop_id: str = "sugarcane") -> float:
    """
    Calcula Graus-Dia de Desenvolvimento (GDD).
    Se t_base não for informado, busca a temperatura base dinamicamente do crop_config.py
    com base no crop_id (ex: Cana=18°C, Soja=10°C, Milho=10°C).
    """
    if t_base is None:
        crop_params = get_crop_parameters(crop_id)
        t_base = crop_params.base_temp_celsius
    return max(0.0, float(t_mean) - float(t_base))


def calculate_water_balance(precipitation: float, et0: float, crop_id: str = "sugarcane") -> float:
    """
    Calcula o Balanço Hídrico Líquido ajustado pela evapotranspiração da cultura (ETc = ET0 * Kc).
    Busca o Kc padrão da cultura dinamicamente no crop_config.py.
    """
    crop_params = get_crop_parameters(crop_id)
    etc = float(et0) * crop_params.kc_default
    return round(float(precipitation) - etc, 2)


def build_features(crop_id: str = "sugarcane"):
    """
    Gera features agronômicas parametrizadas para a cultura especificada.
    """
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / "data" / "interim" / "Dataset_SugarCane_interim.csv"
    output_file = project_root / "data" / "processed" / "dados_features.csv"

    crop_params = get_crop_parameters(crop_id)
    t_base = crop_params.base_temp_celsius

    # 1. Carregar dados limpos
    if not input_file.exists():
        print("Arquivo interim não encontrado para build_features.")
        return

    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # O interim_data é horário. Vamos agregar diariamente primeiro.
    df['date'] = df['timestamp'].dt.date
    daily_df = df.groupby(['talhao', 'date']).agg(
        t_mean=('temperatura_2m', 'mean'),
        t_max=('temperatura_2m', 'max'),
        t_min=('temperatura_2m', 'min'),
        precipitacao_total=('precipitacao_mm', 'sum'),
        evapotranspiracao_total=('evapotranspiracao_mm', 'sum'),
        umidade_solo_mean=('umidade_solo_9_27cm', 'mean'),
        radiacao_solar_mean=('radiacao_solar_wm2', 'mean'),
        ndvi_medio=('ndvi_medio', 'first')
    ).reset_index()

    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values(['talhao', 'date']).reset_index(drop=True)

    features_df = []
    for talhao, group in daily_df.groupby('talhao'):
        # 2. Criar Features (Rolling Sums)
        group['chuva_acumulada_30d'] = group['precipitacao_total'].rolling(window=30, min_periods=1).sum()
        group['chuva_acumulada_60d'] = group['precipitacao_total'].rolling(window=60, min_periods=1).sum()
        group['chuva_acumulada_90d'] = group['precipitacao_total'].rolling(window=90, min_periods=1).sum()

        # 3. GDA (Graus-Dia Acumulados) - Dinâmico por cultura
        group['gdd_diario'] = group['t_mean'].apply(lambda x: calculate_gdd(x, t_base=t_base, crop_id=crop_id))
        group['GDA_mensal'] = group['gdd_diario'].rolling(window=30, min_periods=1).sum()

        # 4. Balanço Hídrico Acumulado 30d com Kc
        group['etc_diaria'] = group['evapotranspiracao_total'] * crop_params.kc_default
        group['balanco_hidrico_30d'] = (group['precipitacao_total'] - group['etc_diaria']).rolling(window=30, min_periods=1).sum()

        # Manter a variavel alvo
        group['ndvi_target'] = group['ndvi_medio']
        features_df.append(group)

    final_df = pd.concat(features_df)

    # Limpar NaNs gerados pelo rolling
    final_df = final_df.dropna(subset=['chuva_acumulada_90d', 'GDA_mensal', 'ndvi_target'])

    # Salvar
    output_file.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_file, index=False)
    print(f"Features geradas para '{crop_params.name}'! Shape: {final_df.shape}. Salvo em {output_file}")


if __name__ == "__main__":
    clean_data()
    build_features()
