from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

class InstrutorCreateSchema(BaseModel):
    nome: str
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    area_atuacao: Optional[str] = None
    disponibilidade: Optional[List[str]] = Field(default_factory=list)
    status: Optional[str] = 'ativo'
    observacoes: Optional[str] = None

class InstrutorUpdateSchema(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    area_atuacao: Optional[str] = None
    disponibilidade: Optional[List[str]] = None
    status: Optional[str] = None
    observacoes: Optional[str] = None
