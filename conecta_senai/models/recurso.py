"""Modelo de recurso."""
from conecta_senai.models import db

class Recurso(db.Model):
    """Modelo para representar recursos disponíveis para salas."""
    __tablename__ = 'recursos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)

    def to_dict(self):
        return {'id': self.id, 'nome': self.nome}

    def __repr__(self):
        return f'<Recurso {self.nome}>'
