"""Modelo de dados para notícias institucionais."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from conecta_senai.models import db


def utcnow():
    """Retorna o horário atual em UTC com informação de timezone."""

    return datetime.now(timezone.utc)


class Noticia(db.Model):
    """Representa uma notícia publicada no portal."""

    __tablename__ = "noticias"
    __table_args__ = (
        db.Index("ix_noticias_ativo", "ativo"),
        db.Index("ix_noticias_destaque", "destaque"),
        db.Index("ix_noticias_data_publicacao", "data_publicacao"),
        db.Index("ix_noticias_ativo_destaque_data", "ativo", "destaque", "data_publicacao"),
    )

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    resumo = db.Column(db.String(500), nullable=True)
    conteudo = db.Column(db.Text, nullable=False)
    autor = db.Column(db.String(120), nullable=True)
    imagem_url = db.Column(db.String(500), nullable=True)
    destaque = db.Column(db.Boolean, nullable=False, default=False, server_default=text("false"))
    ativo = db.Column(db.Boolean, nullable=False, default=True, server_default=text("true"))
    marcar_calendario = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    data_publicacao = db.Column(db.DateTime(timezone=True), nullable=True)
    data_evento = db.Column(db.DateTime(timezone=True), nullable=True)
    imagem = db.relationship(
        "ImagemNoticia",
        back_populates="noticia",
        uselist=False,
        cascade="all, delete-orphan",
    )
    criado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    atualizado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def to_dict(self) -> dict:
        """Serializa a instância para dicionário pronto para JSON."""
        imagem_relacionada = self.imagem.to_dict() if getattr(self, "imagem", None) else None
        imagem_url = imagem_relacionada["url"] if imagem_relacionada else self.imagem_url
        return {
            "id": self.id,
            "titulo": self.titulo,
            "resumo": self.resumo,
            "conteudo": self.conteudo,
            "autor": self.autor,
            "imagem_url": imagem_url,
            "imagem": imagem_relacionada,
            "destaque": bool(self.destaque),
            "ativo": bool(self.ativo),
            "marcar_calendario": bool(self.marcar_calendario),
            "data_publicacao": self.data_publicacao.isoformat() if self.data_publicacao else None,
            "data_evento": self.data_evento.isoformat() if self.data_evento else None,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - representação auxiliar
        return f"<Noticia {self.id} - {self.titulo!r}>"
