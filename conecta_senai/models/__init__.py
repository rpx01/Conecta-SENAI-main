from conecta_senai.extensions import db

from .refresh_token import RefreshToken
from .recurso import Recurso
from .audit_log import AuditLog
from .rateio import RateioConfig, LancamentoRateio
from .log_rateio import LogLancamentoRateio
from .user import User
from .sala import Sala
from .agendamento import Agendamento, Notificacao
from .instrutor import Instrutor
from .ocupacao import Ocupacao
from .treinamento import (
    LocalRealizacao,
    Treinamento,
    TurmaTreinamento,
    InscricaoTreinamento,
)
from .inscricao_treinamento import (
    InscricaoTreinamentoFormulario,
)
from .email_secretaria import EmailSecretaria
from .secretaria_treinamentos import SecretariaTreinamentos
from .horario import Horario
from .noticia import Noticia
from .imagem_noticia import ImagemNoticia
from .suporte_chamado import SuporteChamado
from .suporte_anexo import SuporteAnexo
from .suporte_basedados import SuporteTipoEquipamento, SuporteArea
from .manutencao_chamado import ManutencaoChamado
from .manutencao_anexo import ManutencaoAnexo
from .manutencao_basedados import ManutencaoTipoServico, ManutencaoArea

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
    "ManutencaoChamado",
    "ManutencaoAnexo",
    "ManutencaoTipoServico",
    "ManutencaoArea",
]
