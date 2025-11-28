from pydantic import BaseModel, Field
from typing import List

class RateioConfigCreateSchema(BaseModel):
    filial: str
    uo: str
    cr: str
    classe_valor: str
    descricao: str | None = None

class LancamentoItemSchema(BaseModel):
    rateio_config_id: int
    percentual: float = Field(gt=0)

class LancamentoRateioSchema(BaseModel):
    instrutor_id: int
    ano: int
    mes: int
    lancamentos: List[LancamentoItemSchema]
