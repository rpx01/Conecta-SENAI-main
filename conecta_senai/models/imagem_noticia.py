"""Modelo responsável pelo armazenamento de imagens de notícias."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from flask import send_file, url_for
from sqlalchemy import text
from sqlalchemy.orm import deferred

from conecta_senai.models import db


def utcnow() -> datetime:
    """Retorna a data e hora atual em UTC."""

    return datetime.now(timezone.utc)


class ImagemNoticia(db.Model):
    """Representa a imagem associada a uma notícia."""

    __tablename__ = "imagens_noticias"

    id = db.Column(db.Integer, primary_key=True)
    noticia_id = db.Column(
        db.Integer,
        db.ForeignKey("noticias.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_relativo = db.Column(db.String(255), nullable=False)
    conteudo = deferred(db.Column(db.LargeBinary, nullable=True))
    content_type = db.Column(db.String(255), nullable=False, default="application/octet-stream")
    tem_conteudo = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    criado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    noticia = db.relationship("Noticia", back_populates="imagem", uselist=False)

    @property
    def url_publica(self) -> str:
        """Retorna a URL pública do arquivo armazenado."""

        if self.id is not None and self.tem_conteudo:
            try:
                return url_for("api_noticias.obter_imagem", imagem_id=self.id, _external=False)
            except RuntimeError:
                return f"/api/noticias/imagens/{self.id}"

        caminho = (self.caminho_relativo or "").lstrip("/")
        return f"/static/{caminho}" if caminho else None

    def enviar_arquivo(self):
        """Retorna uma resposta Flask com o conteúdo binário da imagem."""

        if not self.tem_conteudo:
            return None

        if self.conteudo:
            return send_file(
                BytesIO(self.conteudo),
                mimetype=self.content_type or "application/octet-stream",
                download_name=self.nome_arquivo,
            )
        return None

    def to_dict(self) -> dict:
        """Serializa a imagem para um dicionário simples."""

        return {
            "id": self.id,
            "nome_arquivo": self.nome_arquivo,
            "caminho_relativo": self.caminho_relativo,
            "url": self.url_publica,
            "content_type": self.content_type,
        }
