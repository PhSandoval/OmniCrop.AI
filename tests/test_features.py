import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.live_data import _build_features

class TestFeatureEngineering(unittest.TestCase):
    def test_gda_mensal_calculation(self):
        """Teste agronômico preciso do GDA com base 18°C (sem valores negativos)."""
        # Temperaturas: [20, 22, 15, 10, 25] -> Esperado GDA diário: [2, 4, 0, 0, 7]
        dates = pd.date_range("2023-01-01", periods=5)
        df_dummy = pd.DataFrame({
            "date": dates,
            "t_mean": [20.0, 22.0, 15.0, 10.0, 25.0],
            "precipitacao_total": [0.0] * 5,
        })
        
        # Calcular features
        res_df = _build_features(df_dummy)
        
        # Os valores diários de gdd
        gda_diario = res_df["gdd"].tolist()
        self.assertEqual(gda_diario, [2.0, 4.0, 0.0, 0.0, 7.0])
        
        # O GDA Acumulado da janela (GDA_mensal usa rolling de 30, então a última linha pega a soma de tudo)
        gda_acumulado = res_df.iloc[-1]["GDA_mensal"]
        self.assertEqual(gda_acumulado, 13.0)

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
