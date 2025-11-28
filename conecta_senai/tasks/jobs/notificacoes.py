"""Jobs relacionados a notificações."""

from flask import current_app
from conecta_senai.services.notificacao_service import criar_notificacoes_agendamentos_proximos


def _executar_lembretes():
    """Executa geração de lembretes dentro do contexto da aplicação."""
    app = current_app._get_current_object()
    with app.app_context():
        criar_notificacoes_agendamentos_proximos()
