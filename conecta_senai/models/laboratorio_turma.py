"""Modelos de laboratorio e turma."""
from datetime import datetime
from conecta_senai.models import db

class Laboratorio(db.Model):
    """
    Modelo de laboratório disponível para agendamento.
    
    Atributos:
        id (int): Identificador único do laboratório
        nome (str): Nome do laboratório
        data_criacao (datetime): Data de criação do registro
        data_atualizacao (datetime): Data da última atualização do registro
    """
    __tablename__ = 'laboratorios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    # Novo campo para a classe de ícone do laboratório
    classe_icone = db.Column(db.String(50), nullable=True, default='bi-box-seam')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, nome, classe_icone=None):
        """
        Inicializa um novo laboratório.

        Parâmetros:
            nome (str): Nome do laboratório
            classe_icone (str, optional): Classe CSS do ícone do laboratório
        """
        self.nome = nome
        self.classe_icone = classe_icone or 'bi-box-seam'
    
    def to_dict(self):
        """
        Converte o objeto laboratório em um dicionário para serialização.
        
        Retorna:
            dict: Dicionário com os dados do laboratório
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'classe_icone': self.classe_icone,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def __repr__(self):
        """
        Representação em string do objeto laboratório.
        
        Retorna:
            str: Representação em string
        """
        return f"<Laboratorio {self.id}: {self.nome}>"


class Turma(db.Model):
    """
    Modelo de turma disponível para agendamento.
    
    Atributos:
        id (int): Identificador único da turma
        nome (str): Nome da turma
        data_criacao (datetime): Data de criação do registro
        data_atualizacao (datetime): Data da última atualização do registro
    """
    __tablename__ = 'turmas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, nome):
        """
        Inicializa uma nova turma.
        
        Parâmetros:
            nome (str): Nome da turma
        """
        self.nome = nome
    
    def to_dict(self):
        """
        Converte o objeto turma em um dicionário para serialização.
        
        Retorna:
            dict: Dicionário com os dados da turma
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def __repr__(self):
        """
        Representação em string do objeto turma.
        
        Retorna:
            str: Representação em string
        """
        return f"<Turma {self.id}: {self.nome}>"
