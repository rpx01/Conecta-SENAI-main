import pytest
from conecta_senai.routes.user import PASSWORD_REGEX

@pytest.mark.parametrize("senha", [
    "Abcdef1!",
    "Senha@123",
    "Password1!",
])
def test_password_regex_valida(senha):
    assert PASSWORD_REGEX.match(senha)

@pytest.mark.parametrize("senha", [
    "abc",
    "abcdefg",
    "SemNumero!",
    "semSimbolo1",
    "SEMMAIUS1!",
])
def test_password_regex_invalida(senha):
    assert not PASSWORD_REGEX.match(senha)
