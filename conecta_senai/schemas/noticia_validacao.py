"""Esquemas de validação para o módulo de notícias."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _parse_datetime(value: Optional[str | datetime]) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    texto = str(value).strip()
    if not texto:
        return None
    if texto.endswith("Z"):
        texto = f"{texto[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(texto)
    except (TypeError, ValueError) as exc:  # pragma: no cover - validação explícita
        raise ValueError("Data inválida. Use o formato ISO 8601.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class NoticiaBaseSchema(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    resumo: Optional[str] = Field(default=None, max_length=500)
    conteudo: str = Field(min_length=20)
    autor: Optional[str] = Field(default=None, max_length=120)
    imagem_url: Optional[str] = Field(default=None, max_length=500)
    destaque: bool = False
    ativo: bool = True
    marcar_calendario: bool = Field(default=False, alias="marcarCalendario")
    data_publicacao: Optional[datetime] = Field(default=None, alias="dataPublicacao")
    data_agendamento: Optional[datetime] = Field(default=None, alias="dataAgendamento")
    data_evento: Optional[datetime] = Field(default=None, alias="dataEvento")

    @field_validator("titulo", "resumo", "conteudo", "autor", "imagem_url", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Optional[str]):
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned == "":
                return None
            return cleaned
        return value

    @field_validator("resumo")
    @classmethod
    def validar_resumo(cls, value: Optional[str]):
        if value is not None and len(value) < 10:
            raise ValueError("O resumo deve conter ao menos 10 caracteres ou ser omitido.")
        return value

    @field_validator("data_publicacao", "data_agendamento", "data_evento", mode="before")
    @classmethod
    def validar_data_publicacao(cls, value):
        return _parse_datetime(value)

    class Config:
        populate_by_name = True


class NoticiaCreateSchema(NoticiaBaseSchema):
    pass


class NoticiaUpdateSchema(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=3, max_length=200)
    resumo: Optional[str] = Field(default=None, max_length=500)
    conteudo: Optional[str] = Field(default=None, min_length=20)
    autor: Optional[str] = Field(default=None, max_length=120)
    imagem_url: Optional[str] = Field(default=None, max_length=500)
    destaque: Optional[bool] = None
    ativo: Optional[bool] = None
    marcar_calendario: Optional[bool] = Field(default=None, alias="marcarCalendario")
    data_publicacao: Optional[datetime] = Field(default=None, alias="dataPublicacao")
    data_agendamento: Optional[datetime] = Field(default=None, alias="dataAgendamento")
    data_evento: Optional[datetime] = Field(default=None, alias="dataEvento")

    @field_validator("titulo", "resumo", "conteudo", "autor", "imagem_url", mode="before")
    @classmethod
    def sanitize_strings(cls, value: Optional[str]):
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned == "":
                return None
            return cleaned
        return value

    @field_validator("resumo")
    @classmethod
    def validar_resumo(cls, value: Optional[str]):
        if value is not None and len(value) < 10:
            raise ValueError("O resumo deve conter ao menos 10 caracteres ou ser omitido.")
        return value

    @field_validator("data_publicacao", "data_agendamento", "data_evento", mode="before")
    @classmethod
    def validar_data_publicacao(cls, value):
        return _parse_datetime(value)

    class Config:
        populate_by_name = True
