from datetime import datetime
from conecta_senai.models import db

class LogLancamentoRateio(db.Model):
    """Histórico das alterações nos lançamentos de rateio dos instrutores."""

    __tablename__ = 'log_lancamentos_rateio_instrutor'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    acao = db.Column(db.String(20))
    usuario = db.Column(db.String(100))
    instrutor = db.Column(db.String(100))
    filial = db.Column(db.String(100))
    uo = db.Column(db.String(100))
    cr = db.Column(db.String(100))
    classe_valor = db.Column(db.String(100))
    percentual = db.Column(db.Float)
    observacao = db.Column(db.Text)
