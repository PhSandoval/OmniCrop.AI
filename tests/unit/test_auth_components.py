"""
Testes unitários para validação de credenciais e autenticação em components/auth.py.
"""
from components.auth import _validate_email, _validate_password


def test_validate_email():
    assert _validate_email("") == "O e-mail não pode estar em branco."
    assert _validate_email("   ") == "O e-mail não pode estar em branco."
    assert _validate_email("invalido") == "Informe um endereço de e-mail válido (ex: nome@dominio.com)."
    assert _validate_email("sem_dominio@") == "Informe um endereço de e-mail válido (ex: nome@dominio.com)."
    assert _validate_email("teste@exemplo") == "Informe um endereço de e-mail válido (ex: nome@dominio.com)."
    assert _validate_email("produtor@fazenda.com.br") is None
    assert _validate_email("  usuario@omnicrop.ai  ") is None


def test_validate_password():
    assert _validate_password("") == "A senha não pode estar em branco."
    assert _validate_password("1234567") == "A senha deve ter pelo menos 8 caracteres."
    assert _validate_password("senha_valida_123") is None
