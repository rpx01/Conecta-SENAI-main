from conecta_senai.models import db


class SuporteTipoEquipamento(db.Model):
    __tablename__ = "suporte_tipos_equipamento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<SuporteTipoEquipamento {self.nome!r}>"


class SuporteArea(db.Model):
    __tablename__ = "suporte_areas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"<SuporteArea {self.nome!r}>"
