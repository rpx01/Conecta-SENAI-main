# flake8: noqa
from flask import jsonify, make_response, send_file
from datetime import datetime
import json
from io import StringIO, BytesIO
from sqlalchemy.exc import SQLAlchemyError

from conecta_senai.models import db
from conecta_senai.models.agendamento import Agendamento
from conecta_senai.models.laboratorio_turma import Laboratorio
from conecta_senai.models.user import User
from conecta_senai.utils.error_handler import handle_internal_error
from conecta_senai.utils.audit import log_action
from conecta_senai.models.log_agendamento import LogAgendamento
from conecta_senai.routes.user import verificar_admin


def registrar_log_agenda(user, acao, antes, depois):
    """Registra informações detalhadas dos agendamentos."""
    try:
        ref = depois or antes or {}
        log = LogAgendamento(
            usuario=user.nome if user else 'Sistema',
            tipo_acao=acao,
            laboratorio=ref.get('laboratorio'),
            turno=ref.get('turno'),
            data_agendamento=ref.get('data'),
            dados_antes=antes,
            dados_depois=depois,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:  # nosec B110
        db.session.rollback()


def listar_agendamentos(user):
    if verificar_admin(user):
        agendamentos = Agendamento.query.all()
    else:
        agendamentos = Agendamento.query.filter_by(usuario_id=user.id).all()
    return jsonify([a.to_dict() for a in agendamentos])


def obter_agendamento(id, user):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    if not verificar_admin(user) and agendamento.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    return jsonify(agendamento.to_dict())


def obter_agendamento_detalhes(id, user):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    dados = agendamento.to_dict()
    dados['usuario_nome'] = agendamento.usuario.nome if agendamento.usuario else None
    return jsonify(dados)


def verificar_conflitos_horarios(data, laboratorio, horarios_list, agendamento_id=None):
    query = Agendamento.query.filter(
        Agendamento.data == data,
        Agendamento.laboratorio == laboratorio,
    )
    if agendamento_id:
        query = query.filter(Agendamento.id != agendamento_id)
    agendamentos_existentes = query.all()
    if not agendamentos_existentes:
        return []
    try:
        horarios_novos = set(horarios_list)
    except (TypeError, ValueError):
        return ['Formato de horários inválido']
    conflitos = []
    for agendamento in agendamentos_existentes:
        try:
            horarios_existentes = set(agendamento.horarios)
            intersecao = horarios_novos.intersection(horarios_existentes)
            if intersecao:
                conflitos.append({
                    'agendamento_id': agendamento.id,
                    'data': agendamento.data.isoformat(),
                    'laboratorio': agendamento.laboratorio,
                    'turma': agendamento.turma,
                    'horarios_conflitantes': list(intersecao),
                })
        except Exception:  # nosec B110
            pass
    return conflitos


def criar_agendamento(data, user):
    campos_obrigatorios = ['data', 'laboratorio', 'turma', 'turno', 'horarios']
    if not all(campo in data for campo in campos_obrigatorios):
        return jsonify({'erro': 'Dados incompletos'}), 400
    try:
        data_agendamento = datetime.strptime(data['data'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    try:
        horarios = json.loads(data['horarios']) if isinstance(data['horarios'], str) else data['horarios']
    except json.JSONDecodeError:
        return jsonify({'erro': 'Formato de horários inválido'}), 400
    usuario_id = data.get('usuario_id', user.id)
    if usuario_id != user.id:
        usuario_destino = db.session.get(User, usuario_id)
        if not usuario_destino:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
    conflitos = verificar_conflitos_horarios(
        data_agendamento,
        data['laboratorio'],
        horarios,
        None,
    )
    if conflitos:
        return jsonify({'erro': 'Conflito de horários', 'conflitos': conflitos}), 409
    try:
        novo_agendamento = Agendamento(
            data=data_agendamento,
            laboratorio=data['laboratorio'],
            turma=data['turma'],
            turno=data['turno'],
            horarios=horarios,
            usuario_id=usuario_id,
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        log_action(user.id, 'create', 'Agendamento', novo_agendamento.id, novo_agendamento.to_dict())
        registrar_log_agenda(user, 'create', None, novo_agendamento.to_dict())
        return jsonify(novo_agendamento.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


def atualizar_agendamento(id, data, user):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    if not verificar_admin(user) and agendamento.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    estado_anterior = agendamento.to_dict()
    data_agendamento = agendamento.data
    if 'data' in data:
        try:
            data_agendamento = datetime.strptime(data['data'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    horarios_lista = agendamento.horarios
    if 'horarios' in data:
        try:
            horarios = json.loads(data['horarios']) if isinstance(data['horarios'], str) else data['horarios']
            horarios_lista = horarios
        except json.JSONDecodeError:
            return jsonify({'erro': 'Formato de horários inválido'}), 400
    laboratorio = data.get('laboratorio', agendamento.laboratorio)
    conflitos = verificar_conflitos_horarios(
        data_agendamento,
        laboratorio,
        horarios_lista,
        id,
    )
    if conflitos:
        return jsonify({'erro': 'Conflito de horários', 'conflitos': conflitos}), 409
    if 'data' in data:
        agendamento.data = data_agendamento
    if 'laboratorio' in data:
        agendamento.laboratorio = data['laboratorio']
    if 'turma' in data:
        agendamento.turma = data['turma']
    if 'turno' in data:
        agendamento.turno = data['turno']
    if 'horarios' in data:
        agendamento.horarios = horarios_lista
    if 'usuario_id' in data and verificar_admin(user):
        usuario_destino = db.session.get(User, data['usuario_id'])
        if not usuario_destino:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        agendamento.usuario_id = data['usuario_id']
    try:
        db.session.commit()
        dados_depois = agendamento.to_dict()
        log_action(user.id, 'update', 'Agendamento', agendamento.id, dados_depois)
        registrar_log_agenda(user, 'update', estado_anterior, dados_depois)
        return jsonify(dados_depois)
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


def remover_agendamento(id, user):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    if not verificar_admin(user) and agendamento.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    estado_anterior = agendamento.to_dict()
    try:
        db.session.delete(agendamento)
        db.session.commit()
        log_action(user.id, 'delete', 'Agendamento', agendamento.id, estado_anterior)
        registrar_log_agenda(user, 'delete', estado_anterior, None)
        return jsonify({'mensagem': 'Agendamento removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)
