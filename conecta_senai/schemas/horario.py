from pydantic import BaseModel
from typing import Optional, Literal

TurnoLiteral = Literal["Manhã", "Tarde", "Noite", "Manhã/Tarde", "Tarde/Noite"]


class HorarioIn(BaseModel):
    nome: str
    turno: Optional[TurnoLiteral] = None


class HorarioOut(BaseModel):
    id: int
    nome: str
    turno: Optional[TurnoLiteral] = None

    class Config:
        from_attributes = True

