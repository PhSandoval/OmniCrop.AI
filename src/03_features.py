import pandas as pd
from pathlib import Path
import numpy as np

def calculate_gdd(t_mean, t_base=18.0):
    return max(0, t_mean - t_base)

def build_features():
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / "data" / "interim" / "Dataset_SugarCane_interim.csv"
    output_file = project_root / "data" / "processed" / "dados_features.csv"
    
    # 1. Carregar dados limpos
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
        
        # 3. GDA (Graus-Dia Acumulados) - Temperatura base 18°C
        group['gdd_diario'] = group['t_mean'].apply(lambda x: calculate_gdd(x, t_base=18.0))
        group['GDA_mensal'] = group['gdd_diario'].rolling(window=30, min_periods=1).sum()
        
        # Manter a variavel alvo
        group['ndvi_target'] = group['ndvi_medio']
        features_df.append(group)
        
    final_df = pd.concat(features_df)
    
    # 4. Limpar NaNs gerados pelo rolling
    final_df = final_df.dropna(subset=['chuva_acumulada_90d', 'GDA_mensal', 'ndvi_target'])
    
    # Salvar
    output_file.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_file, index=False)
    print(f"Features geradas! Shape: {final_df.shape}. Salvo em {output_file}")

if __name__ == "__main__":
    build_features()
