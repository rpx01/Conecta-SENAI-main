from datetime import datetime, timezone, timedelta

from conecta_senai.models import db


def _get_brasilia_time():
    tz_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(tz_brasilia).replace(tzinfo=None)


class SuporteChamado(db.Model):
    __tablename__ = "suporte_chamados"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    nome_solicitante = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    tipo_equipamento_id = db.Column(
        db.Integer,
        db.ForeignKey("suporte_tipos_equipamento.id"),
        nullable=False,
    )
    patrimonio = db.Column(db.String(120), nullable=True)
    numero_serie = db.Column(db.String(120), nullable=True)
    descricao_problema = db.Column(db.Text, nullable=False)
    nivel_urgencia = db.Column(db.String(20), nullable=False, default="Baixo")
    status = db.Column(db.String(20), nullable=False, default="Aberto")
    observacoes = db.Column(db.Text, nullable=True)
    local_unidade = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=_get_brasilia_time, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=_get_brasilia_time,
        onupdate=_get_brasilia_time,
        nullable=False,
    )

    inicio_atendimento_at = db.Column(db.DateTime, nullable=True)
    encerrado_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref="suporte_chamados")
    tipo_equipamento = db.relationship("SuporteTipoEquipamento", backref="chamados")
    anexos = db.relationship(
        "SuporteAnexo",
        back_populates="chamado",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<SuporteChamado id={self.id} status={self.status!r}>"
