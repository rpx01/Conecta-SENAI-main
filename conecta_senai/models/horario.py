"""Modelo de horários pré-definidos para treinamentos e eventos."""
from conecta_senai.extensions import db


class Horario(db.Model):
    """Representa um intervalo de horário associado a um turno."""

    __tablename__ = "horarios_treinamento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    turno = db.Column(db.String(30), nullable=True)

    def to_dict(self) -> dict:
        """Converte o modelo em dicionário simples."""

        return {"id": self.id, "nome": self.nome, "turno": self.turno}
