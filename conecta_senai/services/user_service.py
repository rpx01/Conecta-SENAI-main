import re
from typing import Tuple, Optional, Dict, Any

from sqlalchemy.exc import SQLAlchemyError

from conecta_senai.models.user import User
from conecta_senai.repositories.user_repository import UserRepository


PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def criar_usuario(
    dados: Dict[str, Any],
) -> Tuple[Optional[User], Optional[Tuple[Dict[str, str], int]]]:

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")
    username = dados.get("username") or (email.split("@")[0] if email else "")

    if UserRepository.get_by_email(email):
        return None, ({"erro": "Email já cadastrado"}, 400)

    try:
        novo_usuario = User(
            nome=nome,
            email=email,
            senha=senha,
            tipo="comum",
            username=username,
        )
        UserRepository.add(novo_usuario)
        return novo_usuario, None
    except SQLAlchemyError as e:
        UserRepository.rollback()
        raise e
