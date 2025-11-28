from datetime import datetime, date
from conecta_senai.models import db

class LogAgendamento(db.Model):
    """Registro de ações realizadas em agendamentos."""

    __tablename__ = 'logs_agendamentos'

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100))
    tipo_acao = db.Column(db.String(20))
    laboratorio = db.Column(db.String(50))
    turno = db.Column(db.String(20))
    data_agendamento = db.Column(db.Date)
    dados_antes = db.Column(db.JSON)
    dados_depois = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, usuario: str, tipo_acao: str, laboratorio: str | None,
                 turno: str | None, data_agendamento: date | None,
                 dados_antes: dict | None, dados_depois: dict | None):
        self.usuario = usuario
        self.tipo_acao = tipo_acao
        self.laboratorio = laboratorio
        self.turno = turno
        self.data_agendamento = data_agendamento
        self.dados_antes = dados_antes
        self.dados_depois = dados_depois

