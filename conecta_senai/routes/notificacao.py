"""Rotas para notificacoes de agendamentos."""
from flask import Blueprint, request, jsonify
from conecta_senai.routes.user import verificar_autenticacao
from conecta_senai.services.notificacao_service import (
    listar_notificacoes as listar_notificacoes_service,
    marcar_notificacao_lida as marcar_notificacao_lida_service,
)


notificacao_bp = Blueprint('notificacao', __name__)

@notificacao_bp.route('/notificacoes', methods=['GET'])
def listar_notificacoes():
    """Retorna notificações ordenadas por data de criação.

    ---
    tags:
      - Notificações
    responses:
      200:
        description: Lista de notificações
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Notification'
      401:
        description: Não autenticado
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    return listar_notificacoes_service(user)

@notificacao_bp.route('/notificacoes/<int:id>/marcar-lida', methods=['PUT'])
def marcar_notificacao_lida(id):
    """Marca uma notificação como lida.

    ---
    tags:
      - Notificações
    parameters:
      - in: path
        name: id
        schema:
          type: integer
        required: true
        description: ID da notificação
    responses:
      200:
        description: Notificação marcada como lida
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Notification'
      401:
        description: Não autenticado
      404:
        description: Notificação não encontrada
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    return marcar_notificacao_lida_service(id, user)

