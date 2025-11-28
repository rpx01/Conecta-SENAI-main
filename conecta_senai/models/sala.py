"""Modelo de sala."""
from conecta_senai.models import db
from datetime import datetime
from typing import List
from .recurso import Recurso

# Tabela associativa entre salas e recursos
sala_recursos = db.Table(
    'sala_recursos',
    db.Column('sala_id', db.Integer, db.ForeignKey('salas.id'), primary_key=True),
    db.Column('recurso_id', db.Integer, db.ForeignKey('recursos.id'), primary_key=True)
)


class Sala(db.Model):
    """
    Modelo para representar as salas de aula disponíveis para agendamento.
    """
    __tablename__ = 'salas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    capacidade = db.Column(db.Integer, nullable=False)
    recursos = db.relationship(
        'Recurso',
        secondary=sala_recursos,
        lazy='joined',
        backref=db.backref('salas', lazy='joined')
    )
    localizacao = db.Column(db.String(100))
    tipo = db.Column(db.String(50))  # aula_teorica, laboratorio, auditorio, etc.
    status = db.Column(db.String(20), default='ativa')  # ativa, inativa, manutencao
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com ocupações
    ocupacoes = db.relationship('Ocupacao', backref='sala', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, nome, capacidade, recursos: List[str] | None = None, localizacao: str | None = None,
                 tipo: str | None = None, status: str = 'ativa', observacoes: str | None = None):
        self.nome = nome
        self.capacidade = capacidade
        self.set_recursos(recursos or [])
        self.localizacao = localizacao
        self.tipo = tipo
        self.status = status
        self.observacoes = observacoes
    
    def get_recursos(self) -> List[str]:
        """Retorna a lista de nomes dos recursos da sala."""
        return [r.nome for r in self.recursos] if self.recursos else []
    
    def set_recursos(self, recursos_list: List[str]):
        """Atualiza a relação de recursos da sala a partir de uma lista de nomes."""
        self.recursos = []
        if not recursos_list:
            return
        novos_recursos = []
        for nome in recursos_list:
            recurso = Recurso.query.filter_by(nome=nome).first()
            if not recurso:
                recurso = Recurso(nome=nome)
            novos_recursos.append(recurso)
        self.recursos = novos_recursos
    
    def is_disponivel(self, data, horario_inicio, horario_fim, ocupacao_id=None, grupo_ocupacao_id=None):
        """
        Verifica se a sala está disponível em um determinado período.
        
        Parâmetros:
            data: Data da verificação
            horario_inicio: Horário de início
            horario_fim: Horário de fim
            ocupacao_id: ID da ocupação a ser excluída da verificação (para edição)
            grupo_ocupacao_id: Grupo de ocupações a ser ignorado (edição de período)
        
        Retorna:
            bool: True se disponível, False caso contrário
        """
        if self.status != 'ativa':
            return False
        
        # Importa aqui para evitar import circular
        from conecta_senai.models.ocupacao import Ocupacao
        
        # Busca ocupações conflitantes
        query = Ocupacao.query.filter(
            Ocupacao.sala_id == self.id,
            Ocupacao.data == data,
            Ocupacao.status.in_(['confirmado', 'pendente']),
            db.or_(
                db.and_(Ocupacao.horario_inicio <= horario_inicio, Ocupacao.horario_fim > horario_inicio),
                db.and_(Ocupacao.horario_inicio < horario_fim, Ocupacao.horario_fim >= horario_fim),
                db.and_(Ocupacao.horario_inicio >= horario_inicio, Ocupacao.horario_fim <= horario_fim)
            )
        )
        
        # Exclui a ocupação atual se estiver editando
        if ocupacao_id:
            query = query.filter(Ocupacao.id != ocupacao_id)

        if grupo_ocupacao_id:
            query = query.filter(Ocupacao.grupo_ocupacao_id != grupo_ocupacao_id)
        
        conflitos = query.all()
        return len(conflitos) == 0
    
    def to_dict(self):
        """
        Converte o objeto para dicionário.
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'capacidade': self.capacidade,
            'recursos': self.get_recursos(),
            'localizacao': self.localizacao,
            'tipo': self.tipo,
            'status': self.status,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def __repr__(self):
        return f'<Sala {self.nome}>'

