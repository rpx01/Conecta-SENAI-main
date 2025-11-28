from datetime import datetime
from sqlalchemy import func, bindparam

from conecta_senai.models import db
from conecta_senai.models.log_rateio import LogLancamentoRateio


class LogRateioRepository:
    """Repositório para logs de rateio."""

    @staticmethod
    def add(log: LogLancamentoRateio):
        db.session.add(log)
        db.session.commit()

    @staticmethod
    def list_logs(usuario=None, instrutor=None, tipo=None, data_acao=None, page=1, per_page=10):
        query = LogLancamentoRateio.query
        if usuario:
            query = query.filter(
                LogLancamentoRateio.usuario.ilike(func.concat('%', bindparam('usuario'), '%'))
            ).params(usuario=usuario)
        if instrutor:
            query = query.filter(
                LogLancamentoRateio.instrutor.ilike(func.concat('%', bindparam('instrutor'), '%'))
            ).params(instrutor=instrutor)
        if tipo:
            query = query.filter(LogLancamentoRateio.acao == tipo)
        if data_acao:
            dia = datetime.strptime(data_acao, '%Y-%m-%d').date()
            query = query.filter(func.date(LogLancamentoRateio.timestamp) == dia)
        return query.order_by(LogLancamentoRateio.timestamp.desc()).paginate(
            page=page, per_page=min(per_page, 100), error_out=False
        )

    @staticmethod
    def all_ordered():
        return LogLancamentoRateio.query.order_by(LogLancamentoRateio.timestamp.desc()).all()

    @staticmethod
    def rollback():
        db.session.rollback()
