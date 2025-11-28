from datetime import datetime
from conecta_senai.models import db

class AuditLog(db.Model):
    """Registro de a\u00e7\u00f5es realizadas por usu\u00e1rios."""

    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    action = db.Column(db.String(50))
    entity = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')
