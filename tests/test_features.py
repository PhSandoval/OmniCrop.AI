import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.live_data import _build_features

class TestFeatureEngineering(unittest.TestCase):
    def test_gda_mensal_calculation(self):
        """A base térmica da cana é 15°C. Se fizermos 30 dias de exatos 20°C, GDA diário = 5. GDA Mensal = 150."""
        # Criar dataframe dummy
        dates = pd.date_range("2023-01-01", periods=30)
        df_dummy = pd.DataFrame({
            "date": dates,
            "t_mean": [20.0] * 30,
            "precipitacao_total": [10.0] * 30, # 10mm por dia
        })
        
        # Calcular
        res_df = _build_features(df_dummy)
        
        # Última linha deve ter 30 dias de acúmulo
        last_row = res_df.iloc[-1]
        
        self.assertEqual(last_row["GDA_mensal"], 150.0)
        self.assertEqual(last_row["chuva_acumulada_30d"], 300.0) # 10mm * 30 dias
        
    def test_chuva_acumulada_limits(self):
        """Teste para garantir que as somas móveis tratam janelas menores no início dos dados (min_periods=1)."""
        dates = pd.date_range("2023-01-01", periods=5)
        df_dummy = pd.DataFrame({
            "date": dates,
            "t_mean": [25.0] * 5,
            "precipitacao_total": [5.0] * 5,
        })
        res_df = _build_features(df_dummy)
        
        # Dia 1 (index 0)
        self.assertEqual(res_df.iloc[0]["chuva_acumulada_30d"], 5.0)
        # Dia 5 (index 4)
        self.assertEqual(res_df.iloc[4]["chuva_acumulada_30d"], 25.0)

if __name__ == '__main__':
    unittest.main()
