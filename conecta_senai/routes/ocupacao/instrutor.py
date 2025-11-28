"""Rotas para gerenciamento de instrutores."""
from flask import Blueprint, request, jsonify
from conecta_senai.models import db
from conecta_senai.models.instrutor import Instrutor
from conecta_senai.models.ocupacao import Ocupacao
from conecta_senai.routes.user import verificar_autenticacao, verificar_admin
from sqlalchemy.exc import SQLAlchemyError
from conecta_senai.utils.error_handler import handle_internal_error
from datetime import datetime, date
from pydantic import ValidationError
from conecta_senai.schemas import InstrutorCreateSchema, InstrutorUpdateSchema

instrutor_bp = Blueprint('instrutor', __name__)

@instrutor_bp.route('/instrutores', methods=['GET'])
def listar_instrutores():
    """
    Lista todos os instrutores com filtros opcionais.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Parâmetros de filtro
    status = request.args.get('status')
    area_atuacao = request.args.get('area_atuacao')
    
    # Constrói a query base
    query = Instrutor.query
    
    # Aplica filtros
    if status:
        query = query.filter(Instrutor.status == status)
    
    if area_atuacao:
        query = query.filter(Instrutor.area_atuacao.ilike(f'%{area_atuacao}%'))
    
    
    # Ordena por nome
    instrutores = query.order_by(Instrutor.nome).all()
    
    return jsonify([instrutor.to_dict() for instrutor in instrutores])

@instrutor_bp.route('/instrutores/<int:id>', methods=['GET'])
def obter_instrutor(id):
    """
    Obtém detalhes de um instrutor específico.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    instrutor = db.session.get(Instrutor, id)
    if not instrutor:
        return jsonify({'erro': 'Instrutor não encontrado'}), 404
    
    return jsonify(instrutor.to_dict())

