from conecta_senai.extensions import db


class SecretariaTreinamentos(db.Model):
    """Model for Secretaria de Treinamentos contacts."""
    __tablename__ = "secretaria_treinamentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "email": self.email}
