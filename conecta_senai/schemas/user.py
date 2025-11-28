"""Pydantic models for user-related operations."""

from datetime import date
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from conecta_senai.services.user_service import PASSWORD_REGEX


def _is_cpf_valid(cpf: str) -> bool:
    cpf = ''.join(re.findall(r"\d", str(cpf)))
    if not cpf or len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10 % 11) % 10
    if d1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10 % 11) % 10
    return d2 == int(cpf[10])


class UserCreateSchema(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    confirmar_senha: Optional[str] = Field(default=None, alias="confirmarSenha")
    username: Optional[str] = None

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Senha deve ter ao menos 8 caracteres, incluindo letra maiúscula, letra minúscula, número e caractere especial"
            )
        return v

    @model_validator(mode="after")
    def senhas_coincidem(self):
        if self.confirmar_senha is not None and self.senha != self.confirmar_senha:
            raise ValueError("As senhas não coincidem")
        return self

    class Config:
        populate_by_name = True


class UserUpdateSchema(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    empresa: Optional[str] = None
    data_nascimento: Optional[date] = None
    tipo: Optional[str] = None
    senha: Optional[str] = None
    senha_atual: Optional[str] = Field(default=None, alias="senha_atual")

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        if v:
            digits = ''.join(filter(str.isdigit, v))
            if not _is_cpf_valid(digits):
                raise ValueError("CPF inválido")
            return digits
        return v

    @field_validator("senha")
    @classmethod
    def validar_nova_senha(cls, v: str) -> str:
        if v and not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Senha deve ter ao menos 8 caracteres, incluindo letra maiúscula, letra minúscula, número e caractere especial"
            )
        return v

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        if v and v not in {"comum", "admin", "secretaria"}:
            raise ValueError("Tipo de usuário inválido")
        return v

    @field_validator("data_nascimento", mode="before")
    @classmethod
    def parse_data(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, date):
            return v
        try:
            return date.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError("Formato de data de nascimento inválido. Use YYYY-MM-DD")

    class Config:
        populate_by_name = True
