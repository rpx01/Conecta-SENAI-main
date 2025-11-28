"""Rotas para gerenciamento de ocupacoes de salas."""
from flask import Blueprint, request, jsonify, make_response, send_file
from conecta_senai.models import db
from conecta_senai.models.ocupacao import Ocupacao
from conecta_senai.models.sala import Sala
from conecta_senai.models.instrutor import Instrutor
from conecta_senai.routes.user import verificar_autenticacao, verificar_admin
from conecta_senai.auth import admin_required
from sqlalchemy.exc import SQLAlchemyError
from conecta_senai.utils.error_handler import handle_internal_error
from conecta_senai.utils.audit import log_action
from datetime import datetime, date, time, timedelta
from pydantic import ValidationError
from conecta_senai.schemas import OcupacaoCreateSchema, OcupacaoUpdateSchema
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import and_, or_, func, extract, desc, cast, String

ocupacao_bp = Blueprint('ocupacao', __name__)

# Desabilita cache para todas as respostas deste blueprint para evitar que o
# navegador utilize dados antigos ao atualizar ou excluir ocupações.
@ocupacao_bp.after_request
def add_no_cache_headers(response):
    """Adiciona cabeçalhos para desativar cache."""
    response.headers['Cache-Control'] = 'no-store'
    return response

TURNOS_PADRAO = {
    'Manhã': (time.fromisoformat('08:00'), time.fromisoformat('12:00')),
    'Tarde': (time.fromisoformat('13:30'), time.fromisoformat('17:30')),
    'Noite': (time.fromisoformat('18:30'), time.fromisoformat('22:30'))
}


def obter_ocupacoes_por_identificador(identificador):
    """Retorna a lista de ocupações associadas ao identificador fornecido.

    O identificador pode ser o ID numérico de uma ocupação específica ou um
    ``grupo_ocupacao_id``. Para registros antigos que não possuem
    ``grupo_ocupacao_id``, o ID numérico continua sendo aceito.
    """

    if not identificador:
        return None, None, None

    ocupacoes = []
    grupo_id = None
    ocupacao_base = None

    if identificador.isdigit():
        ocupacao_base = db.session.get(Ocupacao, int(identificador))
        if not ocupacao_base:
            return None, None, None
        if ocupacao_base.grupo_ocupacao_id:
            grupo_id = ocupacao_base.grupo_ocupacao_id
            ocupacoes = (
                Ocupacao.query
                .filter_by(grupo_ocupacao_id=grupo_id)
                .order_by(Ocupacao.data.asc())
                .all()
            )
        else:
            ocupacoes = [ocupacao_base]
    else:
        grupo_id = identificador
        ocupacoes = (
            Ocupacao.query
            .filter_by(grupo_ocupacao_id=grupo_id)
            .order_by(Ocupacao.data.asc())
            .all()
        )
        if not ocupacoes:
            return None, None, None
        ocupacao_base = ocupacoes[0]

    if ocupacao_base is None and ocupacoes:
        ocupacao_base = ocupacoes[0]

    return ocupacoes, grupo_id, ocupacao_base


def obter_turno_por_horarios(horario_inicio, horario_fim):
    """Retorna o nome do turno a partir dos horários padrão configurados."""

    if not horario_inicio or not horario_fim:
        return None

    for turno_nome, (inicio, fim) in TURNOS_PADRAO.items():
        if inicio == horario_inicio and fim == horario_fim:
            return turno_nome
    return None

