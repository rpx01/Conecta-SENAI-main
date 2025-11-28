from .sala import SalaCreateSchema, SalaUpdateSchema
from .instrutor import InstrutorCreateSchema, InstrutorUpdateSchema
from .ocupacao import OcupacaoCreateSchema, OcupacaoUpdateSchema
from .rateio import RateioConfigCreateSchema, LancamentoRateioSchema
from .user import UserCreateSchema, UserUpdateSchema
from .noticia import NoticiaSchema
from .noticia_validacao import NoticiaCreateSchema, NoticiaUpdateSchema

__all__ = [
    'SalaCreateSchema', 'SalaUpdateSchema',
    'InstrutorCreateSchema', 'InstrutorUpdateSchema',
    'OcupacaoCreateSchema', 'OcupacaoUpdateSchema',
    'RateioConfigCreateSchema', 'LancamentoRateioSchema',
    'UserCreateSchema', 'UserUpdateSchema',
    'NoticiaSchema', 'NoticiaCreateSchema', 'NoticiaUpdateSchema',
]
