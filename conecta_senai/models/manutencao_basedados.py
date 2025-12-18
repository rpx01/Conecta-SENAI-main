from conecta_senai.models import db


class ManutencaoTipoServico(db.Model):
    __tablename__ = "manutencao_tipos_servico"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<ManutencaoTipoServico {self.nome!r}>"


class ManutencaoArea(db.Model):
    __tablename__ = "manutencao_areas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<ManutencaoArea {self.nome!r}>"