@ocupacao_bp.route('/ocupacoes', methods=['GET'])
def listar_ocupacoes():
    """Lista ocupações agrupadas por reserva (grupo_ocupacao_id)."""

    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    sala_id = request.args.get('sala_id', type=int)
    status = request.args.get('status')
    tipo_ocupacao = request.args.get('tipo_ocupacao')
    curso_evento = request.args.get('curso_evento')

    data_inicio = None
    data_fim = None

    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data_inicio inválido (YYYY-MM-DD)'}), 400

    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data_fim inválido (YYYY-MM-DD)'}), 400

    ocupacoes_query = Ocupacao.query

    if sala_id:
        ocupacoes_query = ocupacoes_query.filter(Ocupacao.sala_id == sala_id)

    if status:
        ocupacoes_query = ocupacoes_query.filter(Ocupacao.status == status)

    if tipo_ocupacao:
        ocupacoes_query = ocupacoes_query.filter(Ocupacao.tipo_ocupacao == tipo_ocupacao)

    if curso_evento:
        ocupacoes_query = ocupacoes_query.filter(Ocupacao.curso_evento.ilike(f'%{curso_evento}%'))

    grupo_expr = func.coalesce(Ocupacao.grupo_ocupacao_id, cast(Ocupacao.id, String))

    agrupamento = (
        ocupacoes_query
        .with_entities(
            grupo_expr.label('grupo_id'),
            func.min(Ocupacao.id).label('primeira_ocupacao_id'),
            Ocupacao.sala_id.label('sala_id'),
            func.min(Ocupacao.curso_evento).label('curso_evento'),
            func.min(Ocupacao.tipo_ocupacao).label('tipo_ocupacao'),
            func.min(Ocupacao.recorrencia).label('recorrencia'),
            func.min(Ocupacao.status).label('status'),
            func.min(Ocupacao.observacoes).label('observacoes'),
            func.min(Ocupacao.horario_inicio).label('horario_inicio'),
            func.min(Ocupacao.horario_fim).label('horario_fim'),
            func.min(Ocupacao.usuario_id).label('usuario_id'),
            func.min(Ocupacao.grupo_ocupacao_id).label('grupo_ocupacao_id'),
            func.count(Ocupacao.id).label('quantidade_dias'),
            func.min(Ocupacao.data).label('data_inicio'),
            func.max(Ocupacao.data).label('data_fim')
        )
        .group_by(grupo_expr, Ocupacao.sala_id)
    )

    subquery = agrupamento.subquery()

    query = (
        db.session.query(
            subquery.c.grupo_id,
            subquery.c.primeira_ocupacao_id,
            subquery.c.sala_id,
            subquery.c.curso_evento,
            subquery.c.tipo_ocupacao,
            subquery.c.recorrencia,
            subquery.c.status,
            subquery.c.observacoes,
            subquery.c.horario_inicio,
            subquery.c.horario_fim,
            subquery.c.usuario_id,
            subquery.c.grupo_ocupacao_id,
            subquery.c.quantidade_dias,
            subquery.c.data_inicio,
            subquery.c.data_fim,
            Sala.nome.label('sala_nome')
        )
        .join(Sala, Sala.id == subquery.c.sala_id, isouter=True)
    )

    if data_inicio:
        query = query.filter(subquery.c.data_fim >= data_inicio)

    if data_fim:
        query = query.filter(subquery.c.data_inicio <= data_fim)

    resultados = query.order_by(subquery.c.data_inicio, subquery.c.horario_inicio).all()

    ocupacoes_agrupadas = []
    for item in resultados:
        turno_nome = obter_turno_por_horarios(item.horario_inicio, item.horario_fim)
        identificador = item.grupo_ocupacao_id or item.grupo_id
        ocupacoes_agrupadas.append({
            'id': identificador,
            'grupo_ocupacao_id': item.grupo_ocupacao_id,
            'primeira_ocupacao_id': item.primeira_ocupacao_id,
            'sala_id': item.sala_id,
            'sala_nome': item.sala_nome,
            'curso_evento': item.curso_evento,
            'tipo_ocupacao': item.tipo_ocupacao,
            'recorrencia': item.recorrencia,
            'status': item.status,
            'observacoes': item.observacoes,
            'horario_inicio': item.horario_inicio.strftime('%H:%M') if item.horario_inicio else None,
            'horario_fim': item.horario_fim.strftime('%H:%M') if item.horario_fim else None,
            'turno': turno_nome,
            'data_inicio': item.data_inicio.isoformat() if item.data_inicio else None,
            'data_fim': item.data_fim.isoformat() if item.data_fim else None,
            'quantidade_dias': item.quantidade_dias,
        })

    return jsonify(ocupacoes_agrupadas), 200


