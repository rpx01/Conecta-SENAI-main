"""Modelo de usuario do sistema."""
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from conecta_senai.models import db

class User(db.Model):
    """
    Modelo de usuário do sistema.
    
    Atributos:
        id (int): Identificador único do usuário
        nome (str): Nome completo do usuário
        email (str): Email do usuário (único)
        senha_hash (str): Hash da senha do usuário
        tipo (str): Tipo de usuário ('comum', 'admin' ou 'secretaria')
        cpf (str, opcional): CPF do usuário
        data_nascimento (date, opcional): Data de nascimento do usuário
        empresa (str, opcional): Empresa do usuário
        data_criacao (datetime): Data de criação do registro
        data_atualizacao (datetime): Data da última atualização do registro
    """
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

    tipo = db.Column(db.String(20), nullable=False, default='comum')

    # Novos campos opcionais
    cpf = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    empresa = db.Column(db.String(150), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com agendamentos
    agendamentos = db.relationship('Agendamento', backref='usuario', lazy=True)
    
    def __init__(self, nome, email, senha, tipo='comum', username=None):
        """
        Inicializa um novo usuário.
        
        Parâmetros:
            nome (str): Nome completo do usuário
            email (str): Email do usuário
            senha (str): Senha do usuário (será armazenada como hash)
            tipo (str, opcional): Tipo de usuário ('comum', 'admin' ou 'secretaria'). Padrão é 'comum'.
        """
        self.nome = nome
        self.email = email
        self.username = username or email.split('@')[0]
        self.set_senha(senha)
        self.tipo = tipo
    
    def set_senha(self, senha):
        """
        Define a senha do usuário, armazenando-a como hash.
        
        Parâmetros:
            senha (str): Senha em texto plano
        """
        self.senha_hash = generate_password_hash(senha)
    
    def check_senha(self, senha):
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.

        Parâmetros:
            senha (str): Senha em texto plano para verificação

        Retorna:
            bool: True se a senha estiver correta, False caso contrário
        """
        try:
            return check_password_hash(self.senha_hash, senha)
        except ValueError:
            return False
    
    def is_admin(self):
        """
        Verifica se o usuário é um administrador ou secretaria.

        Retorna:
            bool: True se o usuário for administrador ou secretaria, False caso contrário
        """
        return self.tipo in ['admin', 'secretaria']
    
    def to_dict(self):
        """
        Converte o objeto usuário em um dicionário para serialização.
        
        Retorna:
            dict: Dicionário com os dados do usuário (exceto senha)
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'username': self.username,
            'email': self.email,
            'tipo': self.tipo,
            'cpf': self.cpf,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'empresa': self.empresa,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    def __repr__(self):
        """
        Representação em string do objeto usuário.
        
        Retorna:
            str: Representação em string
        """
        return f"<User {self.email}>"
