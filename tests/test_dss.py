import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from components.api_client import calcular_dss

class TestDSSLogic(unittest.TestCase):
    def test_fase_crescimento_critico(self):
        """Mês de Janeiro (Crescimento), NDVI muito baixo, Simulador sobe NDVI."""
        res = calcular_dss(mes_atual=1, ndvi_atual=0.3, ndvi_projetado=0.5)
        self.assertEqual(res["status_title"], "🔴 Critico")
        self.assertIn("Irrigacao de salvamento", res["mensagem_recomendacao"])

    def test_fase_maturacao_pronto_corte(self):
        """Mês de Agosto (Maturação), NDVI muito baixo (Secando), Simulador não importa."""
        res = calcular_dss(mes_atual=8, ndvi_atual=0.3, ndvi_projetado=0.3)
        self.assertEqual(res["status_title"], "🟡 Pronto p/ Corte")
        self.assertIn("desperdicio", res["mensagem_recomendacao"])

    def test_simulacao_piora_resultado(self):
        """Qualquer mês, se a simulação abaixar o NDVI projetado, a regra absoluta de Alerta dispara."""
        res = calcular_dss(mes_atual=5, ndvi_atual=0.6, ndvi_projetado=0.4)
        self.assertEqual(res["status_title"], "❌ Alerta Simulacao")
        self.assertIn("Estrategia nao recomendada", res["mensagem_recomendacao"])
        
    def test_fase_maturacao_cana_verde(self):
        """Mês de Julho (Maturação), NDVI muito alto (Choveu fora de época, não acumula açúcar)."""
        res = calcular_dss(mes_atual=7, ndvi_atual=0.7, ndvi_projetado=0.7)
        self.assertEqual(res["status_title"], "🟠 Alerta")
        self.assertIn("maturador quimico", res["mensagem_recomendacao"])

if __name__ == '__main__':
    unittest.main()
