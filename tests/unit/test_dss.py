import pytest
import sys
from pathlib import Path

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.predict import calcular_dss

def test_fase_crescimento_critico():
    """Mês de Janeiro (Crescimento), NDVI muito baixo, Simulador sobe NDVI."""
    res = calcular_dss(mes_atual=1, ndvi_atual=0.3, ndvi_projetado=0.5)
    assert res["status_title"] == "🔴 Critico"
    assert "Irrigacao de salvamento" in res["mensagem_recomendacao"]

def test_fase_maturacao_pronto_corte():
    """Mês de Agosto (Maturação), NDVI muito baixo (Secando), Simulador não importa."""
    res = calcular_dss(mes_atual=8, ndvi_atual=0.3, ndvi_projetado=0.3)
    assert res["status_title"] == "🟡 Pronto p/ Corte"
    assert "desperdício" in res["mensagem_recomendacao"]

def test_simulacao_piora_resultado():
    """Se houver intervenção de Irrigação, e o NDVI abaixar, a regra dispara um alerta de falha de estratégia."""
    res = calcular_dss(mes_atual=5, ndvi_atual=0.6, ndvi_projetado=0.4, cenario="Irrigação")
    assert res["status_title"] == "❌ Alerta Simulacao"
    assert "Estratégia não recomendada" in res["mensagem_recomendacao"]
    
def test_fase_maturacao_cana_verde():
    """Mês de Julho (Maturação), NDVI muito alto (Choveu fora de época, não acumula açúcar)."""
    res = calcular_dss(mes_atual=7, ndvi_atual=0.7, ndvi_projetado=0.7)
    assert res["status_title"] == "🟠 Alerta"
    assert "maturador químico" in res["mensagem_recomendacao"]
