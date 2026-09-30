import unittest
from streamlit.testing.v1 import AppTest

class TestAppUI(unittest.TestCase):
    def test_simulador_state_without_talhao(self):
        """Teste de Interface (Palco): Verifica se o Streamlit segura o erro se o usuário não escolheu o talhão."""
        # Cria uma instância virtual do AppTest para a página do Simulador
        at = AppTest.from_file("../app/pages/2_Simulador.py")
        
        # Roda o app virtualmente (sem navegador)
        at.run()
        
        # Sem preencher nenhum input, vamos simular o clique no botão "Simular!"
        # Se o botão existir e for clicado, ele não deve dar um crash horrível de KeyError
        if at.button:
            at.button[0].click()
            at.run()
            
            # O sistema deve continuar vivo sem exceptions na tela (ex: IndexError)
            self.assertFalse(at.exception)
            
            # (Opcional) Podemos verificar se existe algum texto de warning amigável
            # Como "Por favor, selecione um talhão primeiro." dependendo da implementação real
            
if __name__ == '__main__':
    unittest.main()
