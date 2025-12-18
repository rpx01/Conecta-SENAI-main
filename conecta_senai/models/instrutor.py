from conecta_senai.models import db
from datetime import datetime


class Instrutor(db.Model):
    __tablename__ = "instrutores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    telefone = db.Column(db.String(20))
    area_atuacao = db.Column(db.String(100))
    disponibilidade = db.Column(db.JSON)
    status = db.Column(db.String(20), default="ativo")
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    ocupacoes = db.relationship("Ocupacao", backref="instrutor", lazy=True)

    def __init__(
        self,
        nome,
        email=None,
        telefone=None,
        area_atuacao=None,
        disponibilidade=None,
        status="ativo",
    ):
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.area_atuacao = area_atuacao
        self.disponibilidade = disponibilidade or []
        self.status = status

    def get_disponibilidade(self):
        return self.disponibilidade or []

    def set_disponibilidade(self, disponibilidade_list):
        self.disponibilidade = disponibilidade_list or []

    def is_disponivel_horario(self, dia_semana, horario):
        if self.status != "ativo":
            return False

        disponibilidade = self.get_disponibilidade()
        if not disponibilidade:
            return True

        turno_horarios = {
            "manha": ("06:00", "12:00"),
            "tarde": ("12:00", "18:00"),
            "noite": ("18:00", "23:59"),
        }

        for turno, (inicio, fim) in turno_horarios.items():
            if inicio <= horario <= fim:
                return turno in disponibilidade

        return True

    def get_ocupacoes_periodo(self, data_inicio, data_fim):
        from conecta_senai.models.ocupacao import Ocupacao

        return Ocupacao.query.filter(
            Ocupacao.instrutor_id == self.id,
            Ocupacao.data >= data_inicio,
            Ocupacao.data <= data_fim,
            Ocupacao.status.in_(["confirmado", "pendente"]),
        ).all()

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "area_atuacao": self.area_atuacao,
            "observacoes": self.observacoes,
            "disponibilidade": self.get_disponibilidade(),
            "status": self.status,
            "data_criacao": (
                self.data_criacao.isoformat() if self.data_criacao else None
            ),
            "data_atualizacao": (
                self.data_atualizacao.isoformat() if self.data_atualizacao else None
            ),
        }

    def __repr__(self):
        return f"<Instrutor {self.nome}>"
