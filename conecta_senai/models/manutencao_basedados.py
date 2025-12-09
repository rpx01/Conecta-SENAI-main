"""Modelos auxiliares do módulo de manutenção da unidade."""
from conecta_senai.models import db


class ManutencaoTipoServico(db.Model):
    """Tipos de serviços disponíveis para abertura de chamados de manutenção."""

    __tablename__ = "manutencao_tipos_servico"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<ManutencaoTipoServico {self.nome!r}>"


class ManutencaoArea(db.Model):
    """Áreas internas responsáveis pelos chamados de manutenção."""

    __tablename__ = "manutencao_areas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<ManutencaoArea {self.nome!r}>"
