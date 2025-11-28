from pydantic import BaseModel, EmailStr, constr, field_validator
from datetime import date

CpfStr = constr(strip_whitespace=True, min_length=11, max_length=14)


class InscricaoTreinamentoCreate(BaseModel):
    treinamento_id: int | None = None
    nome_treinamento: constr(strip_whitespace=True, min_length=2)
    matricula: constr(strip_whitespace=True, min_length=1)
    tipo_treinamento: constr(strip_whitespace=True, min_length=1)
    nome_completo: constr(strip_whitespace=True, min_length=3)
    naturalidade: constr(strip_whitespace=True, min_length=2)
    email: EmailStr
    data_nascimento: date
    cpf: CpfStr
    empresa: constr(strip_whitespace=True, min_length=1)

    @field_validator('cpf')
    @classmethod
    def valida_cpf(cls, v):
        return v
