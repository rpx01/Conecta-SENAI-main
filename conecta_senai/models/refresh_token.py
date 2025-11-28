"""Modelo de token de atualizacao."""
from datetime import datetime

from conecta_senai.models import db


class RefreshToken(db.Model):
    """Modelo para armazenar tokens de atualização (refresh)."""

    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        return self.expires_at < datetime.utcnow()
