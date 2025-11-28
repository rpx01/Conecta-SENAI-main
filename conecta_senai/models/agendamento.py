"""Modelos de agendamentos e notificacoes."""
from datetime import datetime
from conecta_senai.models import db

class Agendamento(db.Model):
    """
    Modelo de agendamento de laboratório.
    
    Atributos:
        id (int): Identificador único do agendamento
        data (date): Data do agendamento
        laboratorio (str): Nome/identificador do laboratório
        turma (str): Turma para a qual o agendamento foi feito
        turno (str): Turno do agendamento (manhã, tarde ou noite)
        horarios (list): Horários reservados
        usuario_id (int): ID do usuário responsável pelo agendamento
        data_criacao (datetime): Data de criação do registro
        data_atualizacao (datetime): Data da última atualização do registro
    """
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    laboratorio = db.Column(db.String(50), nullable=False)
    turma = db.Column(db.String(50), nullable=False)
    turno = db.Column(db.String(20), nullable=False)
    horarios = db.Column(db.JSON, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, data, laboratorio, turma, turno, horarios, usuario_id):
        """
        Inicializa um novo agendamento.
        
        Parâmetros:
            data (date): Data do agendamento
            laboratorio (str): Nome/identificador do laboratório
            turma (str): Turma para a qual o agendamento foi feito
            turno (str): Turno do agendamento (manhã, tarde ou noite)
        horarios (list): Horários reservados
            usuario_id (int): ID do usuário responsável pelo agendamento
        """
        self.data = data
        self.laboratorio = laboratorio
        self.turma = turma
        self.turno = turno
        self.horarios = horarios
        self.usuario_id = usuario_id
    
    def to_dict(self):
        """
        Converte o objeto agendamento em um dicionário para serialização.
        
        Retorna:
            dict: Dicionário com os dados do agendamento
        """
        return {
            'id': self.id,
            'data': self.data.isoformat() if self.data else None,
            'laboratorio': self.laboratorio,
            'turma': self.turma,
            'turno': self.turno,
            'horarios': self.horarios,
            'usuario_id': self.usuario_id,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def __repr__(self):
        """
        Representação em string do objeto agendamento.
        
        Retorna:
            str: Representação em string
        """
        return f"<Agendamento {self.id}: {self.laboratorio} em {self.data}>"


class Notificacao(db.Model):
    """
    Modelo de notificação de agendamentos.
    
    Atributos:
        id (int): Identificador único da notificação
        usuario_id (int): ID do usuário destinatário da notificação
        agendamento_id (int): ID do agendamento relacionado
        mensagem (str): Texto da notificação
        lida (bool): Indica se a notificação foi lida
        data_criacao (datetime): Data de criação da notificação
    """
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'), nullable=True)
    mensagem = db.Column(db.String(255), nullable=False)
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuario = db.relationship('User', backref=db.backref('notificacoes', lazy=True))
    agendamento = db.relationship('Agendamento', backref=db.backref('notificacoes', lazy=True))
    
    def __init__(self, usuario_id, mensagem, agendamento_id=None):
        """
        Inicializa uma nova notificação.
        
        Parâmetros:
            usuario_id (int): ID do usuário destinatário
            mensagem (str): Texto da notificação
            agendamento_id (int, opcional): ID do agendamento relacionado
        """
        self.usuario_id = usuario_id
        self.mensagem = mensagem
        self.agendamento_id = agendamento_id
        self.lida = False
    
    def marcar_como_lida(self):
        """
        Marca a notificação como lida.
        """
        self.lida = True
    
    def to_dict(self):
        """
        Converte o objeto notificação em um dicionário para serialização.
        
        Retorna:
            dict: Dicionário com os dados da notificação
        """
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'agendamento_id': self.agendamento_id,
            'mensagem': self.mensagem,
            'lida': self.lida,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }
    
    def __repr__(self):
        """
        Representação em string do objeto notificação.
        
        Retorna:
            str: Representação em string
        """
        return f"<Notificacao {self.id} para usuário {self.usuario_id}>"
