from datetime import datetime
import csv
from io import StringIO
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from flask import jsonify, make_response

from conecta_senai.models import db
from conecta_senai.models.rateio import RateioConfig, LancamentoRateio
from conecta_senai.models.instrutor import Instrutor
from conecta_senai.models.log_rateio import LogLancamentoRateio
from conecta_senai.repositories.log_rateio_repository import LogRateioRepository
from conecta_senai.schemas import RateioConfigCreateSchema, LancamentoRateioSchema
from conecta_senai.utils.error_handler import handle_internal_error


def registrar_log_rateio(user, acao, instrutor_nome, config, percentual, observacao=None):
    """Registra log das alterações de lançamentos de rateio."""
    try:
        log = LogLancamentoRateio(
            usuario=user.nome if user else 'Sistema',
            acao=acao,
            instrutor=instrutor_nome,
            filial=config.filial if config else None,
            uo=config.uo if config else None,
            cr=config.cr if config else None,
            classe_valor=config.classe_valor if config else None,
            percentual=percentual,
            observacao=observacao,
        )
        LogRateioRepository.add(log)
    except Exception:
        LogRateioRepository.rollback()


def listar_configs():
    configs = RateioConfig.query.order_by(RateioConfig.filial, RateioConfig.uo).all()
    return jsonify([c.to_dict() for c in configs])


def obter_config(id):
    config = db.session.get(RateioConfig, id)
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404
    return jsonify(config.to_dict())


def criar_config(data):
    try:
        payload = RateioConfigCreateSchema(**(data or {}))
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    try:
        nova_config = RateioConfig(**payload.model_dump())
        db.session.add(nova_config)
        db.session.commit()
        return jsonify(nova_config.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Esta configuração de rateio já existe.'}), 409
    except Exception as e:  # pragma: no cover - proteção extra
        db.session.rollback()
        return handle_internal_error(e)


def atualizar_config(id, data):
    config = db.session.get(RateioConfig, id)
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404

    try:
        config.filial = data.get('filial', config.filial)
        config.uo = data.get('uo', config.uo)
        config.cr = data.get('cr', config.cr)
        config.classe_valor = data.get('classe_valor', config.classe_valor)
        config.descricao = data.get('descricao', config.descricao)
        db.session.commit()
        return jsonify(config.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'erro': 'Já existe outra configuração com estes dados.'}), 409
    except Exception as e:
        db.session.rollback()
        return handle_internal_error(e)


def deletar_config(id):
    config = db.session.get(RateioConfig, id)
    if not config:
        return jsonify({'erro': 'Configuração não encontrada'}), 404

    if LancamentoRateio.query.filter_by(rateio_config_id=id).first():
        return jsonify({'erro': 'Configuração em uso, não pode ser excluída.'}), 400

    db.session.delete(config)
    db.session.commit()
    return jsonify({'mensagem': 'Configuração excluída com sucesso'})


def get_lancamentos(instrutor_id, ano, mes):
    if not all([instrutor_id, ano, mes]):
        return jsonify({'erro': 'Parâmetros instrutor_id, ano e mes são obrigatórios'}), 400

    lancamentos = LancamentoRateio.query.filter_by(
        instrutor_id=instrutor_id, ano=ano, mes=mes
    ).all()
    return jsonify([l.to_dict() for l in lancamentos])


def get_lancamentos_ano(instrutor_id, ano):
    if not instrutor_id or not ano:
        return jsonify({'erro': 'Parâmetros instrutor_id e ano são obrigatórios'}), 400

    lancamentos = LancamentoRateio.query.filter_by(instrutor_id=instrutor_id, ano=ano).all()
    agrupados = {}
    for l in lancamentos:
        agrupados.setdefault(l.mes, []).append(l.to_dict())
    resultado = {mes: agrupados.get(mes, []) for mes in range(1, 13)}
    return jsonify(resultado)


def salvar_lancamentos(data):
    try:
        payload = LancamentoRateioSchema(**(data or {}))
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    total_percentual = sum(item.percentual for item in payload.lancamentos)
    if total_percentual > 100:
        return jsonify({'erro': f'O percentual total ({total_percentual}%) não pode exceder 100%.'}), 400

    try:
        instrutor = db.session.get(Instrutor, payload.instrutor_id)
        existentes = LancamentoRateio.query.filter_by(
            instrutor_id=payload.instrutor_id, ano=payload.ano, mes=payload.mes
        ).all()
        mapa_existentes = {l.rateio_config_id: l for l in existentes}
        novos_ids = {item.rateio_config_id for item in payload.lancamentos if item.percentual > 0}

        for l in list(existentes):
            if l.rateio_config_id not in novos_ids:
                registrar_log_rateio(instrutor, 'delete', instrutor.nome if instrutor else '', l.rateio_config, l.percentual)
                db.session.delete(l)

        for item in payload.lancamentos:
            if item.percentual <= 0:
                continue
            existente = mapa_existentes.get(item.rateio_config_id)
            config = existente.rateio_config if existente else db.session.get(RateioConfig, item.rateio_config_id)
            if existente:
                if existente.percentual != item.percentual:
                    existente.percentual = item.percentual
                    registrar_log_rateio(instrutor, 'update', instrutor.nome if instrutor else '', config, item.percentual)
            else:
                novo = LancamentoRateio(
                    instrutor_id=payload.instrutor_id,
                    ano=payload.ano,
                    mes=payload.mes,
                    rateio_config_id=item.rateio_config_id,
                    percentual=item.percentual,
                )
                db.session.add(novo)
                registrar_log_rateio(instrutor, 'create', instrutor.nome if instrutor else '', config, item.percentual)

        db.session.commit()
        return jsonify({'mensagem': 'Lançamentos salvos com sucesso!'}), 201
    except Exception as e:  # pragma: no cover - segurança
        db.session.rollback()
        return handle_internal_error(e)


def listar_logs_rateio(usuario, instrutor, tipo, data_acao, page, per_page):
    try:
        paginacao = LogRateioRepository.list_logs(
            usuario, instrutor, tipo, data_acao, page, per_page
        )
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido'}), 400

    return jsonify(
        {
            'items': [
                {
                    'id': l.id,
                    'timestamp': l.timestamp.isoformat() if l.timestamp else None,
                    'acao': l.acao,
                    'usuario': l.usuario,
                    'instrutor': l.instrutor,
                    'filial': l.filial,
                    'uo': l.uo,
                    'cr': l.cr,
                    'classe_valor': l.classe_valor,
                    'percentual': l.percentual,
                    'observacao': l.observacao,
                }
                for l in paginacao.items
            ],
            'page': paginacao.page,
            'per_page': paginacao.per_page,
            'total': paginacao.total,
            'pages': paginacao.pages,
        }
    )


def exportar_logs_rateio():
    logs = LogRateioRepository.all_ordered()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Data/Hora', 'Ação', 'Usuário', 'Instrutor', 'Filial', 'UO', 'CR', 'Classe de Valor', 'Percentual', 'Observações'])
    for l in logs:
        writer.writerow([
            l.timestamp.isoformat() if l.timestamp else '',
            l.acao,
            l.usuario,
            l.instrutor,
            l.filial,
            l.uo,
            l.cr,
            l.classe_valor,
            l.percentual,
            l.observacao or '',
        ])
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=logs_rateio.csv'
    output.headers['Content-Type'] = 'text/csv'
    return output