@ocupacao_bp.route('/ocupacoes/export', methods=['GET'])
def exportar_ocupacoes():
    """Exporta ocupações em CSV, PDF ou XLSX."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    formato = request.args.get('formato', 'csv').lower()

    ocupacoes = Ocupacao.query.all()

    if formato == 'pdf':
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(50, 750, "Relatório de Ocupações")
        y = 730
        c.drawString(50, y, "ID  Sala  Data  Início  Fim  Status")
        y -= 20
        for oc in ocupacoes:
            sala = oc.sala.nome if oc.sala else oc.sala_id
            c.drawString(50, y, f"{oc.id}  {sala}  {oc.data}  {oc.horario_inicio}  {oc.horario_fim}  {oc.status}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='ocupacoes.pdf')

    if formato == 'xlsx':
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Sala", "Data", "Início", "Fim", "Status"])
        for oc in ocupacoes:
            sala = oc.sala.nome if oc.sala else oc.sala_id
            ws.append([oc.id, sala, oc.data, oc.horario_inicio, oc.horario_fim, oc.status])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='ocupacoes.xlsx'
        )

    # CSV padrão
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Sala", "Data", "Início", "Fim", "Status"])
    for oc in ocupacoes:
        sala = oc.sala.nome if oc.sala else oc.sala_id
        writer.writerow([oc.id, sala, oc.data, oc.horario_inicio, oc.horario_fim, oc.status])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=ocupacoes.csv"
    output.headers["Content-Type"] = "text/csv"
    return output

@ocupacao_bp.route('/ocupacoes/<string:identificador>', methods=['GET'])
def obter_ocupacao(identificador):
    """Obtém detalhes consolidados de uma ocupação (individual ou agrupada)."""

    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    ocupacoes_grupo, grupo_id, ocupacao_base = obter_ocupacoes_por_identificador(identificador)

    if not ocupacao_base:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404

    if not ocupacoes_grupo:
        ocupacoes_grupo = [ocupacao_base]

    datas = [oc.data for oc in ocupacoes_grupo]
    data_inicio = min(datas)
    data_fim = max(datas)
    horario_inicio = ocupacao_base.horario_inicio
    horario_fim = ocupacao_base.horario_fim

    turno_nome = obter_turno_por_horarios(horario_inicio, horario_fim)

    dados = {
        'id': grupo_id or str(ocupacao_base.id),
        'grupo_ocupacao_id': grupo_id,
        'sala_id': ocupacao_base.sala_id,
        'sala_nome': ocupacao_base.sala.nome if ocupacao_base.sala else None,
        'curso_evento': ocupacao_base.curso_evento,
        'tipo_ocupacao': ocupacao_base.tipo_ocupacao,
        'recorrencia': ocupacao_base.recorrencia,
        'status': ocupacao_base.status,
        'observacoes': ocupacao_base.observacoes,
        'usuario_id': ocupacao_base.usuario_id,
        'horario_inicio': horario_inicio.strftime('%H:%M') if horario_inicio else None,
        'horario_fim': horario_fim.strftime('%H:%M') if horario_fim else None,
        'turno': turno_nome,
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat(),
        'datas': [data.isoformat() for data in datas],
        'quantidade_dias': len(ocupacoes_grupo),
    }

    return jsonify(dados), 200

@ocupacao_bp.route('/ocupacoes', methods=['POST'])
@admin_required
def criar_ocupacao():
    """
    Cria uma nova ocupação.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    data = request.json or {}
    try:
        payload = OcupacaoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    sala = db.session.get(Sala, payload.sala_id)
    if not sala:
        return jsonify({'erro': 'Sala não encontrada'}), 404

    try:
        data_inicio = datetime.strptime(payload.data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(payload.data_fim, '%Y-%m-%d').date()

        if data_inicio > data_fim:
            return jsonify({'erro': 'Data de início deve ser anterior ou igual à data de fim'}), 400


        if payload.turno not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400

        horario_inicio, horario_fim = TURNOS_PADRAO[payload.turno]

        conflitos_totais = []
        dia = data_inicio
        while dia <= data_fim:
            if not sala.is_disponivel(dia, horario_inicio, horario_fim):
                conflitos = Ocupacao.buscar_conflitos(payload.sala_id, dia, horario_inicio, horario_fim)
                conflitos_totais.extend(conflitos)
            dia += timedelta(days=1)

        if conflitos_totais:
            return jsonify({
                'erro': 'Sala não disponível no turno solicitado',
                'conflitos': [c.to_dict(include_relations=False) for c in conflitos_totais]
            }), 409
        
        # Validação de tipo de ocupação
        tipos_validos = ['aula_regular', 'evento_especial', 'reuniao', 'manutencao', 'reserva_especial']
        tipo_ocupacao = payload.tipo_ocupacao or 'aula_regular'
        if tipo_ocupacao not in tipos_validos:
            return jsonify({'erro': f'Tipo de ocupação deve ser um dos seguintes: {", ".join(tipos_validos)}'}), 400

        # Validação de recorrência
        recorrencias_validas = ['unica', 'semanal', 'mensal']
        recorrencia = payload.recorrencia or 'unica'
        if recorrencia not in recorrencias_validas:
            return jsonify({'erro': f'Recorrência deve ser uma das seguintes: {", ".join(recorrencias_validas)}'}), 400
        
        import uuid
        grupo_id = uuid.uuid4().hex

        ocupacoes_criadas = []
        dia = data_inicio
        while dia <= data_fim:
            # Se o tipo de ocupação for 'aula_regular' e o dia for sábado ou domingo, ignora
            if payload.tipo_ocupacao == 'aula_regular' and dia.weekday() >= 5:
                dia += timedelta(days=1)
                continue
            nova_ocupacao = Ocupacao(
                sala_id=payload.sala_id,
                usuario_id=user.id,
                curso_evento=payload.curso_evento,
                data=dia,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
                tipo_ocupacao=tipo_ocupacao,
                recorrencia=recorrencia,
                status=payload.status or 'confirmado',
                observacoes=payload.observacoes,
                grupo_ocupacao_id=grupo_id
            )
            db.session.add(nova_ocupacao)
            ocupacoes_criadas.append(nova_ocupacao)
            dia += timedelta(days=1)

        db.session.commit()
        for oc in ocupacoes_criadas:
            log_action(user.id, 'create', 'Ocupacao', oc.id, oc.to_dict())

        return jsonify([o.to_dict() for o in ocupacoes_criadas]), 201
        
    except ValueError:
        return jsonify({'erro': 'Formato de data ou horário inválido'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/<string:identificador>', methods=['PUT'])
@admin_required
def atualizar_ocupacao(identificador):
    """
    Atualiza uma ocupação existente. Para garantir a consistência de agendamentos
    de múltiplos dias, esta função adota a estratégia de "apagar e recriar".
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    ocupacoes_grupo, grupo_existente, ocupacao_original = obter_ocupacoes_por_identificador(identificador)

    if not ocupacao_original:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404

    # 2. Verifica as permissões do usuário.
    if not ocupacao_original.pode_ser_editada_por(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    # 3. Valida os novos dados recebidos do formulário.
    data = request.json or {}
    try:
        payload = OcupacaoUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    if not ocupacoes_grupo:
        ocupacoes_grupo = [ocupacao_original]

    # 4. Determina o grupo final. Para reservas sem grupo prévio, gera um novo ID.
    grupo_id_existente = grupo_existente
    if not grupo_id_existente:
        grupo_id_existente = ocupacao_original.grupo_ocupacao_id

    grupo_id_final = grupo_id_existente
    if not grupo_id_final:
        import uuid
        grupo_id_final = uuid.uuid4().hex

    # ----- Início da Transação Atómica -----
    try:
        sala_id = payload.sala_id if payload.sala_id is not None else ocupacao_original.sala_id
        sala = db.session.get(Sala, sala_id)
        if not sala:
            raise ValueError('Sala não encontrada.')

        if payload.data_inicio:
            data_inicio = datetime.strptime(payload.data_inicio, '%Y-%m-%d').date()
        else:
            data_inicio = min(oc.data for oc in ocupacoes_grupo)

        if payload.data_fim:
            data_fim = datetime.strptime(payload.data_fim, '%Y-%m-%d').date()
        else:
            data_fim = max(oc.data for oc in ocupacoes_grupo)

        turno = payload.turno if payload.turno is not None else ocupacao_original.get_turno()

        if data_inicio > data_fim:
            raise ValueError("Data de início não pode ser posterior à data de fim.")

        if turno not in TURNOS_PADRAO:
            raise ValueError("Turno inválido.")
        horario_inicio, horario_fim = TURNOS_PADRAO[turno]

        tipo_ocupacao = payload.tipo_ocupacao if payload.tipo_ocupacao is not None else ocupacao_original.tipo_ocupacao
        recorrencia = payload.recorrencia if payload.recorrencia is not None else ocupacao_original.recorrencia
        status_atual = payload.status if payload.status is not None else ocupacao_original.status
        observacoes = payload.observacoes if payload.observacoes is not None else ocupacao_original.observacoes
        curso_evento = payload.curso_evento if payload.curso_evento is not None else ocupacao_original.curso_evento

        ignorar_ocupacao_id = None if grupo_id_existente else ocupacao_original.id

        conflitos_totais = []
        dia_atual = data_inicio
        while dia_atual <= data_fim:
            if not sala.is_disponivel(dia_atual, horario_inicio, horario_fim, ignorar_ocupacao_id, grupo_id_existente):
                conflitos = Ocupacao.buscar_conflitos(
                    sala_id,
                    dia_atual,
                    horario_inicio,
                    horario_fim,
                    ignorar_ocupacao_id,
                    grupo_id_existente
                )
                conflitos_totais.extend(conflitos)
            dia_atual += timedelta(days=1)

        if conflitos_totais:
            raise ValueError('Conflito de horário detectado. A sala já está ocupada neste período.')

        # 5. Apaga as ocupações antigas do grupo (ou a ocupação única).
        ocupacoes_anteriores = ocupacoes_grupo if grupo_id_existente else [ocupacao_original]
        dados_anteriores = [oc.to_dict() for oc in ocupacoes_anteriores]
        for oc in ocupacoes_anteriores:
            db.session.delete(oc)

        # 6. Recria as novas ocupações com os dados atualizados.
        ocupacoes_criadas = []
        dia_atual = data_inicio
        while dia_atual <= data_fim:
            # Se o tipo de ocupação for 'aula_regular' e o dia for sábado ou domingo, ignora
            if payload.tipo_ocupacao == 'aula_regular' and dia_atual.weekday() >= 5:
                dia_atual += timedelta(days=1)
                continue
            nova_ocupacao = Ocupacao(
                sala_id=sala_id,
                usuario_id=user.id,
                curso_evento=curso_evento,
                data=dia_atual,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
                tipo_ocupacao=tipo_ocupacao,
                recorrencia=recorrencia,
                status=status_atual,
                observacoes=observacoes,
                grupo_ocupacao_id=grupo_id_final
            )
            db.session.add(nova_ocupacao)
            ocupacoes_criadas.append(nova_ocupacao)
            dia_atual += timedelta(days=1)

        # 9. Comita a transação.
        db.session.commit()

        for antigo in dados_anteriores:
            log_action(user.id, 'delete', 'Ocupacao', antigo['id'], antigo)

        for oc in ocupacoes_criadas:
            log_action(user.id, 'update', 'Ocupacao', oc.id, oc.to_dict())

        return jsonify({
            'mensagem': 'Ocupação atualizada com sucesso!',
            'ocupacoes': [o.to_dict() for o in ocupacoes_criadas]
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        # 10. Se qualquer passo falhar, desfaz tudo (rollback).
        db.session.rollback()
        return jsonify({'erro': f'Falha ao atualizar a ocupação: {str(e)}'}), 500
@ocupacao_bp.route('/ocupacoes/<string:identificador>', methods=['DELETE'])
@admin_required
def remover_ocupacao(identificador):
    """
    Remove uma ocupação.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    ocupacoes_grupo, grupo_id, ocupacao = obter_ocupacoes_por_identificador(identificador)

    if not ocupacao:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404

    # Verifica permissões
    if not ocupacao.pode_ser_editada_por(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    try:
        somente_dia = request.args.get('somente_dia', default=False, type=lambda v: str(v).lower() == 'true')
        if not ocupacoes_grupo:
            ocupacoes_grupo = [ocupacao]

        if somente_dia or not grupo_id:
            ocupacoes = [ocupacao]
        else:
            ocupacoes = ocupacoes_grupo

        quantidade = len(ocupacoes)
        dados = [oc.to_dict() for oc in ocupacoes]
        for oc in ocupacoes:
            db.session.delete(oc)

        db.session.commit()
        for info in dados:
            log_action(user.id, 'delete', 'Ocupacao', info['id'], info)
        return jsonify({'mensagem': 'Ocupação removida com sucesso', 'removidas': quantidade})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/<string:identificador>/instrutor', methods=['PATCH'])
@admin_required
def atualizar_instrutor_ocupacao(identificador):
    """
    Atualiza o instrutor associado a uma ocupação ou grupo de ocupações.
    Este endpoint permite atribuir ou remover um instrutor de forma leve,
    sem necessidade de recriar as ocupações.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    ocupacoes_grupo, grupo_id, ocupacao_base = obter_ocupacoes_por_identificador(identificador)

    if not ocupacao_base:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404

    # Verifica permissões
    if not ocupacao_base.pode_ser_editada_por(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    data = request.json or {}
    instrutor_id = data.get('instrutor_id')

    # Valida instrutor se fornecido
    if instrutor_id is not None and instrutor_id != '':
        instrutor = db.session.get(Instrutor, instrutor_id)
        if not instrutor:
            return jsonify({'erro': 'Instrutor não encontrado'}), 404
        if instrutor.status != 'ativo':
            return jsonify({'erro': 'Instrutor não está ativo'}), 400
    else:
        instrutor_id = None

    try:
        # Determina quais ocupações atualizar
        if not ocupacoes_grupo:
            ocupacoes_grupo = [ocupacao_base]

        # Atualiza todas as ocupações do grupo
        for ocupacao in ocupacoes_grupo:
            ocupacao.instrutor_id = instrutor_id

        db.session.commit()

        # Log de auditoria
        for oc in ocupacoes_grupo:
            log_action(user.id, 'update', 'Ocupacao', oc.id, {
                'campo': 'instrutor_id',
                'valor_anterior': ocupacao_base.instrutor_id,
                'valor_novo': instrutor_id
            })

        return jsonify({
            'mensagem': 'Instrutor atualizado com sucesso',
            'ocupacoes_atualizadas': len(ocupacoes_grupo),
            'instrutor_id': instrutor_id
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/verificar-disponibilidade', methods=['GET'])
def verificar_disponibilidade():
    """
    Verifica a disponibilidade de uma sala em uma data e horário específicos.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Parâmetros obrigatórios
    sala_id = request.args.get('sala_id', type=int)
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    turno = request.args.get('turno')
    ocupacao_identificador = request.args.get('ocupacao_id')  # Para edição
    grupo_ocupacao_id = None
    ocupacao_id = None
    if ocupacao_identificador:
        ocupacoes_grupo, grupo_id_existente, ocupacao_base = obter_ocupacoes_por_identificador(ocupacao_identificador)
        if ocupacao_base:
            if grupo_id_existente:
                grupo_ocupacao_id = grupo_id_existente
            else:
                ocupacao_id = ocupacao_base.id

    if not all([sala_id, data_inicio_str, data_fim_str, turno]):
        return jsonify({'erro': 'Parâmetros obrigatórios: sala_id, data_inicio, data_fim, turno'}), 400
    
    # Verifica se a sala existe
    sala = db.session.get(Sala, sala_id)
    if not sala:
        return jsonify({'erro': 'Sala não encontrada'}), 404
    
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()

        if data_inicio > data_fim:
            return jsonify({'erro': 'Data de início deve ser anterior ou igual à data de fim'}), 400

        if turno not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400

        horario_inicio, horario_fim = TURNOS_PADRAO[turno]

        disponivel = True
        conflitos = []
        dia = data_inicio
        while dia <= data_fim:
            if not sala.is_disponivel(dia, horario_inicio, horario_fim, ocupacao_id, grupo_ocupacao_id):
                disponivel = False
                conflitos.extend(Ocupacao.buscar_conflitos(sala_id, dia, horario_inicio, horario_fim, ocupacao_id, grupo_ocupacao_id))
            dia += timedelta(days=1)
        
        return jsonify({
            'disponivel': disponivel,
            'sala': sala.to_dict(),
            'conflitos': conflitos
        })
        
    except ValueError:
        return jsonify({'erro': 'Formato de data ou horário inválido'}), 400
    except SQLAlchemyError as e:
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/calendario', methods=['GET'])
def obter_ocupacoes_calendario():
    """
    Obtém ocupações formatadas para exibição em calendário.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Parâmetros de filtro
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    sala_id = request.args.get('sala_id', type=int)
    instrutor_id = request.args.get('instrutor_id', type=int)
    turno = request.args.get('turno')

    # Define período padrão (mês atual) se não fornecido
    if not data_inicio_str or not data_fim_str:
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            ultimo_dia = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        data_inicio = primeiro_dia
        data_fim = ultimo_dia
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido (YYYY-MM-DD)'}), 400
    
    # Query base
    query = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    )
    
    # Aplica filtro de sala se fornecido
    if sala_id:
        query = query.filter(Ocupacao.sala_id == sala_id)

    # Aplica filtro de instrutor se fornecido
    if instrutor_id:
        query = query.filter(Ocupacao.instrutor_id == instrutor_id)

    # Aplica filtro de turno se fornecido
    if turno:
        if turno not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400
        inicio, fim = TURNOS_PADRAO[turno]
        query = query.filter(
            Ocupacao.horario_inicio == inicio,
            Ocupacao.horario_fim == fim
        )
    
    
    ocupacoes = query.order_by(Ocupacao.data, Ocupacao.horario_inicio).all()
    
    # Formata para o calendário
    def cor_turno(t):
        """Retorna a cor associada ao turno."""
        cores = {
            'Manhã': '#FDD835',
            'Tarde': '#00539F',
            'Noite': '#512DA8'
        }
        return cores.get(t, '#888888')

    eventos_calendario = []
    for ocupacao in ocupacoes:
        turno_evento = ocupacao.get_turno()
        cor = cor_turno(turno_evento)
        evento = {
            'id': ocupacao.id,
            # Exibe apenas o turno no calendário mensal para evitar poluição visual
            'title': turno_evento,
            'start': f"{ocupacao.data}T{ocupacao.horario_inicio}",
            'end': f"{ocupacao.data}T{ocupacao.horario_fim}",
            'backgroundColor': cor,
            'borderColor': cor,
            'extendedProps': ocupacao.to_dict()
        }
        eventos_calendario.append(evento)

    return jsonify(eventos_calendario)


@ocupacao_bp.route('/ocupacoes/resumo-periodo', methods=['GET'])
def obter_resumo_periodo():
    """Retorna resumo de salas ocupadas e livres por dia e turno."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    sala_id = request.args.get('sala_id', type=int)
    instrutor_id = request.args.get('instrutor_id', type=int)
    turno_filtro = request.args.get('turno')

    if not data_inicio_str or not data_fim_str:
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            ultimo_dia = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

        data_inicio = primeiro_dia
        data_fim = ultimo_dia
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido (YYYY-MM-DD)'}), 400

    salas_ativas = Sala.query.filter_by(status='ativa').all()
    total_salas = len(salas_ativas)
    salas_dict = {s.id: s.nome for s in salas_ativas}

    query = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    )

    if sala_id:
        query = query.filter(Ocupacao.sala_id == sala_id)

    if instrutor_id:
        query = query.filter(Ocupacao.instrutor_id == instrutor_id)

    if turno_filtro:
        if turno_filtro not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400
        inicio, fim = TURNOS_PADRAO[turno_filtro]
        query = query.filter(
            Ocupacao.horario_inicio == inicio,
            Ocupacao.horario_fim == fim
        )


    ocupacoes = query.all()

    resumo = {}
    dia = data_inicio
    while dia <= data_fim:
        resumo[dia.isoformat()] = {
            turno: {
                'ocupadas': 0,
                'salas_ocupadas': [],
                'salas_livres': [],
                'total_salas': total_salas
            } for turno in TURNOS_PADRAO
        }
        dia += timedelta(days=1)

    for oc in ocupacoes:
        turno = oc.get_turno()
        if not turno:
            continue
        info = resumo[oc.data.isoformat()][turno]
        info['ocupadas'] += 1
        info['salas_ocupadas'].append({
            'sala_id': oc.sala_id,
            'sala_nome': salas_dict.get(oc.sala_id, str(oc.sala_id)),
            'curso_evento': oc.curso_evento,
            'instrutor_nome': oc.instrutor.nome if oc.instrutor else None
        })

    for dia_key, turnos in resumo.items():
        for turno, info in turnos.items():
            ocupadas_ids = [s['sala_id'] for s in info['salas_ocupadas']]
            info['salas_livres'] = [nome for sid, nome in salas_dict.items() if sid not in ocupadas_ids]
            info['livres'] = info['total_salas'] - info['ocupadas']

    return jsonify(resumo)

@ocupacao_bp.route('/ocupacoes/tipos', methods=['GET'])
def listar_tipos_ocupacao():
    """
    Lista os tipos de ocupação disponíveis.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    tipos = [
        {'valor': 'aula_regular', 'nome': 'Aula Regular', 'cor': '#006837'},
        {'valor': 'evento_especial', 'nome': 'Evento Especial', 'cor': '#FFB612'},
        {'valor': 'reuniao', 'nome': 'Reunião', 'cor': '#00539F'},
        {'valor': 'manutencao', 'nome': 'Manutenção', 'cor': '#D50032'},
        {'valor': 'reserva_especial', 'nome': 'Reserva Especial', 'cor': '#9C27B0'}
    ]
    
    return jsonify(tipos)

@ocupacao_bp.route('/ocupacoes/relatorio', methods=['GET'])
def gerar_relatorio_ocupacoes():
    """
    Gera relatório de ocupações com estatísticas.
    Apenas administradores podem acessar.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    # Parâmetros de filtro
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    
    # Define período padrão (mês atual) se não fornecido
    if not data_inicio_str or not data_fim_str:
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            ultimo_dia = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        data_inicio = primeiro_dia
        data_fim = ultimo_dia
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido (YYYY-MM-DD)'}), 400
    
    # Estatísticas gerais
    total_ocupacoes = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim
    ).count()
    
    ocupacoes_confirmadas = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status == 'confirmado'
    ).count()
    
    ocupacoes_pendentes = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status == 'pendente'
    ).count()
    
    ocupacoes_canceladas = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status == 'cancelado'
    ).count()
    
    # Estatísticas por sala
    salas_mais_utilizadas = db.session.query(
        Sala.nome,
        db.func.count(Ocupacao.id).label('total_ocupacoes')
    ).join(Ocupacao).filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    ).group_by(Sala.id, Sala.nome).order_by(db.desc('total_ocupacoes')).limit(10).all()
    
    # Estatísticas por tipo de ocupação
    ocupacoes_por_tipo = db.session.query(
        Ocupacao.tipo_ocupacao,
        db.func.count(Ocupacao.id).label('total')
    ).filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    ).group_by(Ocupacao.tipo_ocupacao).all()
    
    relatorio = {
        'periodo': {
            'data_inicio': data_inicio.isoformat(),
            'data_fim': data_fim.isoformat()
        },
        'estatisticas_gerais': {
            'total_ocupacoes': total_ocupacoes,
            'ocupacoes_confirmadas': ocupacoes_confirmadas,
            'ocupacoes_pendentes': ocupacoes_pendentes,
            'ocupacoes_canceladas': ocupacoes_canceladas
        },
        'salas_mais_utilizadas': [
            {'sala': sala, 'total_ocupacoes': total} 
            for sala, total in salas_mais_utilizadas
        ],
        'ocupacoes_por_tipo': [
            {'tipo': tipo or 'Não especificado', 'total': total} 
            for tipo, total in ocupacoes_por_tipo
        ]
    }

    return jsonify(relatorio)