@instrutor_bp.route('/instrutores', methods=['POST'])
def criar_instrutor():
    """
    Cria um novo instrutor.
    Apenas administradores podem criar instrutores.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    data = request.json or {}
    try:
        payload = InstrutorCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    if payload.email and Instrutor.query.filter_by(email=payload.email).first():
        return jsonify({'erro': 'Já existe um instrutor com este email'}), 400

    status_validos = ['ativo', 'inativo', 'licenca']
    status = payload.status or 'ativo'
    if status not in status_validos:
        return jsonify({'erro': f'Status deve ser um dos seguintes: {", ".join(status_validos)}'}), 400
    
    try:
        novo_instrutor = Instrutor(
            nome=payload.nome,
            email=payload.email,
            telefone=payload.telefone,
            area_atuacao=payload.area_atuacao,
            disponibilidade=payload.disponibilidade,
            status=status
        )
        novo_instrutor.observacoes = payload.observacoes
        
        db.session.add(novo_instrutor)
        db.session.commit()
        
        return jsonify(novo_instrutor.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@instrutor_bp.route('/instrutores/<int:id>', methods=['PUT'])
def atualizar_instrutor(id):
    """
    Atualiza um instrutor existente.
    Apenas administradores podem atualizar instrutores.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    instrutor = db.session.get(Instrutor, id)
    if not instrutor:
        return jsonify({'erro': 'Instrutor não encontrado'}), 404
    
    data = request.json or {}
    try:
        payload = InstrutorUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400
    
    # Atualiza os campos fornecidos
    if payload.nome is not None:
        if not payload.nome:
            return jsonify({'erro': 'Nome não pode estar vazio'}), 400
        instrutor.nome = payload.nome
    
    if payload.email is not None:
        if payload.email:
            instrutor_existente = Instrutor.query.filter_by(email=payload.email).first()
            if instrutor_existente and instrutor_existente.id != id:
                return jsonify({'erro': 'Já existe um instrutor com este email'}), 400
        instrutor.email = payload.email
    
    if payload.telefone is not None:
        instrutor.telefone = payload.telefone
    
    if payload.area_atuacao is not None:
        instrutor.area_atuacao = payload.area_atuacao

    if payload.disponibilidade is not None:
        instrutor.set_disponibilidade(payload.disponibilidade)
    
    if payload.status is not None:
        status_validos = ['ativo', 'inativo', 'licenca']
        if payload.status not in status_validos:
            return jsonify({'erro': f'Status deve ser um dos seguintes: {", ".join(status_validos)}'}), 400
        instrutor.status = payload.status

    if payload.observacoes is not None:
        instrutor.observacoes = payload.observacoes
    
    
    try:
        db.session.commit()
        return jsonify(instrutor.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@instrutor_bp.route('/instrutores/<int:id>', methods=['DELETE'])
def remover_instrutor(id):
    """
    Remove um instrutor.
    Apenas administradores podem remover instrutores.
    Não permite remoção se houver ocupações futuras.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    instrutor = db.session.get(Instrutor, id)
    if not instrutor:
        return jsonify({'erro': 'Instrutor não encontrado'}), 404
    
    # Verifica se há ocupações futuras
    ocupacoes_futuras = Ocupacao.query.filter(
        Ocupacao.instrutor_id == id,
        Ocupacao.data >= date.today(),
        Ocupacao.status.in_(['confirmado', 'pendente'])
    ).count()
    
    if ocupacoes_futuras > 0:
        return jsonify({'erro': 'Não é possível remover instrutor com ocupações futuras'}), 400
    
    try:
        db.session.delete(instrutor)
        db.session.commit()
        return jsonify({'mensagem': 'Instrutor removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@instrutor_bp.route('/instrutores/<int:id>/disponibilidade', methods=['GET'])
def verificar_disponibilidade_instrutor(id):
    """
    Verifica a disponibilidade de um instrutor em uma data e horário específicos.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    instrutor = db.session.get(Instrutor, id)
    if not instrutor:
        return jsonify({'erro': 'Instrutor não encontrado'}), 404
    
    # Parâmetros obrigatórios
    data_str = request.args.get('data')
    horario_str = request.args.get('horario')
    
    if not all([data_str, horario_str]):
        return jsonify({'erro': 'Data e horário são obrigatórios'}), 400
    
    try:
        # Converte strings para objetos date e time
        data_verificacao = datetime.strptime(data_str, '%Y-%m-%d').date()
        horario = datetime.strptime(horario_str, '%H:%M').time()
        
        # Obtém o dia da semana
        dias = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        dia_semana = dias[data_verificacao.weekday()]
        
        # Verifica disponibilidade geral do instrutor
        # Usa o horário formatado para garantir comparação correta
        horario_formatado = horario.strftime('%H:%M')
        disponivel_horario = instrutor.is_disponivel_horario(dia_semana, horario_formatado)
        
        # Verifica se há ocupações conflitantes
        ocupacoes_dia = Ocupacao.query.filter(
            Ocupacao.instrutor_id == id,
            Ocupacao.data == data_verificacao,
            Ocupacao.status.in_(['confirmado', 'pendente'])
        ).all()
        
        conflitos = []
        for ocupacao in ocupacoes_dia:
            if ocupacao.horario_inicio <= horario <= ocupacao.horario_fim:
                conflitos.append(ocupacao.to_dict(include_relations=False))
        
        disponivel = disponivel_horario and len(conflitos) == 0
        
        return jsonify({
            'disponivel': disponivel,
            'disponivel_horario': disponivel_horario,
            'instrutor': instrutor.to_dict(),
            'conflitos': conflitos
        })
        
    except ValueError:
        return jsonify({'erro': 'Formato de data ou horário inválido'}), 400
    except SQLAlchemyError as e:
        return handle_internal_error(e)

@instrutor_bp.route('/instrutores/<int:id>/ocupacoes', methods=['GET'])
def listar_ocupacoes_instrutor(id):
    """
    Lista as ocupações de um instrutor específico com filtros opcionais.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    instrutor = db.session.get(Instrutor, id)
    if not instrutor:
        return jsonify({'erro': 'Instrutor não encontrado'}), 404
    
    # Parâmetros de filtro
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    status = request.args.get('status')
    
    # Query base
    query = Ocupacao.query.filter(Ocupacao.instrutor_id == id)
    
    # Aplica filtros de data
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            query = query.filter(Ocupacao.data >= data_inicio)
        except ValueError:
            return jsonify({'erro': 'Formato de data_inicio inválido (YYYY-MM-DD)'}), 400
    
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            query = query.filter(Ocupacao.data <= data_fim)
        except ValueError:
            return jsonify({'erro': 'Formato de data_fim inválido (YYYY-MM-DD)'}), 400
    
    # Aplica filtro de status
    if status:
        query = query.filter(Ocupacao.status == status)
    
    # Ordena por data e horário
    ocupacoes = query.order_by(Ocupacao.data, Ocupacao.horario_inicio).all()
    
    return jsonify({
        'instrutor': instrutor.to_dict(),
        'ocupacoes': [ocupacao.to_dict() for ocupacao in ocupacoes]
    })


@instrutor_bp.route('/instrutores/areas-atuacao', methods=['GET'])
def listar_areas_atuacao():
    """
    Lista as áreas de atuação disponíveis.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    areas = [
        {'valor': 'automacao_industrial', 'nome': 'Automação Industrial'},
        {'valor': 'eletromecanica', 'nome': 'Eletromecânica'},
        {'valor': 'eletrotecnica', 'nome': 'Eletrotécnica'},
        {'valor': 'mecanica', 'nome': 'Mecânica'},
        {'valor': 'metalurgia', 'nome': 'Metalurgia'},
        {'valor': 'mineracao', 'nome': 'Mineração'},
        {'valor': 'informatica', 'nome': 'Informática'},
        {'valor': 'logistica', 'nome': 'Logística'},
        {'valor': 'administracao', 'nome': 'Administração'},
        {'valor': 'seguranca_trabalho', 'nome': 'Segurança do Trabalho'},
        {'valor': 'meio_ambiente', 'nome': 'Meio Ambiente'},
        {'valor': 'outros', 'nome': 'Outros'}
    ]
    
    return jsonify(areas)


