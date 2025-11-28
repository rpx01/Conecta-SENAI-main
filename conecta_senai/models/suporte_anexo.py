"""Modelo de anexos do módulo de suporte de TI."""
from conecta_senai.models import db


class SuporteAnexo(db.Model):
    """Armazena metadados de arquivos anexados aos chamados de suporte."""

    __tablename__ = "suporte_anexos"

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(
        db.Integer,
        db.ForeignKey("suporte_chamados.id"),
        nullable=False,
    )
    file_path = db.Column(db.String(255), nullable=False)

    chamado = db.relationship("SuporteChamado", back_populates="anexos")

    def __repr__(self) -> str:  # pragma: no cover - representação simples
        return f"<SuporteAnexo id={self.id} chamado_id={self.chamado_id}>"
