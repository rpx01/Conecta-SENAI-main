from conecta_senai.models import db


class ManutencaoAnexo(db.Model):
    __tablename__ = "manutencao_anexos"

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(
        db.Integer,
        db.ForeignKey("manutencao_chamados.id"),
        nullable=False,
    )
    file_path = db.Column(db.String(255), nullable=False)

    chamado = db.relationship("ManutencaoChamado", back_populates="anexos")

    def __repr__(self) -> str:
        return f"<ManutencaoAnexo id={self.id} chamado_id={self.chamado_id}>"
