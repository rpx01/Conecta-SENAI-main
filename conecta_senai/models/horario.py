from conecta_senai.extensions import db


class Horario(db.Model):
    __tablename__ = "horarios_treinamento"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    turno = db.Column(db.String(30), nullable=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "nome": self.nome, "turno": self.turno}
