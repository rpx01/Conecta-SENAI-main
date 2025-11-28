from flask import Blueprint, request
from conecta_senai.auth import admin_required
from conecta_senai.services.rateio_service import (
    listar_configs as listar_configs_service,
    obter_config as obter_config_service,
    criar_config as criar_config_service,
    atualizar_config as atualizar_config_service,
    deletar_config as deletar_config_service,
    get_lancamentos as get_lancamentos_service,
    get_lancamentos_ano as get_lancamentos_ano_service,
    salvar_lancamentos as salvar_lancamentos_service,
    listar_logs_rateio as listar_logs_rateio_service,
    exportar_logs_rateio as exportar_logs_rateio_service,
)

rateio_bp = Blueprint('rateio', __name__)


@rateio_bp.route('/rateio-configs', methods=['GET'])
@admin_required
def listar_configs():
    return listar_configs_service()


@rateio_bp.route('/rateio-configs/<int:id>', methods=['GET'])
@admin_required
def obter_config(id):
    return obter_config_service(id)


@rateio_bp.route('/rateio-configs', methods=['POST'])
@admin_required
def criar_config():
    return criar_config_service(request.json or {})


@rateio_bp.route('/rateio-configs/<int:id>', methods=['PUT'])
@admin_required
def atualizar_config(id):
    return atualizar_config_service(id, request.json or {})


@rateio_bp.route('/rateio-configs/<int:id>', methods=['DELETE'])
@admin_required
def deletar_config(id):
    return deletar_config_service(id)


@rateio_bp.route('/rateio/lancamentos', methods=['GET'])
@admin_required
def get_lancamentos():
    instrutor_id = request.args.get('instrutor_id', type=int)
    ano = request.args.get('ano', type=int)
    mes = request.args.get('mes', type=int)
    return get_lancamentos_service(instrutor_id, ano, mes)


@rateio_bp.route('/rateio/lancamentos-ano', methods=['GET'])
@admin_required
def get_lancamentos_ano():
    instrutor_id = request.args.get('instrutor_id', type=int)
    ano = request.args.get('ano', type=int)
    return get_lancamentos_ano_service(instrutor_id, ano)


@rateio_bp.route('/rateio/lancamentos', methods=['POST'])
@admin_required
def salvar_lancamentos():
    return salvar_lancamentos_service(request.json or {})


@rateio_bp.route('/logs-rateio', methods=['GET'])
@admin_required
def listar_logs_rateio():
    usuario = request.args.get('usuario')
    instrutor = request.args.get('instrutor')
    tipo = request.args.get('tipo')
    data_acao = request.args.get('data')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    return listar_logs_rateio_service(usuario, instrutor, tipo, data_acao, page, per_page)


@rateio_bp.route('/logs-rateio/export', methods=['GET'])
@admin_required
def exportar_logs_rateio():
    return exportar_logs_rateio_service()