@ocupacao_bp.route('/ocupacoes/tendencia', methods=['GET'])
def obter_tendencia_ocupacoes():
    """Retorna total de ocupações por mês do ano informado."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    ano = request.args.get('ano', type=int, default=date.today().year)

    resultados = db.session.query(
        extract('month', Ocupacao.data).label('mes'),
        func.count(Ocupacao.id).label('total')
    ).filter(
        extract('year', Ocupacao.data) == ano
    ).group_by(extract('month', Ocupacao.data)).order_by(extract('month', Ocupacao.data)).all()

    dados_meses = {str(r.mes).zfill(2): r.total for r in resultados}
    dados_formatados = []
    for i in range(1, 13):
        mes_str = str(i).zfill(2)
        dados_formatados.append({
            'mes': mes_str,
            'total': dados_meses.get(mes_str, 0)
        })

    return jsonify(dados_formatados)


@ocupacao_bp.route('/dashboard/salas/utilizacao', methods=['GET'])
def salas_utilizacao_mes():
    """Retorna contagem de ocupações por sala no mês atual."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    if hoje.month == 12:
        fim_mes = date(hoje.year + 1, 1, 1) - timedelta(days=1)
    else:
        fim_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

    resultados = db.session.query(
        Sala.nome,
        func.count(Ocupacao.id).label('total')
    ).join(Sala, Sala.id == Ocupacao.sala_id).filter(
        Ocupacao.data >= inicio_mes,
        Ocupacao.data <= fim_mes,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    ).group_by(Sala.id, Sala.nome).order_by(desc('total')).all()

    return jsonify([
        {'sala': sala, 'total': total}
        for sala, total in resultados
    ])

