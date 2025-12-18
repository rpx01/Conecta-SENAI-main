from datetime import datetime
from conecta_senai.models import db


class Laboratorio(db.Model):
    __tablename__ = "laboratorios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)

    classe_icone = db.Column(db.String(50), nullable=True, default="bi-box-seam")
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __init__(self, nome, classe_icone=None):
        self.nome = nome
        self.classe_icone = classe_icone or "bi-box-seam"

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "classe_icone": self.classe_icone,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat() if self.data_atualizacao else None
            ),
        }

    def __repr__(self):
        return f"<Laboratorio {self.id}: {self.nome}>"


class Turma(db.Model):
    __tablename__ = "turmas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __init__(self, nome):
        self.nome = nome

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat() if self.data_atualizacao else None
            ),
        }

    def __repr__(self):
        return f"<Turma {self.id}: {self.nome}>"
