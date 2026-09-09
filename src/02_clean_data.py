import pandas as pd
from pathlib import Path

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

if __name__ == '__main__':
    clean_data()
