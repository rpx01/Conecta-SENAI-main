from conecta_senai.extensions import db


class EmailSecretaria(db.Model):
    """Model for storing Secretaria emails."""
    __tablename__ = "emails_secretaria"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "email": self.email}
