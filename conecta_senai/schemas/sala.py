from pydantic import BaseModel, Field
from typing import List, Optional

class SalaCreateSchema(BaseModel):
    nome: str
    capacidade: int = Field(gt=0)
    recursos: Optional[List[str]] = Field(default_factory=list)
    localizacao: Optional[str] = None
    tipo: Optional[str] = None
    status: Optional[str] = 'ativa'
    observacoes: Optional[str] = None

class SalaUpdateSchema(BaseModel):
    nome: Optional[str] = None
    capacidade: Optional[int] = Field(default=None, gt=0)
    recursos: Optional[List[str]] = None
    localizacao: Optional[str] = None
    tipo: Optional[str] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None
