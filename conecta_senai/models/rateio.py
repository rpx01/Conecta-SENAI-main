from conecta_senai.models import db
from datetime import datetime

class RateioConfig(db.Model):
    """Modelo para armazenar as configuracoes de rateio."""
    __tablename__ = 'rateio_configs'

    id = db.Column(db.Integer, primary_key=True)
    filial = db.Column(db.String(100), nullable=False)
    uo = db.Column('unidade_organizacional', db.String(100), nullable=False)
    cr = db.Column('centro_resultado', db.String(100), nullable=False)
    classe_valor = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('filial', 'unidade_organizacional', 'centro_resultado', 'classe_valor', name='_rateio_config_uc'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'filial': self.filial,
            'uo': self.uo,
            'cr': self.cr,
            'classe_valor': self.classe_valor,
            'descricao': self.descricao,
            'descricao_completa': f"{self.filial} | {self.uo} | {self.cr} | {self.classe_valor}",
        }

class LancamentoRateio(db.Model):
    """Modelo para os lancamentos de rateio mensais por instrutor."""
    __tablename__ = 'lancamentos_rateio'

    id = db.Column(db.Integer, primary_key=True)
    instrutor_id = db.Column(db.Integer, db.ForeignKey('instrutores.id'), nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    rateio_config_id = db.Column(db.Integer, db.ForeignKey('rateio_configs.id'), nullable=False)
    percentual = db.Column(db.Float, nullable=False)

    instrutor = db.relationship('Instrutor', backref='lancamentos_rateio')
    rateio_config = db.relationship('RateioConfig', backref='lancamentos')

    __table_args__ = (db.Index('ix_lancamento_instrutor_periodo', 'instrutor_id', 'ano', 'mes'),)

    def to_dict(self):
        return {
            'id': self.id,
            'instrutor_id': self.instrutor_id,
            'mes': self.mes,
            'ano': self.ano,
            'rateio_config_id': self.rateio_config_id,
            'percentual': self.percentual,
            'rateio_config': self.rateio_config.to_dict() if self.rateio_config else None,
        }
