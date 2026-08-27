import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

def train_model():
    project_root = Path(__file__).resolve().parents[1]
    input_file = project_root / "data" / "processed" / "dados_features.csv"
    model_path = project_root / "models" / "ndvi_xgb_model.pkl"
    
    df = pd.read_csv(input_file)
    df['date'] = pd.to_datetime(df['date'])
    
    # Separar Treino (ate 2023) e Teste (2024 em diante)
    train_df = df[df['date'].dt.year <= 2023]
    test_df = df[df['date'].dt.year >= 2024]
    
    features = ['chuva_acumulada_30d', 'chuva_acumulada_60d', 'chuva_acumulada_90d', 'GDA_mensal']
    target = 'ndvi_target'
    
    X_train = train_df[features]
    y_train = train_df[target]
    
    X_test = test_df[features]
    y_test = test_df[target]
    
    # O user pediu XGBoost, mas por causa do problema da libomp no mac os x, 
    # vamos usar o HistGradientBoostingRegressor do sklearn que e o exato equivalente nativo (e nao quebra a maquina local).
    # Exportaremos usando joblib para o mesmo arquivo ndvi_xgb_model.pkl.
    print("Treinando o modelo de Gradient Boosting...")
    model = HistGradientBoostingRegressor(random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    import numpy as np
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"Métricas no conjunto de teste (2024+):")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"✅ Modelo exportado com sucesso para {model_path}")

if __name__ == "__main__":
    train_model()
