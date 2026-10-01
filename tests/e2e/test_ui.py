import pytest
from streamlit.testing.v1 import AppTest

def test_simulador_state_without_talhao():
    """Teste de Interface (Palco): Verifica se o Streamlit segura o erro se o usuário não escolheu o talhão."""
    # Cria uma instância virtual do AppTest para a página do Simulador
    at = AppTest.from_file("../../pages/2_Simulador.py")
    
    # Roda o app virtualmente (sem navegador)
    at.run()
    
    # Sem preencher nenhum input, simula clique no botão "Simular!"
    if at.button:
        at.button[0].click()
        at.run()
        
        # O sistema deve continuar vivo sem exceptions na tela
        assert not at.exception
