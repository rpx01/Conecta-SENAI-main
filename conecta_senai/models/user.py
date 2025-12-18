from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from conecta_senai.models import db


class User(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

    tipo = db.Column(db.String(20), nullable=False, default="comum")

    cpf = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    empresa = db.Column(db.String(150), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agendamentos = db.relationship(
        "Agendamento",
        backref="usuario",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __init__(self, nome, email, senha, tipo="comum", username=None):
        self.nome = nome
        self.email = email
        self.username = username or email.split("@")[0]
        self.set_senha(senha)
        self.tipo = tipo

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        try:
            return check_password_hash(self.senha_hash, senha)
        except ValueError:
            return False

    def is_admin(self):
        return self.tipo in ["admin", "secretaria"]

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "username": self.username,
            "email": self.email,
            "tipo": self.tipo,
            "cpf": self.cpf,
            "data_nascimento": (
                self.data_nascimento.isoformat() if self.data_nascimento else None
            ),
            "empresa": self.empresa,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat() if self.data_atualizacao else None
            ),
        }

    def __repr__(self):
        return f"<User {self.email}>"
