"""Inicialização do pacote de modelos."""

from conecta_senai.extensions import db

from .refresh_token import RefreshToken  # noqa: E402
from .recurso import Recurso  # noqa: E402
from .audit_log import AuditLog  # noqa: E402
from .rateio import RateioConfig, LancamentoRateio  # noqa: E402
from .log_rateio import LogLancamentoRateio  # noqa: E402
from .user import User  # noqa: E402
from .sala import Sala  # noqa: E402
from .agendamento import Agendamento, Notificacao  # noqa: E402
from .instrutor import Instrutor  # noqa: E402
from .ocupacao import Ocupacao  # noqa: E402
from .treinamento import (  # noqa: E402
    LocalRealizacao,
    Treinamento,
    TurmaTreinamento,
    InscricaoTreinamento,
)
from .inscricao_treinamento import (
    InscricaoTreinamentoFormulario,
)  # noqa: E402
from .email_secretaria import EmailSecretaria  # noqa: E402
from .secretaria_treinamentos import SecretariaTreinamentos  # noqa: E402
from .horario import Horario  # noqa: E402
from .noticia import Noticia  # noqa: E402
from .imagem_noticia import ImagemNoticia  # noqa: E402
from .suporte_chamado import SuporteChamado  # noqa: E402
from .suporte_anexo import SuporteAnexo  # noqa: E402
from .suporte_basedados import SuporteTipoEquipamento, SuporteArea  # noqa: E402

__all__ = [
    "db",
    "RefreshToken",
    "Recurso",
    "AuditLog",
    "RateioConfig",
    "LancamentoRateio",
    "LogLancamentoRateio",
    "User",
    "Sala",
    "Agendamento",
    "Notificacao",
    "Instrutor",
    "Ocupacao",
    "LocalRealizacao",
    "Treinamento",
    "TurmaTreinamento",
    "InscricaoTreinamento", 
    "InscricaoTreinamentoFormulario", 
    "EmailSecretaria", 
    "SecretariaTreinamentos",
    "Noticia",
    "ImagemNoticia",
    "SuporteChamado",
    "SuporteAnexo",
    "SuporteTipoEquipamento",
    "SuporteArea",
]
