"""Esquemas Pydantic para o módulo de treinamentos."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date


class InscricaoTreinamentoCreateSchema(BaseModel):
    nome: str
    email: str
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    empresa: Optional[str] = None


class TreinamentoCreateSchema(BaseModel):
    """Schema para cadastro de treinamentos."""

    nome: str
    codigo: str
    capacidade_maxima: Optional[int] = None
    carga_horaria: Optional[int] = None
    tem_pratica: Optional[bool] = False
    links_materiais: Optional[List[str]] = None
    tipo: Optional[str] = None
    conteudo_programatico: Optional[str] = None


class TreinamentoUpdateSchema(BaseModel):
    """Schema para atualização parcial de treinamentos."""

    nome: Optional[str] = None
    codigo: Optional[str] = None
    capacidade_maxima: Optional[int] = None
    carga_horaria: Optional[int] = None
    tem_pratica: Optional[bool] = None
    links_materiais: Optional[List[str]] = None
    tipo: Optional[str] = None
    conteudo_programatico: Optional[str] = None


class TurmaTreinamentoCreateSchema(BaseModel):
    """Schema para criação de turmas de treinamento."""

    treinamento_id: int
    data_inicio: date
    data_fim: date
    local_realizacao: Optional[str] = None
    horario: Optional[str] = None
    instrutor_id: Optional[int] = None
    teoria_online: bool = Field(default=False)


class TurmaTreinamentoUpdateSchema(BaseModel):
    """Schema para atualização de turmas de treinamento."""

    treinamento_id: Optional[int] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    local_realizacao: Optional[str] = None
    horario: Optional[str] = None
    instrutor_id: Optional[int] = None
    teoria_online: Optional[bool] = Field(default=None)


class TreinamentoSchema(BaseModel):
    """Schema para representação de treinamentos."""

    id: int
    nome: str
    codigo: str
    capacidade_maxima: Optional[int] = None
    carga_horaria: Optional[int] = None
    tem_pratica: bool = False
    links_materiais: Optional[List[str]] = None
    tipo: Optional[str] = None
    conteudo_programatico: Optional[str] = None


class LocalRealizacaoSchema(BaseModel):
    """Schema para validação e serialização de locais de realização."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    nome: str = Field(..., min_length=1, max_length=255)
