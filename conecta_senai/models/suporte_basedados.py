"""Modelos auxiliares do módulo de suporte de TI."""
from conecta_senai.models import db


class SuporteTipoEquipamento(db.Model):
    """Tipos de equipamentos disponíveis para abertura de chamados."""

    __tablename__ = "suporte_tipos_equipamento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<SuporteTipoEquipamento {self.nome!r}>"


class SuporteArea(db.Model):
    """Áreas internas da organização para roteamento de chamados."""

    __tablename__ = "suporte_areas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<SuporteArea {self.nome!r}>"
