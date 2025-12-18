from flask import Blueprint, request, jsonify
from conecta_senai.routes.user import verificar_autenticacao
from conecta_senai.services.notificacao_service import (
    listar_notificacoes as listar_notificacoes_service,
    marcar_notificacao_lida as marcar_notificacao_lida_service,
)


notificacao_bp = Blueprint("notificacao", __name__)


@notificacao_bp.route("/notificacoes", methods=["GET"])
def listar_notificacoes():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    return listar_notificacoes_service(user)


@notificacao_bp.route("/notificacoes/<int:id>/marcar-lida", methods=["PUT"])
def marcar_notificacao_lida(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    return marcar_notificacao_lida_service(id, user)
